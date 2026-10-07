"""Fit Cursed Clash Gojo onto Elden Ring's player skeleton (plan step 6).

Run in the background (nothing to click):
  blender.exe --background --python fit_gojo.py -- <gojo.glb> <elden ring Game folder> <parts copy folder> <out.blend> [P1|P2]

  <gojo.glb>           SK_CP_050_00.glb exported from Cursed Clash
  <Game folder>        Elden Ring's Game folder. Soulstruct only reads it (for the Oodle DLL).
  <parts copy folder>  A folder named `parts` holding COPIES of bd_m_1410, hd_m_1410, lg_m_1410 and am_m_1010
                       (.partsbnd.dcx). Its parent is used as Soulstruct's project folder.
  <out.blend>          Where to save the result. Renders go next to it in a `fit_previews` folder.
  P1 | P2              Which variant parts to keep: P1 = blindfold, P2 = no blindfold (default P2).

What it does:
  1. Imports Gojo and deletes the parts Elden Ring can't use (anime outline shells, battle-damage decals) and the
     other variant's parts.
  2. Builds one Elden Ring skeleton (`c0000_fit`) from the bones each armor piece really uses (each piece only
     stores correct positions for its own bones).
  3. Moves Gojo's vertices so his joints land on Elden Ring's: the torso is squashed evenly from hip to neck,
     and arms, legs and fingers are lined up joint by joint.
  4. Renames his vertex groups to Elden Ring bone names with gojo_to_er_bones.json (merging where several Gojo
     bones follow one Elden Ring bone), keeps at most 4 bones per vertex (FLVER's limit) and normalises.
  5. Parents him to `c0000_fit` and renders front, side and a pose test.

Needs Soulstruct for Blender installed and enabled. It never writes to the game folder.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index("--") + 1:]
GLB, GAME_DIR, PARTS_DIR, OUT_BLEND = args[:4]
VARIANT = args[4] if len(args) > 4 else "P2"
HERE = os.path.dirname(os.path.abspath(__file__))
BONE_MAP = json.load(open(os.path.join(HERE, "gojo_to_er_bones.json"), encoding="utf-8"))["map"]
PIECES = ["bd_m_1410", "hd_m_1410", "lg_m_1410", "am_m_1010"]
PREVIEWS = os.path.join(os.path.dirname(os.path.abspath(OUT_BLEND)), "fit_previews")
os.makedirs(PREVIEWS, exist_ok=True)

# Gojo bone -> (Elden Ring bone, next Gojo bone, next Elden Ring bone). The "next" pair sets the direction the
# segment is turned to; None means a tip, which keeps its parent's turn and is only moved.
CHAINS = {"neck": ("Neck", "head", "Head"), "head": ("Head", None, None)}
for s in "LR":
    CHAINS.update({
        f"{s}_collar": (f"{s}_Clavicle", f"{s}_arm", f"{s}_UpperArm"),
        f"{s}_arm": (f"{s}_UpperArm", f"{s}_elbow", f"{s}_Forearm"),
        f"{s}_elbow": (f"{s}_Forearm", f"{s}_hand", f"{s}_Hand"),
        f"{s}_hand": (f"{s}_Hand", f"{s}_middlefinger_A", f"{s}_Finger2"),
        f"{s}_leg": (f"{s}_Thigh", f"{s}_knee", f"{s}_Calf"),
        f"{s}_knee": (f"{s}_Calf", f"{s}_ankle", f"{s}_Foot"),
        f"{s}_ankle": (f"{s}_Foot", f"{s}_toe", f"{s}_Toe0"),
        f"{s}_toe": (f"{s}_Toe0", None, None),
    })
    for finger, n in (("thumb", "0"), ("index", "1"), ("middle", "2"), ("ring", "3"), ("little", "4")):
        CHAINS[f"{s}_{finger}finger_A"] = (f"{s}_Finger{n}", f"{s}_{finger}finger_B", f"{s}_Finger{n}1")
        CHAINS[f"{s}_{finger}finger_B"] = (f"{s}_Finger{n}1", f"{s}_{finger}finger_C", f"{s}_Finger{n}2")
        CHAINS[f"{s}_{finger}finger_C"] = (f"{s}_Finger{n}2", None, None)
TORSO = {"hip", "waist", "spine", "chest"}  # share one even squash from hip (-> Pelvis) to neck (-> Neck)
# Parents Elden Ring's pieces leave out (a piece stores a bone as a root when its parent isn't in that piece).
ER_PARENTS = {"Pelvis": None, "Spine": "Pelvis", "Spine1": "Spine", "Spine2": "Spine1",
              "L_Forearm": "L_UpperArm", "R_Forearm": "R_UpperArm"}


def log(*a):
    print("FIT", *a, flush=True)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)


# --- 1. Elden Ring skeleton -------------------------------------------------------------------------------------
settings = bpy.context.scene.soulstruct_settings
settings.game_enum = "ELDEN_RING"
settings.also_export_to_game = False
settings.eldenring.game_root_str = GAME_DIR
settings.eldenring.project_root_str = os.path.dirname(os.path.abspath(PARTS_DIR))

clear_scene()
er_bones = {}  # name -> (matrix_local, length, parent, weighted vertex count)
for piece in PIECES:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.equipment_flver(directory=os.path.abspath(PARTS_DIR) + os.sep,
                                         files=[{"name": piece + ".partsbnd.dcx"}])
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    mesh = next(o for o in new if o.type == "MESH")
    counts = {}
    names = {g.index: g.name for g in mesh.vertex_groups}
    for v in mesh.data.vertices:
        for ge in v.groups:
            if ge.weight > 0:
                counts[names[ge.group]] = counts.get(names[ge.group], 0) + 1
    for b in arm.data.bones:
        c = counts.get(b.name, 0)
        if c and c > er_bones.get(b.name, (None, 0, None, 0))[3]:
            er_bones[b.name] = (arm.matrix_world @ b.matrix_local, b.length,
                                b.parent.name if b.parent else None, c)
    log("piece", piece, "weighted bones", len(counts))
clear_scene()
for name, parent in ER_PARENTS.items():
    if name in er_bones:
        m, length, _, c = er_bones[name]
        er_bones[name] = (m, length, parent, c)
log("Elden Ring skeleton:", len(er_bones), "bones")

er_data = bpy.data.armatures.new("c0000_fit")
er_arm = bpy.data.objects.new("c0000_fit", er_data)
bpy.context.scene.collection.objects.link(er_arm)
bpy.context.view_layer.objects.active = er_arm
bpy.ops.object.mode_set(mode="EDIT")
for name, (m, length, _, _) in er_bones.items():
    eb = er_data.edit_bones.new(name)
    eb.head, eb.tail = Vector((0, 0, 0)), Vector((0, max(length, 0.02), 0))
    eb.matrix = m
for name, (_, _, parent, _) in er_bones.items():
    if parent in er_bones:
        er_data.edit_bones[name].parent = er_data.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")
ER_HEAD = {n: (m @ Vector((0, 0, 0))) for n, (m, _, _, _) in er_bones.items()}

# --- 2. Gojo -----------------------------------------------------------------------------------------------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
new = [o for o in bpy.data.objects if o not in before]
for o in new:
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o)
gojo_arm = next(o for o in bpy.data.objects if o.type == "ARMATURE" and o is not er_arm)
gojo = next(o for o in bpy.data.objects if o.type == "MESH")
gojo.name = "Gojo"
other = "P1" if VARIANT == "P2" else "P2"
mat_names = [s.material.name for s in gojo.material_slots]
drop = [i for i, n in enumerate(mat_names) if "Outline" in n or "Decal" in n or n.endswith("_" + other)]
bm = bmesh.new()
bm.from_mesh(gojo.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in drop], context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(gojo.data)
bm.free()
for i in sorted(drop, reverse=True):
    gojo.active_material_index = i
    bpy.context.view_layer.objects.active = gojo
    bpy.ops.object.material_slot_remove()
log("Gojo kept", len(gojo.data.polygons), "triangles,", len(gojo.material_slots), "materials:",
    [s.material.name for s in gojo.material_slots])

G_HEAD = {b.name: gojo_arm.matrix_world @ b.head_local for b in gojo_arm.data.bones}
G_PARENT = {b.name: (b.parent.name if b.parent else None) for b in gojo_arm.data.bones}


def scale_along(direction, ratio):
    """3x3 scale by `ratio` along `direction` only."""
    d = direction.normalized()
    m = Matrix.Identity(3)
    for i in range(3):
        for j in range(3):
            m[i][j] += (ratio - 1.0) * d[i] * d[j]
    return m


def affine(lin3, src, dst):
    """4x4 that applies `lin3` about `src` and then moves `src` onto `dst`."""
    return Matrix.Translation(dst) @ lin3.to_4x4() @ Matrix.Translation(-src)


# Torso: one even squash along Z from Gojo's hip..neck onto Elden Ring's Pelvis..Neck.
k = (ER_HEAD["Neck"].z - ER_HEAD["Pelvis"].z) / (G_HEAD["neck"].z - G_HEAD["hip"].z)
torso = affine(Matrix.Diagonal((1.0, 1.0, k)), G_HEAD["hip"], ER_HEAD["Pelvis"])
log(f"torso squash {k:.3f}")

XFORM = {b: torso for b in TORSO}
ROT = {b: Matrix.Identity(3) for b in TORSO}


def solve(bone):
    """Transform for a Gojo bone; parents first so tips can reuse their parent's turn."""
    if bone in XFORM:
        return XFORM[bone]
    parent = G_PARENT[bone]
    if bone in CHAINS:
        er, g_next, er_next = CHAINS[bone]
        if parent:
            solve(parent)
        if g_next:
            gd = G_HEAD[g_next] - G_HEAD[bone]
            ed = ER_HEAD[er_next] - ER_HEAD[er]
            rot = gd.rotation_difference(ed).to_matrix()
            lin = rot @ scale_along(gd, ed.length / gd.length)
        else:
            p = parent
            while p not in ROT:
                p = G_PARENT[p]
            rot = ROT[p]
            lin = rot
        ROT[bone] = rot
        XFORM[bone] = affine(lin, G_HEAD[bone], ER_HEAD[er])
    else:
        # helpers, hair, face, hood, hem: follow the nearest solved ancestor
        XFORM[bone] = solve(parent) if parent else torso
        ROT[bone] = ROT.get(parent, Matrix.Identity(3)) if parent else Matrix.Identity(3)
    return XFORM[bone]


