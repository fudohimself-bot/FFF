# Gojo as the Elden Ring player (personal, offline use)

Status: **plan only. Nothing here has been run on a real game yet.** The art work has to happen on your Windows PC with your own copies of Jujutsu Kaisen Cursed Clash and Elden Ring. Keep the extracted and converted files on your PC: they are Bandai Namco's and FromSoftware's assets, so don't share or upload them, and never put them in this repo. Play offline only.

## What the finished mod is

Gojo Satoru's model from Cursed Clash, worn by your Elden Ring character as a replacement for one armor set. Put that set on and your Tarnished looks like Gojo; everything else in Elden Ring (moves, bosses, the world) stays the same. It is loaded with Mod Engine 2, which starts Elden Ring with Easy Anti-Cheat off, so it only works offline.

Part 2 is Gojo's moves (see "Part 2: Gojo's moves" below): his Cursed Clash animations brought onto the Elden Ring body, hooked up as a fist weapon and a set of sorceries. Part 1 (the model) comes first, because the moves need the same bone map.

## Where things are on your PC

Both games are on the D: drive. These are guesses from your FF16 path; check them in Steam (right-click the game, Manage, Browse local files):

| Game | Folder |
|---|---|
| Cursed Clash | `D:\steam\steamapps\common\Jujutsu Kaisen CC` (its packs are in `Jujutsu Kaisen CC\Content\Paks`) |
| Elden Ring | `D:\steam\steamapps\common\ELDEN RING\Game` |

## Tools (all free, you download them)

