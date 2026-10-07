# Handoff: Gojo in Elden Ring (read this first)

For a new session picking this project up.

## The project

The user asked to "merge" Elden Ring and Jujutsu Kaisen Cursed Clash. A real merge isn't possible: the two games run on different engines with no engine source, EldenRingHKS is just three player and enemy behaviour scripts, and the Cursed Clash UE5 Mod Kit ships no game assets. Agreed scope: Gojo's Cursed Clash model replacing one Elden Ring armor set (Part 1), then his moves rebuilt in Elden Ring (Part 2), loaded offline with Mod Engine 2. The user says their PC handles it: **don't downscale textures or decimate the mesh for performance.**

Branch: `gojo-elden-ring` (this project only). The user's earlier SF6 Tekken Mode project lives on `claude/ff16-fortnite-melty-mashup-o6arrd`; leave it alone. Do not open a pull request unless the user asks.

## Local setup on the user's PC (done 2026-10-07)

- Repo clone: `D:\GojoMod\fff`.
- Tools: `D:\GojoMod\tools` (FModel, Soulstruct-Blender 3.2.1, UXM 2.4.2, Smithbox 2.2.6, ModEngine2 2.1.0, WitchyBND 3.0.1.0, DSAnimStudio 4.9.9, ERClipGeneratorTool 1.0.0, `usmap`, portable Blender 5.1.2 in `blender-5.1.2-windows-x64`). Soulstruct is installed and enabled in that Blender as the extension `bl_ext.user_default.io_soulstruct`.
- `get_tools.ps1` was run. download.blender.org answered with a browser check page, so the script now falls back to official mirrors and checks Blender's SHA-256.
- Cursed Clash extractor (not in the repo; it has the pack keys in it): `D:\GojoER\tools\CUE4Parse\JjkExtract`, a small CUE4Parse console app built with the .NET 10 SDK in `D:\GojoER\tools\dotnet10`. Exe: `bin\Release\net10.0\JjkExtract.exe`. Usage: `JjkExtract list <filter>`, `JjkExtract export <filter> <outdir>` (set `JJK_FMT=gltf` for glTF). The first key in it opens all 53,896 files. This replaces FModel for steps 1 and 2.
- Extracted Cursed Clash files: `D:\GojoMod\work\cc_export` (outside the repo; never commit or share it).

## Where it stands

- Plan: `docs/gojo-for-elden-ring.md`. Steps 1 and 2 are done.
- Game folders confirmed: `D:\steam\steamapps\common\Jujutsu Kaisen CC` and `D:\steam\steamapps\common\ELDEN RING\Game`.
- Gojo is `CP_050`: outfits `SK_CP_050_00` to `_40`; `CP_050/Animations` has 262 files. `SK_CP_050_00` is exported as `.glb` plus textures. It has 61,725 triangles (about 31,700 without the anime outline shells, which are dropped because they render as a black skin in Elden Ring) and 223 bones (`root`, `COG`, `hip`, `spine`, `chest`, `neck`, `head`, `L_collar`, `L_arm`, `L_elbow`, `L_hand`, fingers `_A/_B/_C`, `L_leg`, `L_knee`, `L_ankle`, `L_toe`, `*_EX` helper bones, many `DyT_*` hair, hood and hem bones, face bones). Gojo's skeleton dump comes from the `.glb`, so the user doesn't need to make it in Blender.
- Not yet checked: which of the 5 outfits and which `_P1`/`_P2` part variants the user wants (no one has looked at the model yet).
- Waiting on: the armor set the user wants to replace, and permission to run UXM on the Elden Ring folder (UXM writes the unpacked files inside the game folder). After that, the Elden Ring skeleton dump.

## The user

- Windows; the Desktop is inside OneDrive (`C:\Users\fudoh\OneDrive\Desktop`).
- Not a programmer. Prefers plain language and one clear step at a time, with exact commands and where to paste them.

## Ground rules

- Offline play only. Never work around any anti-cheat.
- Do not copy game-derived assets (extracted models, textures, screenshots) into the repo or share them.
- Do not touch the user's game files without asking first.
- Say clearly what is verified and what is not.
