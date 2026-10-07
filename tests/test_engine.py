"""Tests for the generated mod's rules (run against a fake match) and for the preflight itself.

  python3 -m venv .venv && .venv/bin/pip install lupa
  .venv/bin/python -I tests/test_engine.py
"""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("build", ROOT / "tools" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def load_engine():
    """Load the generated mod outside the game: no `re`/`sdk` globals, so only the rules are defined."""
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute((ROOT / "reframework" / "autorun" / "sf6_tekken_mode.lua").read_text())
    return lua, lua.eval("SF6_TEKKEN")


class Match:
    """A fake match: set health / guard / keys, then tick."""

    def __init__(self, lua, g):
        self.lua, self.g = lua, g
        self.engine = g.Engine
        self.state = self.engine.new_state()
        self.round, self.timer = 1, 0
        self.hp = [1000, 1000]
        self.hp_max = None  # None = game gave no max health (engine falls back to highest seen)
        self.guard = [0, 0]
        self.hitstun = [0, 0]
        self.send_hitstun = True
        self.keys = [False, False]
        self.art_keys = [False, False]

    def tick(self, advance=True, **kw):
        """One match tick. advance=False repeats the previous timer value, like an extra render frame."""
        if advance:
            self.timer += 1
        for k, v in kw.items():
            setattr(self, k, v)
        extra = {}
        extra["art_keys"] = self.lua.table_from({0: self.art_keys[0], 1: self.art_keys[1]})
        if self.send_hitstun:
            extra["hitstun"] = self.lua.table_from({0: self.hitstun[0], 1: self.hitstun[1]})
        if self.hp_max is not None:
            extra["hp_max"] = self.lua.table_from({0: self.hp_max[0], 1: self.hp_max[1]})
        snap = self.lua.table(
            round=self.round,
            timer=self.timer,
            **extra,
            hp=self.lua.table_from({0: self.hp[0], 1: self.hp[1]}),
            guard=self.lua.table_from({0: self.guard[0], 1: self.guard[1]}),
            keys=self.lua.table_from({0: self.keys[0], 1: self.keys[1]}),
        )
        writes = self.engine.step(self.state, snap)
        out = {int(k): int(v) for k, v in writes.items()}
        for i, v in out.items():
            self.hp[i] = v  # the glue writes the new health back to the game
        return out


class EngineRules(unittest.TestCase):
    def setUp(self):
        self.lua, self.g = load_engine()
        self.m = Match(self.lua, self.g)
        self.m.tick()  # first observation sets max health

    def hit(self, victim, damage):
        self.m.hp[victim] -= damage
        return self.m.tick()

    def test_no_bonus_without_rage_or_heat(self):
        self.assertEqual(self.hit(1, 100), {})

    def test_rage_adds_bonus_damage_below_threshold(self):
        self.m.tick(hp=[190, 1000])  # P1 (index 0) at 19%, under the 25% line
        writes = self.hit(1, 100)  # Rage +10% -> 110 total, so 10 extra
        self.assertEqual(writes, {1: 890})

    def test_rage_not_active_above_threshold(self):
        self.m.tick(hp=[300, 1000])  # 30%
        self.assertEqual(self.hit(1, 100), {})

    def test_rage_off_when_disabled(self):
        self.g.MECH.rage.enabled = False
        self.m.tick(hp=[100, 1000])
        self.assertEqual(self.hit(1, 100), {})

    def test_dead_fighter_has_no_rage(self):
        self.m.tick(hp=[0, 1000])
        self.assertEqual(self.hit(1, 100), {})

    def test_heat_key_starts_heat_but_gives_no_damage_bonus(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.assertTrue(self.g.Engine.heat_active(self.m.state, 0))
        self.assertEqual(self.hit(1, 100), {})  # Tekken 8 Heat has no general damage bonus

    def test_heat_expires_after_duration(self):
        self.m.tick(keys=[True, False])
        for _ in range(600):
            self.m.tick(keys=[False, False])
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))
        self.assertEqual(self.hit(1, 100), {})

    def test_heat_cannot_be_used_twice_in_a_round(self):
        self.m.tick(keys=[True, False])
        for _ in range(610):
            self.m.tick(keys=[False, False])
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))
        self.m.tick(keys=[True, False])  # second press in the same round
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))
        self.assertFalse(self.g.Engine.heat_available(self.m.state, 0))

    def test_heat_is_available_again_next_round(self):
        self.m.tick(keys=[True, False])
        for _ in range(610):
            self.m.tick(keys=[False, False])
        self.m.tick(round=2, keys=[False, False])
        self.assertTrue(self.g.Engine.heat_available(self.m.state, 0))
        self.m.tick(keys=[True, False])
        self.assertTrue(self.g.Engine.heat_active(self.m.state, 0))

    def test_heat_timer_stops_while_opponent_is_in_hitstun(self):
        self.m.tick(keys=[True, False])
        for _ in range(100):
            self.m.tick(keys=[False, False], hitstun=[0, 20])  # P2 is being hit
        self.assertEqual(self.g.Engine.heat_left(self.m.state, 0), 600)
        for _ in range(50):
            self.m.tick(hitstun=[0, 0])
        self.assertEqual(self.g.Engine.heat_left(self.m.state, 0), 550)

    def test_own_hitstun_does_not_stop_your_heat_timer(self):
        self.m.tick(keys=[True, False])
        for _ in range(10):
            self.m.tick(keys=[False, False], hitstun=[20, 0])  # P1 is being hit
        self.assertEqual(self.g.Engine.heat_left(self.m.state, 0), 590)

    def test_missing_hitstun_data_does_not_stop_the_timer(self):
        self.m.send_hitstun = False
        self.m.tick(keys=[True, False])
        for _ in range(10):
            self.m.tick(keys=[False, False])
        self.assertEqual(self.g.Engine.heat_left(self.m.state, 0), 590)

    def test_held_key_does_not_retrigger(self):
        self.m.tick(keys=[True, False])
        for _ in range(600 + 5):
            self.m.tick(keys=[True, False])
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))

    def test_heat_chip_damage_on_block_start(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        writes = self.m.tick(guard=[0, 12])  # P2 starts blocking; chip = 2% of 1000 = 20
        self.assertEqual(writes, {1: 980})
        self.assertEqual(self.m.state["chip_count"], 1)
        self.assertEqual(self.m.tick(guard=[0, 11]), {})  # blockstun continues: no second chip

    def test_chip_never_kills(self):
        self.m.tick(hp=[1000, 5])  # damage taken before Heat: no bonus applies
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        writes = self.m.tick(guard=[0, 12])
        self.assertEqual(writes, {1: 1})
        self.m.tick(guard=[0, 0])
        self.assertEqual(self.m.tick(guard=[0, 12]), {})  # at 1 health: nothing more to take

    def test_no_chip_without_heat(self):
        self.assertEqual(self.m.tick(guard=[0, 12]), {})

    def test_same_timer_does_not_double_apply(self):
        self.m.tick(hp=[100, 1000])  # P1 enters Rage
        self.m.hp[1] -= 100
        self.assertEqual(self.m.tick(advance=False), {})  # same timer value: not processed yet
        self.assertEqual(self.m.tick(), {1: 890})  # the next match tick applies the bonus once
        self.assertEqual(self.m.tick(advance=False), {})
        self.assertEqual(self.m.tick(), {})

    def test_round_change_resets_state(self):
        self.m.tick(keys=[True, False])
        self.m.tick(round=2, hp=[1000, 1000], keys=[False, False])
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))
        self.assertEqual(self.hit(1, 100), {})

    def test_heal_does_not_count_as_damage(self):
        self.m.tick(hp=[190, 700])
        self.m.tick(hp=[190, 800])  # P2 recovers health
        self.assertEqual(self.m.tick(hp=[190, 800]), {})

    def test_heat_adds_nothing_on_top_of_rage(self):
        self.m.tick(hp=[100, 1000])  # P1 in Rage
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.assertEqual(self.hit(1, 100), {1: 890})  # only Rage's 15%

    def test_chip_cannot_ko_and_is_recoverable(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.assertEqual(self.m.tick(guard=[0, 12]), {1: 980})
        self.assertEqual(self.m.state["p"][1]["pool"], 20)

    def test_landing_an_attack_wins_back_recoverable_health(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.m.tick(guard=[0, 12])  # P2 chipped for 20
        self.m.tick(guard=[0, 0])
        self.m.hp[0] -= 10  # P1 takes a hit, which counts as P2 landing an attack
        writes = self.m.tick()
        self.assertEqual(writes, {1: 990})  # P2 regains 1% of max (10), pool 20 -> 10
        self.assertEqual(self.m.state["p"][1]["pool"], 10)

    def test_recovery_is_capped_by_what_chip_took(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.m.tick(guard=[0, 12])  # pool 20
        self.m.tick(guard=[0, 0])
        for _ in range(5):
            self.m.hp[0] -= 10
            self.m.tick()
        self.assertEqual(self.m.hp[1], 1000)  # back to full, never above max
        self.assertEqual(self.m.state["p"][1]["pool"], 0)

    def test_recoverable_pool_resets_each_round(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.m.tick(guard=[0, 12])
        self.m.tick(round=2, guard=[0, 0])
        self.assertEqual(self.m.state["p"][1]["pool"], 0)

    def test_blocking_a_move_counts_as_landing_for_recovery(self):
        self.m.tick(keys=[False, True])  # P2 Heat on
        self.m.tick(keys=[False, False])
        self.m.tick(guard=[12, 0])  # P1 blocks P2's attack: chipped 20, pool 20
        self.m.tick(guard=[0, 0])
        self.m.tick(guard=[0, 12])  # P2's block starts: P1 landed an attack, regains
        self.assertEqual(self.m.hp[0], 990)


class TekkenAccuracy(unittest.TestCase):
    def setUp(self):
        self.lua, self.g = load_engine()
        self.m = Match(self.lua, self.g)
        self.m.tick()

    def hit(self, victim, damage):
        self.m.hp[victim] -= damage
        return self.m.tick()

    def heat_on(self, i=0):
        keys = [False, False]
        keys[i] = True
        self.m.tick(keys=keys)
        self.m.tick(keys=[False, False])

    def test_rage_threshold_is_a_quarter_of_max_health(self):
        self.m.tick(hp=[250, 1000])  # exactly 25%: Rage
        self.assertTrue(self.m.state["p"][0]["rage"])
        self.m.tick(hp=[251, 1000])
        self.assertFalse(self.m.state["p"][0]["rage"])

    def test_rage_bonus_is_ten_percent_rounded_down(self):
        self.m.tick(hp=[100, 1000])
        self.assertEqual(self.hit(1, 109), {1: 1000 - 109 - 10})  # 10.9 -> 10
        self.assertEqual(self.hit(1, 9), {})  # 0.9 -> 0, no write

    def test_rage_cuts_chip_taken_by_seventy_percent(self):
        self.heat_on(1)  # P2 in Heat
        self.m.tick(hp=[200, 1000])  # P1 in Rage (20%)
        writes = self.m.tick(guard=[12, 0])  # P1 blocks P2's Heat attack: 20 * 0.3 = 6
        self.assertEqual(writes, {0: 194})

    def test_hit_eats_recoverable_health_when_not_in_heat(self):
        self.heat_on(0)
        self.m.tick(guard=[0, 12])  # P2 chipped: pool 20
        self.m.tick(guard=[0, 0])
        self.hit(1, 40)  # 30% of 40 = 12 off the pool (P1's attack landing also wins back 10 first)
        self.assertEqual(self.m.state["p"][1]["pool"], 20 - 12 - 0)

    def test_hit_does_not_eat_recoverable_health_while_in_heat(self):
        self.heat_on(0)
        self.heat_on(1)
        self.m.tick(guard=[0, 12])
        self.assertGreater(self.m.state["p"][1]["pool"], 0)
        self.m.tick(guard=[0, 0])
        pool = self.m.state["p"][1]["pool"]
        self.m.hp[1] -= 40
        self.m.tick()
        self.assertEqual(self.m.state["p"][1]["pool"], pool)


class StandInMoves(unittest.TestCase):
    """Heat Smash and Rage Art stand-ins, and the Heat-start heal."""

    def setUp(self):
        self.lua, self.g = load_engine()
        self.m = Match(self.lua, self.g)
        self.m.tick()

    def press_heat(self, i=0):
        keys = [False, False]
        keys[i] = True
        self.m.tick(keys=keys)
        self.m.tick(keys=[False, False])

    def press_art(self, i=0):
        keys = [False, False]
        keys[i] = True
        self.m.tick(art_keys=keys)
        self.m.tick(art_keys=[False, False])

    def hit(self, victim, damage):
        self.m.hp[victim] -= damage
        return self.m.tick()

    def p(self, i):
        return self.m.state["p"][i]

    # Heat Smash
    def test_second_heat_press_arms_smash_and_next_hit_deals_bonus_and_spends_heat(self):
        self.press_heat()
        self.press_heat()  # second press: armed
        self.assertGreater(self.p(0)["smash_left"], 0)
        writes = self.hit(1, 100)  # 100 + 15% of 1000 max = 150 extra
        self.assertEqual(writes, {1: 1000 - 100 - 150})
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))
        self.assertEqual(self.m.state["smash_count"], 1)

    def test_smash_cannot_be_armed_without_heat(self):
        self.m.tick(keys=[False, False])
        self.assertEqual(self.p(0)["smash_left"], 0)

    def test_missed_smash_still_spends_heat(self):
        self.press_heat()
        self.press_heat()
        for _ in range(125):
            self.m.tick()
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))
        self.assertIn("Heat Smash MISSED", str(self.m.state["last_event"]))

    def test_blocked_attack_does_not_use_up_the_smash(self):
        self.press_heat()
        self.press_heat()
        self.m.tick(guard=[0, 12])  # chip, but the smash stays armed
        self.assertGreater(self.p(0)["smash_left"], 0)
        self.assertTrue(self.g.Engine.heat_active(self.m.state, 0))

    def test_smash_disabled_by_switch(self):
        self.g.MECH.heat_smash.enabled = False
        self.press_heat()
        self.press_heat()
        self.assertEqual(self.p(0)["smash_left"], 0)
        self.assertEqual(self.hit(1, 100), {})

    def test_smash_can_ko(self):
        self.m.tick(hp=[1000, 120])
        self.press_heat()
        self.press_heat()
        self.assertEqual(self.hit(1, 50), {1: 0})

    # Rage Art
    def test_rage_art_needs_rage(self):
        self.press_art()
        self.assertEqual(self.p(0)["art_left"], 0)

    def test_rage_art_lands_for_bonus_clears_pool_and_spends_rage(self):
        self.m.tick(hp=[200, 1000])  # P1 in Rage
        self.p(1)["pool"] = 30  # P2 has recoverable health
        self.press_art()
        self.assertGreater(self.p(0)["art_left"], 0)
        writes = self.hit(1, 100)  # 100 + Rage 10 = 110, then Art 18% of 1000 = 180
        self.assertEqual(writes, {1: 1000 - 110 - 180})
        self.assertEqual(self.p(1)["pool"], 0)
        self.assertEqual(self.m.state["art_count"], 1)
        self.m.tick()
        self.assertFalse(self.p(0)["rage"])  # Rage is spent

    def test_rage_art_once_per_round(self):
        self.m.tick(hp=[200, 1000])
        self.press_art()
        self.hit(1, 100)
        self.m.tick(hp=[150, 1000])  # still low, but Rage is spent
        self.press_art()
        self.assertEqual(self.p(0)["art_left"], 0)

    def test_rage_art_is_available_again_next_round(self):
        self.m.hp_max = [1000, 1000]
        self.m.tick(hp=[200, 1000])
        self.press_art()
        self.hit(1, 100)
        self.m.tick(round=2, hp=[200, 1000])
        self.m.tick(hp=[200, 1000])
        self.press_art()
        self.assertGreater(self.p(0)["art_left"], 0)

    def test_missed_rage_art_spends_rage(self):
        self.m.tick(hp=[200, 1000])
        self.press_art()
        for _ in range(125):
            self.m.tick()
        self.assertFalse(self.p(0)["rage"])
        self.assertIn("Rage Art MISSED", str(self.m.state["last_event"]))

    def test_rage_art_wins_back_some_of_your_recoverable_health(self):
        self.m.tick(hp=[200, 1000])
        self.p(0)["pool"] = 100
        self.press_art()
        writes = self.hit(1, 100)
        # Rage Art wins back 7% of max (70) and landing any attack wins back 1% more (10)
        self.assertEqual(writes[0], 200 + 70 + 10)
        self.assertEqual(self.p(0)["pool"], 20)

    def test_rage_art_disabled_by_switch(self):
        self.g.MECH.rage_art.enabled = False
        self.m.tick(hp=[200, 1000])
        self.press_art()
        self.assertEqual(self.p(0)["art_left"], 0)

    # Heat start heals
    def test_starting_heat_wins_back_half_the_recoverable_pool(self):
        self.m.tick(hp=[600, 1000])
        self.p(0)["pool"] = 100
        writes = self.m.tick(keys=[True, False])
        self.assertEqual(writes, {0: 650})
        self.assertEqual(self.p(0)["pool"], 50)

    def test_starting_heat_with_no_pool_writes_nothing(self):
        self.assertEqual(self.m.tick(keys=[True, False]), {})


