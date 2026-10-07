# Handoff: Gojo in Elden Ring (read this first)

For a new session picking this project up.

## The project

The user asked to "merge" Elden Ring and Jujutsu Kaisen Cursed Clash. A real merge isn't possible: the two games run on different engines with no engine source, EldenRingHKS is just three player and enemy behaviour scripts, and the Cursed Clash UE5 Mod Kit ships no game assets. Agreed scope: Gojo's Cursed Clash model replacing one Elden Ring armor set (Part 1), then his moves rebuilt in Elden Ring (Part 2), loaded offline with Mod Engine 2, light on the PC (about 60k triangles or fewer, 2K textures).

Branch: `gojo-elden-ring` (this project only). The user's earlier SF6 Tekken Mode project lives on `claude/ff16-fortnite-melty-mashup-o6arrd`; leave it alone. Do not open a pull request unless the user asks.

## Where it stands

- Plan: `docs/gojo-for-elden-ring.md`.
- Both games are installed on the D: drive, probably `D:\steam\steamapps\common\Jujutsu Kaisen CC` and `D:\steam\steamapps\common\ELDEN RING\Game` (not yet confirmed).
- Gojo is `CP_050` (adult; `CP_051` is teen), from the ID table in https://github.com/MadMax1960/JJK-CC-Resources, which also has the `.usmap` FModel needs. Not yet seen in FModel by the user. The pack AES key is in the mod kit's `Content/Python/import_game_assets.py`.
- The user wants to play as Gojo with his moves. Part 2 of the plan covers this: retargeted Cursed Clash animations plus Elden Ring params and recoloured Elden Ring effects. Cursed Clash's own effects, the Domain Expansion cutscene and voice lines are out of scope.
- Waiting on: the user confirming `CP_050` in FModel, the armor set they want to replace, then the two skeleton dumps from `tools/blender/dump_armature.py`.

## The user

- Windows; the Desktop is inside OneDrive (`C:\Users\fudoh\OneDrive\Desktop`). No Blender installed yet.
- Not a programmer. Prefers plain language and one clear step at a time, with exact commands and where to paste them.

## Ground rules

- Offline play only. Never work around any anti-cheat.
- Do not copy game-derived assets (extracted models, textures, screenshots) into the repo or share them.
- Do not touch the user's game files without asking first.
- Say clearly what is verified and what is not.
