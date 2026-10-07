# SF6 Tekken Mode

Tekken-style mechanics for **Street Fighter 6**, for **offline play at home** (local versus, training). A personal mod, not published on Melty.

**Status: Rage, Heat, Heat Smash, Rage Art and the hit freeze boost work and feel good in offline play (user report, 2026-10-07); the impact slow-motion is off by default and looks choppy.** In real offline matches every field the mod needs read correctly, health writes were kept and the game honoured extra hit freeze frames. The rules are tested against a fake match and a fake REFramework (124 tests).

## What it adds

| System | What it does | Status |
|---|---|---|
| Rage | Tekken 8 season 3: at or under 25% health, every hit deals 10% more damage (rounded down) and you take 70% less chip damage | built, untested in game |
| Heat | P1 presses **F1** (P2 **F2**): once per round, 10 seconds of running time that stops while the opponent is in hitstun. No damage bonus. Blocked hits chip the blocker (2% of max health, an estimate) | built, untested in game |
| Recoverable health | Heat chip can't KO and is won back (1% of max health per landed attack, an estimate) when the chipped fighter lands attacks. A hit on a fighter not in Heat eats 30% of its damage from their recoverable health | built, untested in game |
| Heat start heal | Starting Heat wins back half of your recoverable health (an estimate), like Tekken's Engager | built, untested in game |
| Heat Smash (stand-in) | Press the Heat key again while in Heat to arm it for 2 seconds. Your next hit deals 15% of max health extra and uses up your Heat. If it doesn't land in time, the Heat is spent anyway. A block doesn't use it up | built, untested in game. Not the real move: no animation or armor |
| Rage Art (stand-in) | While in Rage, press **F3** (P2 **F4**), once per round. Your next hit within 2 seconds deals 18% of max health extra, removes the opponent's recoverable health, wins back some of yours and ends your Rage. If it misses, Rage still ends | built, untested in game. Not the real move: no cinematic |
| Heat gauge (on-screen) | A Tekken 8 style gauge under each health bar, drawn by the mod: an orange bar that drains over Heat's 10 seconds with the seconds left shown, pale blue while the timer is paused, flashing red under 25%, a thin outline labelled HEAT when Heat is available, a thin recoverable-health bar, and RAGE / HEAT SMASH ARMED / RAGE ART ARMED labels. Position and size are sliders in the panel and are saved | built, untested in game. The default position was chosen from a screenshot at 1911x1105; other resolutions are untested |
| Impact slow-motion | When a Heat Smash or Rage Art lands, the game slows to 50% for about half a second | experimental, **off by default**. Only the frame cap method visibly slowed SF6 in testing (it looks choppy, since it lowers the frame rate). Speed and length can be changed live in the panel |
| Hit freeze boost (weightier hits) | When a hit lands, adds 3 frames to the game's `hit_stop` counter on both fighters (10 when a Heat Smash or Rage Art lands) | **on by default**: the user tried it offline and said it feels good. Sizes adjustable live in the panel |
| Juggle scaling | Longer air combos | research only, not built |

**Not possible in this mod** (they need new moves, animations or movement, not state changes): the real Heat Smash and Rage Art moves, Heat Dash, Heat Burst as a 2+3 input, Heat Engager moves, sidesteps, Tekken's four-button layout and a Tekken move list for any SF6 fighter. **Possible but needs more research:** wall carry and bounce tuning, and starting Heat from a gamepad button combo (the panel shows the game's raw held-button bits so they can be decoded).

Both built systems add their bonus by lowering the victim's health after a hit. SF6 accepted these writes in real offline matches. What isn't known yet is how the game's rollback system behaves over a long session, and whether the on-screen health bar always follows the written value.

## Settings

The panel's checkboxes, sliders and slow-motion method are saved automatically to `reframework/data/sf6_tekken/settings.json` in the game folder and loaded next time. Bad or out-of-range values in that file are ignored or clamped, and the panel has a **reset settings to defaults** button. Delete the file to start fresh.

## Offline only

SF6 has in-process anti-cheat for online play, and mods can get an account banned there. REFramework disables its Lua scripts in online matches, but don't rely on that: **play offline only**, and keep the game's network features off while this is installed. Nothing here works around the anti-cheat.

## Install (Windows)

1. Install REFramework for SF6 from the [REFramework nightly releases](https://github.com/praydog/REFramework-nightly/releases) (the `SF6.zip`). Put its `dinput8.dll` in the game folder.
2. Copy this project's `reframework` folder into the SF6 game folder (merge with the existing `reframework` folder).
3. Start SF6 **offline**.

## First test: the probe

1. Start a local versus or training match.
2. Press **Insert** to open the REFramework menu. Find **SF6 Tekken Probe** and press **Run probe now**.
3. Send me `reframework/data/sf6_tekken/probe_report.json` (in the game folder). It says which of the field names worked.
4. Press **Run write test**. It takes 1 health point from P1 and checks, right away and again 1, 30 and 120 frames later, whether the game kept the change. Send me `write_test_report.json` from the same folder.
5. Then try the mod itself: open **SF6 Tekken Mode (offline only)** in the same menu. It shows each player's Rage and Heat state, and how many bonus health writes it has made.

## How it's built

- `sheets/hooks.json`: every read or write of the game, one row each. **Source of truth.**
- `sheets/mechanics.json`: one row per Tekken-style system.
- `src/*.lua.tpl`: the rules and the REFramework glue.
- `tools/build.py preflight`: lists unfilled cells, broken references, unbuilt rows and unverified rows.
- `tools/build.py generate`: runs the preflight, then writes `reframework/autorun/*.lua`. Don't edit those files by hand; change the sheets, then regenerate.
- `tests/test_engine.py`: needs `lupa` (`pip install lupa`).

```
python3 -I tools/build.py generate
python3 -I tests/test_engine.py
```

## Joshua for Ken (planned)

A personal-use model swap putting Joshua Rosfield from FF16 on Ken's default look. Plan and tools are in `docs/joshua-for-ken.md`; `tools/blender/dump_armature.py` dumps a skeleton from Blender so a bone map can be written. Nothing has been run on real models yet.

## Credits

Field names for SF6's battle data come from the community script [SF6_replay_capture](https://github.com/rkaganda/SF6_replay_capture) by rkaganda. Street Fighter 6 is a Capcom game. This project contains none of its files.
