"""Dump the skeleton and meshes of whatever is in the open Blender scene to a small JSON file.

How to use (Blender 3.x or 4.x):
  1. Import ONE model into an empty scene (Joshua from the FF16 .gltf, or Ken through RE Mesh Editor).
  2. Open the Scripting tab, open this file, and press Run Script.
  3. The result is written to your Desktop as armature_dump_<blend file name>.json. Send that file.

It only reads the scene. It changes nothing and needs no add-ons.
"""
import json
import os

import bpy


def r4(values):
    return [round(float(v), 4) for v in values]


def dump_scene():
    out = {
        "blend_file": bpy.path.basename(bpy.data.filepath) or "(unsaved)",
        "blender": ".".join(str(n) for n in bpy.app.version),
        "unit_scale": bpy.context.scene.unit_settings.scale_length,
        "armatures": [],
        "meshes": [],
    }
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            bones = []
            for b in obj.data.bones:
                bones.append({
                    "name": b.name,
                    "parent": b.parent.name if b.parent else None,
                    "head": r4(b.head_local),
                    "tail": r4(b.tail_local),
                    "length": round(float(b.length), 4),
                })
            out["armatures"].append({
                "object": obj.name,
                "location": r4(obj.location),
                "scale": r4(obj.scale),
                "dimensions": r4(obj.dimensions),
                "bone_count": len(bones),
                "bones": bones,
            })
        elif obj.type == "MESH":
            out["meshes"].append({
                "object": obj.name,
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "dimensions": r4(obj.dimensions),
                "location": r4(obj.location),
                "scale": r4(obj.scale),
                "vertex_groups": [g.name for g in obj.vertex_groups],
                "materials": [m.name if m else None for m in obj.data.materials],
                "parent": obj.parent.name if obj.parent else None,
                "modifiers": [m.type for m in obj.modifiers],
            })
    return out


def main():
    data = dump_scene()
    stem = os.path.splitext(data["blend_file"])[0] if data["blend_file"] != "(unsaved)" else "scene"
    path = os.path.join(os.path.expanduser("~"), "Desktop", f"armature_dump_{stem}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        path = os.path.join(os.path.expanduser("~"), f"armature_dump_{stem}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    n_bones = sum(a["bone_count"] for a in data["armatures"])
    print(f"Wrote {path}: {len(data['armatures'])} armature(s), {n_bones} bones, {len(data['meshes'])} mesh(es)")


if __name__ == "__main__":
    main()
