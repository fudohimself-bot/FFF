"""Checks tools/blender/dump_armature.py against a stand-in for Blender's `bpy` (real Blender is not available here).

  python3 -I tests/test_blender_dump.py
"""
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class V(list):
    pass


def make_bpy(objects, filepath="C:/models/joshua.blend"):
    bpy = types.ModuleType("bpy")
    bpy.app = types.SimpleNamespace(version=(4, 1, 0))
    bpy.data = types.SimpleNamespace(filepath=filepath)
    bpy.path = types.SimpleNamespace(basename=lambda p: p.replace("\\", "/").split("/")[-1])
    bpy.context = types.SimpleNamespace(
        scene=types.SimpleNamespace(objects=objects, unit_settings=types.SimpleNamespace(scale_length=1.0)))
    return bpy


def bone(name, parent=None, head=(0, 0, 0), tail=(0, 0, 1)):
    return types.SimpleNamespace(name=name, parent=parent, head_local=head, tail_local=tail, length=1.0)


def load_script(bpy):
    sys.modules["bpy"] = bpy
    spec = importlib.util.spec_from_file_location("dump_armature", ROOT / "tools" / "blender" / "dump_armature.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class DumpArmature(unittest.TestCase):
    def scene(self):
        root = bone("root")
        hips = bone("hips", parent=root, head=(0, 0, 1), tail=(0, 0, 2))
        arm = types.SimpleNamespace(type="ARMATURE", name="Armature", location=(0, 0, 0), scale=(1, 1, 1),
                                    dimensions=(1, 1, 2), data=types.SimpleNamespace(bones=[root, hips]))
        mesh = types.SimpleNamespace(
            type="MESH", name="body", dimensions=(0.5, 0.3, 1.8), location=(0, 0, 0), scale=(1, 1, 1), parent=arm,
            data=types.SimpleNamespace(vertices=[1, 2, 3], polygons=[1], materials=[types.SimpleNamespace(name="skin"), None]),
            vertex_groups=[types.SimpleNamespace(name="hips")], modifiers=[types.SimpleNamespace(type="ARMATURE")])
        light = types.SimpleNamespace(type="LIGHT", name="Light")
        return [arm, mesh, light]

    def test_dump_has_bones_parents_and_meshes(self):
        mod = load_script(make_bpy(self.scene()))
        data = mod.dump_scene()
        self.assertEqual(data["blend_file"], "joshua.blend")
        self.assertEqual(data["armatures"][0]["bone_count"], 2)
        bones = {b["name"]: b for b in data["armatures"][0]["bones"]}
        self.assertEqual(bones["hips"]["parent"], "root")
        self.assertIsNone(bones["root"]["parent"])
        m = data["meshes"][0]
        self.assertEqual((m["vertices"], m["polygons"]), (3, 1))
        self.assertEqual(m["vertex_groups"], ["hips"])
        self.assertEqual(m["materials"], ["skin", None])
        self.assertEqual(m["parent"], "Armature")
        self.assertEqual(len(data["meshes"]) + len(data["armatures"]), 2)  # lights ignored

    def test_main_writes_a_json_file_named_after_the_blend_file(self):
        mod = load_script(make_bpy(self.scene()))
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, "Desktop"))
            old = os.environ.get("HOME"), os.environ.get("USERPROFILE")
            os.environ["HOME"] = home
            os.environ["USERPROFILE"] = home
            try:
                mod.main()
            finally:
                for k, v in zip(("HOME", "USERPROFILE"), old):
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            out = Path(home) / "Desktop" / "armature_dump_joshua.json"
            self.assertTrue(out.exists())
            self.assertEqual(json.loads(out.read_text())["armatures"][0]["bone_count"], 2)

    def test_unsaved_scene_gets_a_safe_name(self):
        mod = load_script(make_bpy([], filepath=""))
        data = mod.dump_scene()
        self.assertEqual(data["blend_file"], "(unsaved)")
        self.assertEqual(data["armatures"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
