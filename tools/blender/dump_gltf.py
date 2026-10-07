"""Import a .gltf/.glb into an empty scene and write a skeleton dump, without opening Blender's window.

  blender.exe --background --factory-startup --python dump_gltf.py -- <out folder> <model.glb>

Writes armature_dump_<model>.json into <out folder>, in the same format as dump_armature.py.
"""
import importlib.util
import json
import os
import sys

import bpy

out_dir, model = sys.argv[sys.argv.index("--") + 1:][:2]
os.makedirs(out_dir, exist_ok=True)

spec = importlib.util.spec_from_file_location("dump_armature", os.path.join(os.path.dirname(__file__), "dump_armature.py"))
dump_armature = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dump_armature)

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)
bpy.ops.import_scene.gltf(filepath=model)
data = dump_armature.dump_scene()
stem = os.path.basename(model).split(".")[0]
data["blend_file"] = os.path.basename(model)
path = os.path.join(out_dir, f"armature_dump_{stem}.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print(f"DUMPED {stem}: {sum(a['bone_count'] for a in data['armatures'])} bones, {len(data['meshes'])} mesh(es) -> {path}")