for b in G_HEAD:
    solve(b)

# --- 3. Move Gojo's vertices (linear blend of the per-bone transforms) -------------------------------------------
gm, gm_inv = gojo.matrix_world, gojo.matrix_world.inverted()
groups = {g.index: g.name for g in gojo.vertex_groups}
moved = 0
for v in gojo.data.vertices:
    p = gm @ v.co
    acc, wsum = Vector((0, 0, 0)), 0.0
    for ge in v.groups:
        name = groups.get(ge.group)
        if ge.weight > 0 and name in XFORM:
            acc += ge.weight * (XFORM[name] @ p)
            wsum += ge.weight
    v.co = gm_inv @ ((acc / wsum) if wsum else (torso @ p))
    moved += 1
gojo.data.update()
log("moved", moved, "vertices")

# --- 4. Rename and merge vertex groups to Elden Ring names ------------------------------------------------------
weights = [dict() for _ in gojo.data.vertices]
for v in gojo.data.vertices:
    for ge in v.groups:
        target = BONE_MAP.get(groups.get(ge.group))
        if target and ge.weight > 0:
            weights[v.index][target] = weights[v.index].get(target, 0.0) + ge.weight
gojo.vertex_groups.clear()
new_groups = {}
for i, w in enumerate(weights):
    top = sorted(w.items(), key=lambda x: -x[1])[:4]  # FLVER keeps at most 4 bones per vertex
    total = sum(x[1] for x in top) or 1.0
    for name, wt in top:
        if name not in new_groups:
            new_groups[name] = gojo.vertex_groups.new(name=name)
        new_groups[name].add([i], wt / total, "REPLACE")