**Shortcut:** double-click `tools\windows\get_tools.bat` from this project. It downloads all of the tools below (and Part 2's) into `D:\GojoMod\tools`, plus the Cursed Clash mapping files, and checks that both games are where it expects. Not yet run on a real PC.

| Tool | For | Link |
|---|---|---|
| FModel | Opening Cursed Clash's packs and exporting Gojo's model and textures | https://fmodel.app |
| Blender (5.1 or newer; Soulstruct for Blender needs it) | Fitting Gojo onto the Elden Ring body | https://www.blender.org/download/ |
| Soulstruct for Blender | Importing and exporting Elden Ring models (FLVER) in Blender | https://github.com/Grimrukh/soulstruct-blender |
| UXM Selective Unpacker | Unpacking Elden Ring's game files so the armor files can be read | https://github.com/Nordgaren/UXM-Selective-Unpack |
| Smithbox | Editing Elden Ring's armor table (which body parts the armor hides) | https://github.com/vawser/Smithbox |
| Mod Engine 2 | Loading the mod and starting the game offline | https://github.com/soulsmods/ModEngine2/releases |

You do **not** need the Cursed Clash UE5 Mod Kit itself (Unreal Engine 5.1, Visual Studio and 60 GB of space). FModel reads the same packs directly. The packs are encrypted; the key FModel needs is in the mod kit's `Content/Python/import_game_assets.py` (the `_AES_KEY` line). FModel also needs the game's mapping file (`.usmap`) to read models: get it from [JJK-CC-Resources](https://github.com/MadMax1960/JJK-CC-Resources) and set it in FModel's settings as the local mapping file.

## Steps

1. **Find Gojo in Cursed Clash.** In FModel, add the Cursed Clash folder as a game (Unreal Engine version 5.1) and paste the key into Directory > AES Manager. Characters are under `Content/Characters/CP_###`. **Gojo is `CP_050`** (adult Gojo; `CP_051` is teen Gojo), according to the ID table in [JJK-CC-Resources](https://github.com/MadMax1960/JJK-CC-Resources). Open the `SK_...` skeletal mesh in `CP_050` to check it's him.
2. **Export Gojo.** In FModel's settings, set the model export format to glTF and textures to PNG. Right-click Gojo's skeletal mesh, choose Save Model, and save his textures too.
3. **Pick the armor set to replace.** Choose a set you already own in your save (or one you can get early). Tell me its name and I'll give you its file numbers: Elden Ring stores each piece as `parts\hd_m_####.partsbnd.dcx` (head), `bd_m_` (body), `am_m_` (arms) and `lg_m_` (legs).
4. **Unpack Elden Ring** with UXM Selective Unpacker, choosing only the `parts` folder.
5. **Dump both skeletons.** In Blender, import Gojo's `.gltf` into an empty scene, open the Scripting tab, open `tools/blender/dump_armature.py` from this project and press Run Script. It writes `armature_dump_<name>.json` to your Desktop, named after the Blender file, so save each scene first with its own name (for example `gojo.blend` and `eldenring.blend`). Do the same with the body armor piece imported through Soulstruct for Blender. **Send me both files.** They are small text files.
6. **I write the bone map.** From the two dumps I build a table that says which of Gojo's bones follow which Elden Ring bones, and a Blender script that applies it: renames or merges the vertex groups, fits Gojo to the Elden Ring body's height and pose, and drops bones Elden Ring can't use.
7. **You run my script in Blender,** pose-test the arms and legs, and fix the weights that look wrong.
8. **Split and export.** Gojo goes into the body piece; the head, arms and legs pieces show his matching parts (or nothing). Export each with Soulstruct for Blender, keeping the original file names.
9. **Hide the Tarnished underneath.** In Smithbox, open the armor table (EquipParamProtector) and set the set's hide flags so your character's own face, hair and body don't poke through Gojo.
10. **Install and test.** Put the files in Mod Engine 2's `mod\parts` folder (and the edited `regulation.bin` from Smithbox in `mod`), start the game with `launchmod_eldenring.bat`, and put the armor on at a Site of Grace.

## Part 2: Gojo's moves

Elden Ring can't run Cursed Clash's moves directly: Cursed Clash moves are Unreal animation montages with Unreal effects, and Elden Ring uses Havok animations (`.hkx`), its own event timelines (TAE) and its own effects (FXR). Each move has to be rebuilt: the animation is brought across, and the hitboxes, damage and effects are set up again in Elden Ring's tools.

| Gojo move | How it's built in Elden Ring | Animation | Effect |
|---|---|---|---|
| Punch and kick combos | A fist weapon whose light and heavy attacks use his Cursed Clash combo animations | Cursed Clash, retargeted | Elden Ring's hit sparks |
| Lapse Blue (pull) | A sorcery whose projectile pulls enemies in, based on Elden Ring's gravity spells | Cursed Clash cast pose | Elden Ring gravity effect, recoloured blue |
| Reversal Red (push) | A sorcery with a short-range blast that knocks enemies back | Cursed Clash cast pose | Elden Ring blast effect, recoloured red |
| Hollow Purple | A sorcery that fires a large slow beam, based on Comet Azur | Cursed Clash cast pose | Comet Azur's beam, recoloured purple |
| Infinity | A buff (SpEffect) that cuts damage taken a lot for a few seconds | Elden Ring buff pose | Elden Ring barrier effect |
| Domain Expansion: Unlimited Void | A sorcery that freezes nearby enemies for a few seconds | Cursed Clash hand sign | An Elden Ring area effect; no black-void cutscene |
| Teleport dash | Replaces the dodge roll with a quick step | Elden Ring's Quickstep | Elden Ring's |

What won't come across: the anime effects themselves (Cursed Clash's particles, outlines and cutscene camera), the Domain Expansion cutscene and his voice lines. The move effects above are Elden Ring's own effects recoloured, so they look Elden Ring-style, not anime.

Tools for this part, on top of Part 1's:

| Tool | For | Link |
|---|---|---|
| Soulstruct for Blender (animation import/export) | Turning retargeted animations into Elden Ring `.hkx` (Elden Ring animation support is marked partial) | https://github.com/Grimrukh/soulstruct-blender |
| DS Anim Studio | Adding hitboxes, invincibility frames and cancel windows to each animation (TAE events) | https://github.com/Meowmaritus/DSAnimStudio |
| ERClipGeneratorTool | Registering new animations in Elden Ring's behaviour file | https://github.com/The12thAvenger/ERClipGeneratorTool |
| WitchyBND | Unpacking and repacking `c0000.anibnd.dcx` | https://github.com/ividyon/WitchyBND |
| Smithbox | Weapon, sorcery, damage and buff tables (params) | https://github.com/vawser/Smithbox |
| EldenRingHKS `c0000.hks` | Player behaviour script, if a move needs new input logic | https://github.com/soulsmods/EldenRingHKS |

Steps:

1. **Export Gojo's animations** from `CP_050/Animations` in FModel (same glTF setting as the model). Start with one combo and one cast.
2. **I write a retarget script** for Blender, using the bone map from Part 1, that moves each Cursed Clash animation onto the Elden Ring skeleton.
3. **Export as `.hkx`** with Soulstruct for Blender, replacing a test animation first (a fist light attack) to prove the pipeline works in game.
4. **Events.** In DS Anim Studio, copy the hitbox and cancel events from the Elden Ring attack each move replaces, then adjust the timing to Gojo's animation.
5. **Params.** In Smithbox I'll walk you through each new weapon, sorcery and buff entry, with the exact numbers.
6. **Test one move at a time** offline before adding the next.

Order of work: model first, then one combo animation as a pipeline test, then the sorceries, then Domain Expansion last.

## Keeping it light on your PC

A model swap costs almost nothing beyond Elden Ring itself, as long as the model stays near the size of Elden Ring's own armor:

- Keep the whole Gojo model at or under about 60,000 triangles. The dump in step 5 lists each mesh's polygon count; if it's over, I'll add a Decimate step to the step 6 script.
- Keep his textures at 2048x2048 or smaller.
- Use one material per piece where possible.
- The moves are animations and table changes; they cost nothing extra to run. Recoloured Elden Ring effects cost the same as the originals.

## Honest expectations

- This is hours of Blender work, not a button. I can write the scripts and read your error messages and screenshots, but I can't run the games or see the models from here.
- Cursed Clash uses a cel-shaded (anime outline) look; Elden Ring's shaders are realistic. Gojo will look like a realistic-lit version of himself, without the anime outlines.
- Gojo's proportions don't match the Tarnished's, so some parts will clip or stretch in some moves. Weight painting fixes most of it.
- If a step fails, send me the exact error or a screenshot and we go from there.