class RoundAndDebug(unittest.TestCase):
    def setUp(self):
        self.lua, self.g = load_engine()
        self.m = Match(self.lua, self.g)
        self.m.timer = 500
        self.m.tick()

    def test_timer_jump_back_resets_round_even_if_round_number_is_unchanged(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.assertTrue(self.g.Engine.heat_active(self.m.state, 0))
        self.m.timer = 3  # new round: timer restarts, RoundNo still reads 1
        self.m.tick()
        self.assertFalse(self.g.Engine.heat_active(self.m.state, 0))

    def test_heat_expiry_is_recorded_as_normal(self):
        self.m.tick(keys=[True, False])
        for _ in range(605):
            self.m.tick(keys=[False, False])
        self.assertIn("P1 Heat ended: timer ran out after 600 running ticks", str(self.m.state["last_event"]))

    def test_heat_cleared_by_reset_is_recorded_with_the_numbers(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.m.timer = 3
        self.m.tick()
        ev = str(self.m.state["last_event"])
        self.assertIn("P1 Heat CLEARED by a reset", ev)
        self.assertIn("timer 503 -> 4", ev)

    def test_heat_countdown_helpers(self):
        self.m.tick(keys=[True, False])
        for _ in range(100):
            self.m.tick(keys=[False, False])
        e = self.g.Engine
        self.assertEqual(e.heat_left(self.m.state, 0), 500)
        self.assertFalse(e.heat_available(self.m.state, 0))

    def test_small_timer_wobble_does_not_reset(self):
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.m.timer -= 5  # a rollback re-simulation steps back a few ticks
        self.m.tick()
        self.assertTrue(self.g.Engine.heat_active(self.m.state, 0))

    def test_debug_force_rage_gives_bonus_at_full_health(self):
        self.g.Engine.debug.force_rage[0] = True
        self.m.tick()
        self.m.hp[1] -= 100
        self.assertEqual(self.m.tick(), {1: 890})

    def test_debug_start_heat_without_key(self):
        self.g.Engine.start_heat(self.m.state, 0)
        self.assertTrue(self.g.Engine.heat_active(self.m.state, 0))
        self.m.tick(guard=[0, 12])
        self.assertEqual(self.m.hp[1], 980)  # chip, as Heat does


class RealMaxHealth(unittest.TestCase):
    def setUp(self):
        self.lua, self.g = load_engine()
        self.m = Match(self.lua, self.g)

    def test_rage_uses_game_max_health_even_if_script_started_mid_round(self):
        self.m.hp = [150, 1000]  # script "starts" with P1 already low: highest-seen would be 150
        self.m.hp_max = [1000, 1000]
        self.m.tick()
        self.m.tick()
        self.m.hp[1] -= 100
        self.assertEqual(self.m.tick(), {1: 890})  # P1 at 15% of the real max is in Rage

    def test_fallback_without_game_max_would_miss_that_rage(self):
        self.m.hp = [150, 1000]  # no hp_max given
        self.m.tick()
        self.m.tick()
        self.m.hp[1] -= 100
        self.assertEqual(self.m.tick(), {})

    def test_chip_uses_game_max_health(self):
        self.m.hp_max = [10000, 10000]
        self.m.hp = [10000, 6000]
        self.m.tick()
        self.m.tick(keys=[True, False])
        self.m.tick(keys=[False, False])
        self.assertEqual(self.m.tick(guard=[0, 12]), {1: 5800})  # 2% of 10000 = 200


class GeneratedFiles(unittest.TestCase):
    def test_both_files_compile(self):
        lua = LuaRuntime()
        for name in ("sf6_tekken_mode.lua", "sf6_tekken_probe.lua"):
            text = (ROOT / "reframework" / "autorun" / name).read_text()
            fn, err = lua.eval("function(src) return load(src) end")(text), None
            self.assertIsNotNone(fn, f"{name} does not compile")

    def test_generated_files_match_sheets(self):
        hooks, mechs = build.load("hooks"), build.load("mechanics")
        text = (ROOT / "reframework" / "autorun" / "sf6_tekken_mode.lua").read_text()
        for r in mechs["rows"]:
            if r["status"] == build.STATUS_BUILT:
                self.assertIn(f'"{r["id"]}"', text)
        for r in hooks["rows"]:
            self.assertIn(f'"{r["id"]}"', text)


class Preflight(unittest.TestCase):
    def sheets(self):
        return copy.deepcopy(build.load("hooks")), copy.deepcopy(build.load("mechanics"))

    def test_real_sheets_are_clean(self):
        errors, _, _ = build.preflight(*self.sheets())
        self.assertEqual(errors, [])

    def test_unfilled_cell_is_caught(self):
        h, m = self.sheets()
        m["rows"][0]["damage_mult"] = ""
        errors, _, _ = build.preflight(h, m)
        self.assertTrue(any("rage.damage_mult: unfilled" in e for e in errors), errors)

    def test_missing_cell_is_caught(self):
        h, m = self.sheets()
        del h["rows"][2]["purpose"]
        errors, _, _ = build.preflight(h, m)
        self.assertTrue(any("hp_now.purpose: unfilled" in e for e in errors), errors)

    def test_broken_reference_is_caught(self):
        h, m = self.sheets()
        m["rows"][1]["uses_hooks"].append("no_such_hook")
        errors, _, _ = build.preflight(h, m)
        self.assertTrue(any("no_such_hook" in e for e in errors), errors)

    def test_write_to_read_only_hook_is_caught(self):
        h, m = self.sheets()
        h["rows"][2]["access"] = "r"
        errors, _, _ = build.preflight(h, m)
        self.assertTrue(any("read-only" in e for e in errors), errors)

    def test_built_row_with_na_value_is_caught(self):
        h, m = self.sheets()
        m["rows"][1]["duration_ticks"] = "n/a"
        errors, _, _ = build.preflight(h, m)
        self.assertTrue(any("heat.duration_ticks" in e for e in errors), errors)

    def test_unused_hook_is_caught(self):
        h, m = self.sheets()
        h["rows"].append(copy.deepcopy(h["rows"][0]))
        h["rows"][-1]["id"] = "orphan"
        errors, _, _ = build.preflight(h, m)
        self.assertTrue(any("orphan" in e and "no mechanics row" in e for e in errors), errors)



FAKE_REFRAMEWORK = r"""
-- A fake REFramework: just enough of re / sdk / imgui / json / reframework for the glue code to run.
fake = { frame_cbs = {}, ui_cbs = {}, saved = {}, keys = {}, ui_text = {}, clicks = {} }
players = {
  [0] = { pl_sw_now = 0, vital_new = 1000, vital_max = 1000, guard_time = 0, damage_time = 0, combo_dm_air = 0 },
  [1] = { pl_sw_now = 0, vital_new = 1000, vital_max = 1000, guard_time = 0, damage_time = 0, combo_dm_air = 0 },
}
battle = {
  Round = { RoundNo = 1 }, Game = { stage_timer = 0 },
  Player = { mcPlayer = players },
}
re = {
  on_frame = function(cb) table.insert(fake.frame_cbs, cb) end,
  on_draw_ui = function(cb) table.insert(fake.ui_cbs, cb) end,
}
sdk = { find_type_definition = function(name)
  if name ~= "gBattle" or fake.no_battle then return nil end
  return { get_field = function(self, f) return { get_data = function() return battle[f] end } end }
end }
reframework = { is_key_down = function(self, vk) return fake.keys[vk] == true end }
imgui = {
  tree_node = function() return true end, tree_pop = function() end,
  text = function(t) table.insert(fake.ui_text, t) end,
  checkbox = function(label, v) return false, v end,
  button = function(label) return fake.press == label end,
  begin_window = function(name) fake.window = name; return true end, end_window = function() end,
  progress_bar = function(frac, size, text) table.insert(fake.bars, { frac = frac, text = text }) end,
}
Vector2f = { new = function(x, y) return { x = x, y = y } end }
fake.bars = {}
json = { dump_file = function(path, tbl) fake.saved[path] = tbl; return true end }
"""


class GlueWithFakeREFramework(unittest.TestCase):
    def boot(self, filename):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(FAKE_REFRAMEWORK)
        lua.execute((ROOT / "reframework" / "autorun" / filename).read_text())
        return lua

    def frame(self, lua):
        lua.execute("for _, cb in ipairs(fake.frame_cbs) do cb() end")

    def test_mod_applies_rage_through_game_objects(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)  # first tick: max health recorded
        lua.execute("players[0].vital_new = 100; battle.Game.stage_timer = 1")
        self.frame(lua)  # P1 enters Rage
        lua.execute("players[1].vital_new = 900; battle.Game.stage_timer = 2")  # P2 takes 100
        self.frame(lua)
        self.assertEqual(lua.eval("players[1].vital_new"), 890)

    def test_mod_starts_heat_from_keyboard(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("fake.keys[112] = true; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.keys[112] = false; battle.Game.stage_timer = 2")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("P1  rage: false  heat: true", joined)

    def test_mod_reads_hitstun_and_shows_it(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("players[1].damage_time = 22; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("Hitstun timer now P1 0 / P2 22, highest seen P1 0 / P2 22", joined)

    def test_mod_uses_vital_max_from_game_objects(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("players[0].vital_max = 10000; players[1].vital_max = 10000; players[0].vital_new = 1500; players[1].vital_new = 10000")
        self.frame(lua)  # started with P1 at 15% of real max
        lua.execute("battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("players[1].vital_new = 9000; battle.Game.stage_timer = 2")
        self.frame(lua)
        self.assertEqual(lua.eval("players[1].vital_new"), 8900)

    def test_mod_survives_missing_vital_max(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("players[0].vital_max = nil; players[1].vital_max = nil")
        self.frame(lua)
        lua.execute("battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertNotIn("Last error", joined)

    def test_ui_shows_block_timer_readouts(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("players[1].guard_time = 14; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("players[1].guard_time = 0; battle.Game.stage_timer = 2")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("Chip hits: 0   block timer now P1 0 / P2 0, highest seen P1 0 / P2 14", joined)

    def test_ui_counts_bonus_writes(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("players[0].vital_new = 100; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("players[1].vital_new = 900; battle.Game.stage_timer = 2")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("Bonus health writes: 1 (last: P2 health 900 -> 890)", joined)

    def test_hud_draws_a_heat_bar_and_survives_a_broken_imgui(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("fake.keys[112] = true; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.keys[112] = false; fake.bars = {}; battle.Game.stage_timer = 2")
        self.frame(lua)
        bars = list(lua.eval("fake.bars").values())
        self.assertEqual(len(bars), 1)
        self.assertIn("P1 HEAT", bars[0]["text"])
        lua.execute("imgui.progress_bar = function() error('no such function') end; battle.Game.stage_timer = 3")
        self.frame(lua)  # must not raise, and must not break the rules
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("On-screen readout error", joined)
        self.assertIn("P1  rage: false  heat: true", joined)

    def test_panel_shows_held_game_buttons_in_bits(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("players[0].pl_sw_now = 5; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("Held buttons (game bits) P1 5 [000000000101]", joined)

    def test_mod_survives_missing_button_field(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("players[0].pl_sw_now = nil")
        self.frame(lua)
        lua.execute("battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertNotIn("Last error", joined)

    def test_art_key_is_read_from_the_keyboard_and_hud_shows_it_armed(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("players[0].vital_new = 100; players[0].vital_max = 1000")
        self.frame(lua)
        lua.execute("battle.Game.stage_timer = 1")
        self.frame(lua)  # P1 in Rage
        lua.execute("fake.keys[114] = true; battle.Game.stage_timer = 2")
        self.frame(lua)
        lua.execute("fake.keys[114] = false; fake.texts = {}; battle.Game.stage_timer = 3")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("Last Heat event: P1 Rage Art armed", joined)

    def test_missing_art_row_does_not_break_the_mod(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.rage_art = nil")  # as if the row were not built
        self.frame(lua)
        lua.execute("battle.Game.stage_timer = 1")
        self.frame(lua)

    def test_no_match_is_handled(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.no_battle = true")
        self.frame(lua)
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        self.assertIn("Status: waiting for a match", list(lua.eval("fake.ui_text").values()))

    def test_read_error_is_reported_not_thrown(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("battle.Player = nil")
        self.frame(lua)  # must not raise
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        joined = " ".join(str(v) for v in lua.eval("fake.ui_text").values())
        self.assertIn("Last error", joined)

    def test_probe_writes_report(self):
        lua = self.boot("sf6_tekken_probe.lua")
        lua.execute("fake.press = 'Run probe now'; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        report = lua.eval('fake.saved["sf6_tekken/probe_report.json"]')
        self.assertIsNotNone(report)
        ids = [r["id"] for r in report.results.values()]
        self.assertEqual(sorted(ids), sorted(r["id"] for r in build.load("hooks")["rows"]))
        by_id = {r["id"]: r for r in report.results.values()}
        self.assertTrue(by_id["hp_now"]["ok"])
        self.assertEqual(len(by_id["hp_now"]["reads"]), 2)
        self.assertTrue(by_id["key_state"]["ok"])

    def run_write_test(self, lua, frames=125):
        lua.execute("fake.press = 'Run write test (takes 1 health point from P1)'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.press = nil")
        for _ in range(frames):
            self.frame(lua)
        return lua.eval('fake.saved["sf6_tekken/write_test_report.json"]')

    def test_write_test_reports_a_kept_write(self):
        lua = self.boot("sf6_tekken_probe.lua")
        report = self.run_write_test(lua)
        self.assertIsNotNone(report)
        res = list(report.results.values())
        self.assertEqual([r["id"] for r in res], ["hp_now"])  # only the writable hook
        r = res[0]
        self.assertTrue(r["write_ok"])
        self.assertEqual((r["before"], r["after_write"], r["after_1_frame"], r["after_30_frames"], r["after_120_frames"]),
                         (1000, 999, 999, 999, 999))

    def test_write_test_reports_a_reverted_write(self):
        lua = self.boot("sf6_tekken_probe.lua")
        # the game puts the old value back on the next frame
        lua.execute("table.insert(fake.frame_cbs, 1, function() players[0].vital_new = 1000 end)")
        report = self.run_write_test(lua)
        r = list(report.results.values())[0]
        self.assertEqual(r["after_write"], 999)
        self.assertEqual(r["after_1_frame"], 1000)
        self.assertEqual(r["after_120_frames"], 1000)

    def test_write_test_reports_a_refused_write(self):
        lua = self.boot("sf6_tekken_probe.lua")
        lua.execute("""
            local real = players[0]
            players[0] = setmetatable({}, { __index = real, __newindex = function() error("read-only field") end })
        """)
        report = self.run_write_test(lua)
        r = list(report.results.values())[0]
        self.assertFalse(r["write_ok"])
        self.assertIn("read-only", r["error"])

    def test_probe_flags_a_wrong_field_name(self):
        lua = self.boot("sf6_tekken_probe.lua")
        lua.execute("players[0].vital_new = nil; players[1].vital_new = nil")
        lua.execute("fake.press = 'Run probe now'; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        report = lua.eval('fake.saved["sf6_tekken/probe_report.json"]')
        by_id = {r["id"]: r for r in report.results.values()}
        self.assertFalse(by_id["hp_now"]["ok"])
        self.assertTrue(by_id["guard_time"]["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
