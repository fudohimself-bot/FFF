# Gojo in Elden Ring

A personal, **offline-only** mod: Gojo Satoru's model from Jujutsu Kaisen Cursed Clash, worn by your Elden Ring character in place of one armor set, loaded with Mod Engine 2.

**Status: plan only. Nothing has been run on the real games yet.**

- `docs/gojo-for-elden-ring.md`: the tools and the step-by-step plan.
- `tools/blender/dump_armature.py`: dumps a model's skeleton from Blender to a small JSON file, so a bone map from Gojo to the Elden Ring body can be written.

## Ground rules

- Offline only. Mod Engine 2 starts Elden Ring with Easy Anti-Cheat off; nothing here works around any anti-cheat.
- No game files in this repo: extracted models, textures and converted armor files stay on your PC. They are Bandai Namco's and FromSoftware's assets.

## Credits

Jujutsu Kaisen Cursed Clash is a Bandai Namco game; Elden Ring is a FromSoftware / Bandai Namco game. This project contains none of their files. Pack-reading details come from the [JJK Cursed Clash UE5 Mod Kit](https://github.com/JJKCursedClashModding/UE5-Mod-Kit); Elden Ring behaviour scripts are at [soulsmods/EldenRingHKS](https://github.com/soulsmods/EldenRingHKS).