missing = sorted(set(new_groups) - set(er_bones))
log("vertex groups:", len(new_groups), "| not in Elden Ring skeleton:", missing or "none")

# --- 5. Parent to the Elden Ring skeleton, save, render ---------------------------------------------------------
gojo.parent = None
gojo.matrix_world = gm
for mod in list(gojo.modifiers):
    gojo.modifiers.remove(mod)
bpy.data.objects.remove(gojo_arm)
gojo.parent = er_arm
gojo.matrix_parent_inverse = er_arm.matrix_world.inverted()
mod = gojo.modifiers.new("Armature", "ARMATURE")
mod.object = er_arm
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
log("saved", OUT_BLEND)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.render.resolution_x, scene.render.resolution_y = 900, 1200
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"
scene.collection.objects.link(cam)
scene.camera = cam


def render(name, loc, rot, scale):
    cam.location, cam.rotation_euler, cam.data.ortho_scale = loc, rot, scale
    scene.render.filepath = os.path.join(PREVIEWS, name + ".png")
    bpy.ops.render.render(write_still=True)
    log("rendered", scene.render.filepath)


FRONT = (Vector((0, -5, 0.9)), (math.radians(90), 0, 0), 2.0)
SIDE = (Vector((5, 0, 0.9)), (math.radians(90), 0, math.radians(90)), 2.0)
render("fit_front", *FRONT)
render("fit_side", *SIDE)


def turn(bone, axis, degrees):
    """Pose test: turn a bone about a world axis through its head."""
    pb = er_arm.pose.bones[bone]
    head = er_arm.matrix_world @ pb.head
    r = Matrix.Translation(head) @ Quaternion(axis, math.radians(degrees)).to_matrix().to_4x4() @ Matrix.Translation(-head)
    pb.matrix = er_arm.matrix_world.inverted() @ r @ er_arm.matrix_world @ pb.matrix
    bpy.context.view_layer.update()


turn("L_UpperArm", (0, 1, 0), -40)   # left arm up
turn("R_Forearm", (0, 1, 0), -70)    # right elbow bent
turn("L_Thigh", (1, 0, 0), -50)      # left leg forward
turn("L_Calf", (1, 0, 0), 70)        # left knee bent
turn("Head", (0, 0, 1), 30)          # head turned
render("fit_pose_front", *FRONT)
render("fit_pose_side", *SIDE)
log("done")
