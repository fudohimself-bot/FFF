# SF6 Tekken Mode

Tekken-style mechanics for **Street Fighter 6**, for **offline play at home** (local versus, training). A personal mod, not published on Melty.

**Status: NOT YET RUN IN THE REAL GAME.** The rules are tested against a fake match and a fake REFramework (32 tests), but every game field this mod touches is still unproven until the probe below has run on a real copy of SF6. Treat it as untested.

## What it adds

| System | What it does | Status |
|---|---|---|
| Rage | A fighter at or under 20% health deals 15% more damage | built, untested in game |
| Heat | P1 presses **F1** (P2 **F2**) for 10 seconds of +15% damage and chip damage on blocked hits, then a 20 second cooldown. Keyboard only: REFramework can't read gamepad buttons | built, untested in game |
| Juggle scaling | Longer air combos | research only, not built |

Both built systems add their bonus by lowering the victim's health after a hit. Whether SF6 lets a script write health this way, and whether its rollback system overwrites it, is exactly what still has to be checked.

## Offline only

SF6 has in-process anti-cheat for online play, and mods can get an account banned there. REFramework disables its Lua scripts in online matches, but don't rely on that: **play offline only**, and keep the game's network features off while this is installed. Nothing here works around the anti-cheat.

## Install (Windows)

1. Install REFramework for SF6 from the [REFramework nightly releases](https://github.com/praydog/REFramework-nightly/releases) (the `SF6.zip`). Put its `dinput8.dll` in the game folder.
2. Copy this project's `reframework` folder into the SF6 game folder (merge with the existing `reframework` folder).
3. Start SF6 **offline**.

## First test: the probe

1. Start a local versus or training match.
2. Press **Insert** to open the REFramework menu. Find **SF6 Tekken Probe** and press **Run probe now**.
3. Send me `reframework/data/sf6_tekken/probe_report.json` (in the game folder). It says which of the field names worked. I then mark the hooks as verified or fix the ones that failed.
4. Then try the mod itself: open **SF6 Tekken Mode (offline only)** in the same menu to see its status and switch Rage or Heat off.

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

## Credits

Field names for SF6's battle data come from the community script [SF6_replay_capture](https://github.com/rkaganda/SF6_replay_capture) by rkaganda. Street Fighter 6 is a Capcom game. This project contains none of its files.
