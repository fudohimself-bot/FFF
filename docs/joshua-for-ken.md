# Joshua Rosfield as Ken's default look (personal, offline use)

Status: **plan only. Nothing here has been run on a real game yet.** The art work has to happen on your Windows PC with your own copies of Final Fantasy XVI and Street Fighter 6. Keep the converted files on your PC: they are Square Enix's and Capcom's assets, so don't share or upload them. Play offline only.

## What the finished mod is

A folder of replacement files for Ken's default costume (his costume 1 mesh, skeleton binding and materials), installed with Fluffy Mod Manager next to the Tekken Mode scripts. Ken keeps all of his SF6 moves; only the look changes.

## Tools (all free, you download them)

| Tool | For | Link |
|---|---|---|
| FF16Tools | Unpacking FF16's `.pac` files | https://github.com/Nenkai/FF16Tools |
| FF16 Model Importer | `.mdl` to `.gltf` | https://github.com/KillzXGaming/FF16-Model-Importer/releases |
| Blender (4.x) | Editing and rigging | https://www.blender.org/download/ |
| RE-Toolbox + RE Mesh Editor | SF6 mesh import and export in Blender | https://github.com/NSACloud/RE-Mesh-Editor |
| Fluffy Mod Manager | Installing the finished mod | already installed |

## Steps

1. **Get Joshua out of FF16.** Unpack the game's character packs with FF16Tools and find Joshua's pack (the `chara` folder). Run `MdlConverter.exe body.mdl <his>.pac` to get a `.gltf`. Textures come out of the same packs as `.tex`, which FF16Tools converts to `.dds`. If you can't tell which pack is Joshua's, send me the folder listing and I'll narrow it down.
2. **Get Ken out of SF6.** With RE Mesh Editor's tools, export Ken's default costume mesh and skeleton, and note the exact file paths inside the game's `natives` folder. Those paths are where the replacement files go.
3. **Dump both skeletons.** In Blender, import one model into an empty scene, open the Scripting tab, open `tools/blender/dump_armature.py` from this project, and press Run Script. It writes `armature_dump_<name>.json` to your Desktop. Do it once for Joshua and once for Ken, and **send me both files**. They are small text files.
4. **I write the bone map.** From the two dumps I build a table that says which of Joshua's bones follow which of Ken's, plus a Blender script that applies it: renames or merges the vertex groups, fits Joshua to Ken's height and pose, and drops what SF6 can't use. I can't produce that without seeing the real bone names.
5. **You run my script in Blender,** check the result against Ken's animations (a quick pose test in Blender catches most stretching), then fix the weights that look wrong.
6. **Materials.** FF16's shader setup doesn't match SF6's. The textures (colour, normal, and so on) have to be assigned to SF6 material files through RE Mesh Editor. This is the most hand-made step.
7. **Export with RE Mesh Editor,** put the files at Ken's paths in a mod folder, install it with Fluffy Mod Manager, and test in offline Training mode.

## Honest expectations

- This is hours of Blender work, not a button. I can write the scripts and read your error messages and screenshots, but I can't run Blender or see the models from here.
- Joshua's hair and clothes were built for FF16's body, not Ken's, so some parts will clip or stretch in some moves. Weight painting fixes most of it.
- If a step fails, send me the exact error or a screenshot and we go from there.
