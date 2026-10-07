# Handoff: SF6 Tekken Mode (read this first)

For a new session picking this project up, for example a local session on the user's PC. Everything here was true when it was written; check the sheets and git log for anything newer.

## The project in one paragraph

A personal, **offline-only** REFramework Lua mod for **Street Fighter 6** that adds Tekken 8 style mechanics. It is not published anywhere. The user started by wanting an FF16 x Fortnite mashup on Melty, but that fell apart (Fortnite has Easy Anti-Cheat, no Melty-installed loader for FF16 or Fortnite). The project is now the SF6 mod plus an optional personal Joshua-for-Ken model swap. **Melty is out of scope.** A Melty token was given in the first message of the original session; it is not in this repo and must not be used or stored.

Repo: `fudohimself-bot/fff`, branch `claude/ff16-fortnite-melty-mashup-o6arrd`. Push to that branch only. Do not open a pull request unless the user asks.

## How the repo works

- `sheets/hooks.json`: every read or write of the game, one row each, with `read_verified` / `write_verified` and `evidence`. **Source of truth.**
- `sheets/mechanics.json`: one row per system (rage, heat, heat_smash, rage_art, slowmo_fx, hitstop_boost, heat_gauge, plus research rows).
- `src/engine.lua.tpl`: the rules (pure logic, `Engine.step`) and the REFramework glue. `src/probe.lua.tpl`: the probe.
- `tools/build.py preflight|generate`: lists unfilled cells, broken references, unbuilt and unverified rows; `generate` writes `reframework/autorun/sf6_tekken_mode.lua` and `sf6_tekken_probe.lua`. **Never hand-edit those two generated files.**
- `tests/test_engine.py`: 127 tests. They run the generated Lua in a Lua runtime (`pip install lupa`) against a fake match and a fake REFramework. `tests/test_blender_dump.py` tests the Blender helper.
- Workflow: change the sheet first, then the template, then `python3 -I tools/build.py generate`, then `python3 -I tests/test_engine.py`, then commit and push. Preflight must be clean before building.
- Other files: `docs/joshua-for-ken.md` (model swap plan), `tools/blender/dump_armature.py`, `tools/ff16/extract_c1002.bat`, `README.md` (status table).

## What exists and its status

Confirmed in the real game by the user (offline Training and Versus), 2026-10-07:
- All hooks in `sheets/hooks.json` marked verified read fine; health writes are kept; extra `hit_stop` frames are honoured.
- Rage (Tekken 8: at or under 25% health, +10% rounded down, 70% less chip taken), Heat (F1 for P1, F2 for P2: once per round, 10 s timer that stops while the opponent is in hitstun, no damage bonus, chip on block that cannot KO and is recoverable), Heat Smash and Rage Art stand-ins (second Heat key press arms a Smash; F3 / F4 in Rage arms a Rage Art) and the hit freeze boost: the user said these "feel good".
- Settings (checkboxes, sliders) are saved to `reframework/data/sf6_tekken/settings.json` in the game folder.

Built but **not seen in the game yet**: the on-screen Heat gauge (`heat_gauge`, drawn with REFramework's `draw` API; default position chosen from a 1911x1105 screenshot; look is from memory of Tekken 8, so a reference screenshot would help).

Experimental and off by default: `slowmo_fx`. Only the `max_fps` method visibly slowed SF6 (global speed and scene time scale did nothing); it looks choppy.

## Open items, in priority order

1. **"Weighted punches" don't seem to be added** (user report, latest). The hit freeze boost (`hitstop_boost`, on by default, +3 frames per landed hit, +10 on Smash / Art) used to feel good. Find out why it is not noticeable now. Ask the user for the SF6 Tekken Mode panel readings after a few landed hits: is `hitstop_boost enabled` ticked, is "Hit freeze boosts applied" going up, is there a "Hit freeze error" line, what does "Settings:" say. Possible causes to check: a saved settings.json with the box off, blocks not counting (only damaging hits count), 3 frames being too subtle, or a regression in `src/engine.lua.tpl`.
2. Heat gauge in the real game: placement, thickness, colours. Offer the panel's gauge sliders; ask for a Tekken 8 Heat gauge reference screenshot to match the art.
3. **Joshua model for Ken** (personal use; do not share or commit extracted assets). The user wants **Joshua at the older age in the red hooded cape, black tunic, red belt, black gloves, shaggy ginger hair**. FF16 character `c1002` body `b0001` was extracted, converted and rendered: it is a leather vest with shoulder plates and boots, no cape, so it is **not** the target. Next step: extract the game's `nxd` data tables (from `0001.pac`, via `FF16Tools.CLI nxd-to-sqlite`) to tie character names to `c####` IDs. Then rig onto Ken's skeleton in Blender with RE Mesh Editor. Plan and tools: `docs/joshua-for-ken.md`. Blender 4.2.3 worked headless in the cloud session; the user has no Blender installed.
4. Research: knockback, wall carry and juggle scaling (fields `combo_dm_air`, `combo_scale`, `vector_zuri`, `damage_speed` exist on the fighter object); starting Heat from a gamepad button combo (the panel shows `pl_sw_now` bits so they can be decoded).

## The user's PC (as learned in the cloud session)

- Windows; the Desktop is inside OneDrive, so `%USERPROFILE%\Desktop` does not exist (use `C:\Users\fudoh\OneDrive\Desktop`).
- FF16 packs: `D:\steam\steamapps\common\FINAL FANTASY XVI\data\`. SF6 install path: not yet given; ask.
- REFramework v1.5.9.1 is installed for SF6; the mod's `reframework\autorun` has the two generated `.lua` files; open the menu with Insert, panels are under Script Generated UI.
- FF16Tools.CLI 1.13.3 and the FF16 Model Importer (`MdlConverter.exe`) are unzipped under `C:\Users\fudoh\OneDrive\Desktop\New folder (11)\win-x64\`; extracted files are in `joshua_extract` there. `FF16Tools.CLI list-files` writes `<pack>_files.txt` next to the pack, not where you redirect output.

## Ground rules

- Offline play only. SF6 has anti-cheat for online play. Never work around any anti-cheat.
- Do not copy game-derived assets (extracted models, textures, screenshots) into the repo or share them.
- Do not touch the user's game files without asking first.
- Say clearly what is verified and what is not. The user tests in the real game and reports back; do not claim something works until they say so or a probe shows it.
- The user prefers plain language and one clear step at a time, and is not a programmer. Give exact commands and where to paste them.
- Keep secrets (tokens, keys) out of the repo, commits and replies.
