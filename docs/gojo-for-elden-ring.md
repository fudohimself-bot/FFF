# Gojo as the Elden Ring player (personal, offline use)

Status: **plan only. Nothing here has been run on a real game yet.** The art work has to happen on your Windows PC with your own copies of Jujutsu Kaisen Cursed Clash and Elden Ring. Keep the extracted and converted files on your PC: they are Bandai Namco's and FromSoftware's assets, so don't share or upload them, and never put them in this repo. Play offline only.

## What the finished mod is

Gojo Satoru's model from Cursed Clash, worn by your Elden Ring character as a replacement for one armor set. Put that set on and your Tarnished looks like Gojo; everything else in Elden Ring (moves, bosses, the world) stays the same. It is loaded with Mod Engine 2, which starts Elden Ring with Easy Anti-Cheat off, so it only works offline.

Later, optional: a Gojo-style moveset made by editing Elden Ring's player behaviour script `c0000.hks` from [soulsmods/EldenRingHKS](https://github.com/soulsmods/EldenRingHKS). That reuses Elden Ring's own animations; bringing over Cursed Clash animations or effects (Hollow Purple, Domain Expansion) is a much bigger job and is not part of this plan.

## Where things are on your PC

Both games are on the D: drive. These are guesses from your FF16 path; check them in Steam (right-click the game, Manage, Browse local files):

| Game | Folder |
|---|---|
| Cursed Clash | `D:\steam\steamapps\common\Jujutsu Kaisen CC` (its packs are in `Jujutsu Kaisen CC\Content\Paks`) |
| Elden Ring | `D:\steam\steamapps\common\ELDEN RING\Game` |

## Tools (all free, you download them)

| Tool | For | Link |
|---|---|---|
| FModel | Opening Cursed Clash's packs and exporting Gojo's model and textures | https://fmodel.app |
| Blender (4.x) | Fitting Gojo onto the Elden Ring body | https://www.blender.org/download/ |
| Soulstruct for Blender | Importing and exporting Elden Ring models (FLVER) in Blender | https://github.com/Grimrukh/soulstruct-blender |
| UXM Selective Unpacker | Unpacking Elden Ring's game files so the armor files can be read | https://github.com/Nordgaren/UXM-Selective-Unpack |
| Smithbox | Editing Elden Ring's armor table (which body parts the armor hides) | https://github.com/vawser/Smithbox |
| Mod Engine 2 | Loading the mod and starting the game offline | https://github.com/soulsmods/ModEngine2/releases |

You do **not** need the Cursed Clash UE5 Mod Kit itself (Unreal Engine 5.1, Visual Studio and 60 GB of space). FModel reads the same packs directly. The packs are encrypted; the key FModel needs is in the mod kit's `Content/Python/import_game_assets.py` (the `_AES_KEY` line).

## Steps

1. **Find Gojo in Cursed Clash.** In FModel, add the Cursed Clash folder as a game (Unreal Engine version 5.1) and paste the key into Directory > AES Manager. Characters are under `Content/Characters/CP_###`; the mod kit doesn't say which number is Gojo, so open the `SK_...` skeletal mesh in each `CP_` folder until you see him. **Tell me the folder number.**
2. **Export Gojo.** In FModel's settings, set the model export format to glTF and textures to PNG. Right-click Gojo's skeletal mesh, choose Save Model, and save his textures too.
3. **Pick the armor set to replace.** Choose a set you already own in your save (or one you can get early). Tell me its name and I'll give you its file numbers: Elden Ring stores each piece as `parts\hd_m_####.partsbnd.dcx` (head), `bd_m_` (body), `am_m_` (arms) and `lg_m_` (legs).
4. **Unpack Elden Ring** with UXM Selective Unpacker, choosing only the `parts` folder.
5. **Dump both skeletons.** In Blender, import Gojo's `.gltf` into an empty scene, open the Scripting tab, open `tools/blender/dump_armature.py` from this project and press Run Script. It writes `armature_dump_<name>.json` to your Desktop, named after the Blender file, so save each scene first with its own name (for example `gojo.blend` and `eldenring.blend`). Do the same with the body armor piece imported through Soulstruct for Blender. **Send me both files.** They are small text files.
6. **I write the bone map.** From the two dumps I build a table that says which of Gojo's bones follow which Elden Ring bones, and a Blender script that applies it: renames or merges the vertex groups, fits Gojo to the Elden Ring body's height and pose, and drops bones Elden Ring can't use.
7. **You run my script in Blender,** pose-test the arms and legs, and fix the weights that look wrong.
8. **Split and export.** Gojo goes into the body piece; the head, arms and legs pieces show his matching parts (or nothing). Export each with Soulstruct for Blender, keeping the original file names.
9. **Hide the Tarnished underneath.** In Smithbox, open the armor table (EquipParamProtector) and set the set's hide flags so your character's own face, hair and body don't poke through Gojo.
10. **Install and test.** Put the files in Mod Engine 2's `mod\parts` folder (and the edited `regulation.bin` from Smithbox in `mod`), start the game with `launchmod_eldenring.bat`, and put the armor on at a Site of Grace.

## Keeping it light on your PC

A model swap costs almost nothing beyond Elden Ring itself, as long as the model stays near the size of Elden Ring's own armor:

- Keep the whole Gojo model at or under about 60,000 triangles. The dump in step 5 lists each mesh's polygon count; if it's over, I'll add a Decimate step to the step 6 script.
- Keep his textures at 2048x2048 or smaller.
- Use one material per piece where possible.

## Honest expectations

- This is hours of Blender work, not a button. I can write the scripts and read your error messages and screenshots, but I can't run the games or see the models from here.
- Cursed Clash uses a cel-shaded (anime outline) look; Elden Ring's shaders are realistic. Gojo will look like a realistic-lit version of himself, without the anime outlines.
- Gojo's proportions don't match the Tarnished's, so some parts will clip or stretch in some moves. Weight painting fixes most of it.
- If a step fails, send me the exact error or a screenshot and we go from there.
