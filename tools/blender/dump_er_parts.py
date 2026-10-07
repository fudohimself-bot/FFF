"""Import Elden Ring armor pieces with Soulstruct for Blender and write a skeleton dump for each.

Run from a command prompt (Blender opens in the background, nothing to click):
  blender.exe --background --python dump_er_parts.py -- <game folder> <out folder> <piece.partsbnd.dcx> [more pieces...]

<game folder> is Elden Ring's `Game` folder. Soulstruct only reads from it (for the Oodle DLL that
decompresses the pieces); exporting to the game stays off. Each piece must sit in a folder named `parts`,
whose parent is used as Soulstruct's project folder; use copies, not the game's own files.

Writes armature_dump_<piece>.json into <out folder>, in the same format as dump_armature.py.
Needs Soulstruct for Blender installed and enabled. It only reads the piece files.
"""
import importlib.util
import json
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
game_dir, out_dir, pieces = args[0], args[1], args[2:]
os.makedirs(out_dir, exist_ok=True)

settings = bpy.context.scene.soulstruct_settings
settings.game_enum = "ELDEN_RING"
settings.also_export_to_game = False
settings.eldenring.game_root_str = game_dir
settings.eldenring.project_root_str = os.path.dirname(os.path.dirname(os.path.abspath(pieces[0])))

spec = importlib.util.spec_from_file_location("dump_armature", os.path.join(os.path.dirname(__file__), "dump_armature.py"))
dump_armature = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dump_armature)

for piece in pieces:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    folder, name = os.path.split(os.path.abspath(piece))
    bpy.ops.import_scene.equipment_flver(directory=folder + os.sep, files=[{"name": name}])
    data = dump_armature.dump_scene()
    stem = name.split(".")[0]
    data["blend_file"] = name
    path = os.path.join(out_dir, f"armature_dump_{stem}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    n_bones = sum(a["bone_count"] for a in data["armatures"])
    n_tris = sum(m["polygons"] for m in data["meshes"])
    print(f"DUMPED {stem}: {len(data['armatures'])} armature(s), {n_bones} bones, {len(data['meshes'])} mesh(es), {n_tris} polygons -> {path}")
