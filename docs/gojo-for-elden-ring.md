# Gojo as the Elden Ring player (personal, offline use)

Status: **steps 1 and 2 done on the user's PC (2026-10-07); the rest is not yet run.** Verified so far: both game folders are where the table below says; the first Cursed Clash AES key opens the packs; `CP_050` is adult Gojo (outfits `SK_CP_050_00` to `_40`, 262 animation files); `SK_CP_050_00` exports as glTF with its PNG textures. All tools are in `D:\GojoMod\tools`, with Blender 5.1.2 and Soulstruct for Blender 3.2.1 installed. The art work has to happen on your Windows PC with your own copies of Jujutsu Kaisen Cursed Clash and Elden Ring. Keep the extracted and converted files on your PC: they are Bandai Namco's and FromSoftware's assets, so don't share or upload them, and never put them in this repo. Play offline only.

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
3. **Pick the armor set to replace.** Chosen: **the Prisoner set** (the Prisoner class's starting armor). Read from `regulation.bin` (EquipParamProtector) and checked against UXM's file list:

   | Piece | Row | Model | Files in `parts\` |
   |---|---|---|---|
   | Prisoner Iron Mask | 890000 | 1410 | `hd_m_1410`, `hd_m_1410_l` |
   | Prisoner Clothing | 890100 | 1410 | `bd_m_1410`, `bd_m_1410_l`, `bd_f_1410`, `bd_f_1410_l` |
   | Prisoner Trousers | 890300 | 1410 | `lg_m_1410`, `lg_m_1410_l` |

   All are `.partsbnd.dcx`; `_l` is the low-detail copy the game shows at a distance. The body has separate male and female files, so both get Gojo. The set has no arms piece (no row 890200), so the player's bare arms show; Gojo's sleeves and hands go into the body piece, and step 9 hides the bare arms.
4. **Unpack Elden Ring** with UXM Selective Unpacker, choosing only the `parts` folder.
5. **Dump both skeletons.** **Done 2026-10-07, without opening Blender's window:** `tools/blender/dump_gltf.py` (Gojo) and `tools/blender/dump_er_parts.py` (Elden Ring pieces through Soulstruct) write the same JSON as `dump_armature.py`, which now also records how many vertices each bone really moves. The Prisoner pieces give positions for the body, head and leg bones; a gauntlet (`am_m_1010`) gives the finger bones. Both models face -Y and rest in a 45° A-pose. Gojo is taller (shoulders about 14 cm higher; legs about the same length), so step 6 moves his joints onto the Elden Ring joints rather than scaling him evenly. The manual way, for reference: in Blender, import Gojo's `.gltf` into an empty scene, open the Scripting tab, open `tools/blender/dump_armature.py` from this project and press Run Script. It writes `armature_dump_<name>.json` to your Desktop, named after the Blender file, so save each scene first with its own name (for example `gojo.blend` and `eldenring.blend`). Do the same with the body armor piece imported through Soulstruct for Blender. **Send me both files.** They are small text files.
6. **I write the bone map.** The map is done: `tools/blender/gojo_to_er_bones.json` sends all 223 Gojo bones to 68 Elden Ring bones (12 bones that move no vertices are dropped; hair, face and blindfold bones follow `Head`, hood bones `Spine2`, coat-hem bones `L/R_ThighTwist`). The fit script `tools/blender/fit_gojo.py` is written and ran on 2026-10-07: it builds an 86-bone Elden Ring skeleton from the bones the armor pieces really use, squashes Gojo's torso evenly (0.817) from hip to neck, lines up arms, legs and fingers joint by joint, renames his weights to Elden Ring bones (at most 4 per vertex) and saves `D:\GojoMod\work\gojo_fit.blend`. A pose test (arm up, elbow and knee bent, head turned) deforms cleanly in its renders. Not yet looked at by the user; outlines and textures are not in it yet. From the two dumps I build a table that says which of Gojo's bones follow which Elden Ring bones, and a Blender script that applies it: renames or merges the vertex groups, fits Gojo to the Elden Ring body's height and pose, and drops bones Elden Ring can't use.
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

## Model size and textures

The user's PC handles the model as it is, so **don't downscale textures or decimate the mesh** to save performance (user's decision, 2026-10-07).

What `SK_CP_050_00` contains (read from the exported `.glb`): 61,725 triangles in 21 parts and 223 bones. About 30,000 of those triangles are the anime outline shells (the materials with `Outline` in the name); see "Keeping the anime look" below. Some parts come in `_P1` and `_P2` versions; **the user chose `_P2`** (no blindfold, hair down, blue eyes; `_P1` is the blindfold look). `Decal` and `DecayDecal` are Cursed Clash's battle-damage marks and are dropped. With `_P2` and without outlines and decals he is 24,496 triangles.

## Keeping the anime look (only on Gojo)

The user wants Gojo to keep his Cursed Clash look, on him only. Cursed Clash's shaders are Unreal Engine materials and can't run in Elden Ring, so the look is rebuilt from three parts:

1. **Colours:** his Cursed Clash colour textures are already flat, hand-painted anime colours and are used as they are.
2. **Outlines:** checked on the `.glb`: the outline meshes are exact copies of the body, facing the same way, with no gap. Cursed Clash pushes them out and turns them inside out in its shader. That gets done ahead of time in Blender: push each outline copy out along its normals by a small width, flip its faces, give it a plain black material and turn back-face culling on (Soulstruct writes culling per material into the FLVER). It's skinned to the same bones, so it moves with him. Not yet tested in game.
3. **Lighting:** Elden Ring will still light and shadow him with its own realistic lighting; that part of the toon look can't come across. A flatter look can be tried later by picking a low-shine Elden Ring material, or one with some self-lighting (which would also glow faintly in dark places). Not yet tested.

Moves are animations and table changes and cost nothing extra to run.

## Honest expectations

- This is hours of Blender work, not a button. I can write the scripts and read your error messages and screenshots, but I can't run the games or see the models from here.
- Cursed Clash uses a cel-shaded look; Elden Ring's lighting is realistic. With his own textures and baked outlines (see "Keeping the anime look") he keeps his colours and black outlines, but Elden Ring's lights and shadows still fall on him.
- Gojo's proportions don't match the Tarnished's, so some parts will clip or stretch in some moves. Weight painting fixes most of it.
- If a step fails, send me the exact error or a screenshot and we go from there.
