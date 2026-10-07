# Handoff: Gojo in Elden Ring (read this first)

For a new session picking this project up.

## The project

The user asked to "merge" Elden Ring and Jujutsu Kaisen Cursed Clash. A real merge isn't possible: the two games run on different engines with no engine source, EldenRingHKS is just three player and enemy behaviour scripts, and the Cursed Clash UE5 Mod Kit ships no game assets. Agreed scope: Gojo's Cursed Clash model replacing one Elden Ring armor set, loaded offline with Mod Engine 2, light on the PC (about 60k triangles or fewer, 2K textures). A Gojo-style moveset via `c0000.hks` is a possible later step.

Branch: `gojo-elden-ring` (this project only). The user's earlier SF6 Tekken Mode project lives on `claude/ff16-fortnite-melty-mashup-o6arrd`; leave it alone. Do not open a pull request unless the user asks.

## Where it stands

- Plan: `docs/gojo-for-elden-ring.md`.
- Both games are installed on the D: drive, probably `D:\steam\steamapps\common\Jujutsu Kaisen CC` and `D:\steam\steamapps\common\ELDEN RING\Game` (not yet confirmed).
- Cursed Clash characters are under `Content/Characters/CP_###` in the packs. Which number is Gojo is unknown; the user is checking in FModel. The pack AES key is in the mod kit's `Content/Python/import_game_assets.py`.
- Waiting on: Gojo's `CP_###` number, the armor set the user wants to replace, then the two skeleton dumps from `tools/blender/dump_armature.py`.

## The user

- Windows; the Desktop is inside OneDrive (`C:\Users\fudoh\OneDrive\Desktop`). No Blender installed yet.
- Not a programmer. Prefers plain language and one clear step at a time, with exact commands and where to paste them.

## Ground rules

- Offline play only. Never work around any anti-cheat.
- Do not copy game-derived assets (extracted models, textures, screenshots) into the repo or share them.
- Do not touch the user's game files without asking first.
- Say clearly what is verified and what is not.
