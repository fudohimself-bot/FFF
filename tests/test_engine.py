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

    def test_gauge_model_reports_heat_state(self):
        e = self.g.Engine
        m0 = e.gauge_model(self.m.state, 0)
        self.assertFalse(m0.active)
        self.assertTrue(m0.available)
        self.heat_on(0)
        m = e.gauge_model(self.m.state, 0)
        self.assertTrue(m.active)
        self.assertAlmostEqual(m.fraction, 599 / 600, places=3)
        self.assertAlmostEqual(m.seconds, 599 / 60.0, places=2)
        self.assertFalse(m.available)
        self.assertFalse(m.paused)

    def test_gauge_model_marks_the_timer_paused_during_opponent_hitstun(self):
        e = self.g.Engine
        self.heat_on(0)
        self.m.tick(hitstun=[0, 15])
        self.assertTrue(e.gauge_model(self.m.state, 0).paused)
        self.m.tick(hitstun=[0, 0])
        self.assertFalse(e.gauge_model(self.m.state, 0).paused)

    def test_gauge_model_recoverable_fraction(self):
        e = self.g.Engine
        self.heat_on(0)
        self.m.tick(guard=[0, 12])  # chip 20 of 1000
        self.assertAlmostEqual(e.gauge_model(self.m.state, 1).pool_fraction, 0.02, places=3)

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
  [0] = { hit_stop = 0, sleep_time = 0, damage_sleep = 0, pl_sw_now = 0, vital_new = 1000, vital_max = 1000, guard_time = 0, damage_time = 0, combo_dm_air = 0 },
  [1] = { hit_stop = 0, sleep_time = 0, damage_sleep = 0, pl_sw_now = 0, vital_new = 1000, vital_max = 1000, guard_time = 0, damage_time = 0, combo_dm_air = 0 },
}
battle = {
  Round = { RoundNo = 1 }, Game = { stage_timer = 0 },
  Player = { mcPlayer = players },
}
re = {
  on_frame = function(cb) table.insert(fake.frame_cbs, cb) end,
  on_draw_ui = function(cb) table.insert(fake.ui_cbs, cb) end,
  on_script_reset = function(cb) fake.reset_cb = cb end,
}
fake.speeds = {}
fake.scale_calls = {}
fake.fps_calls = {}
fake.fps = 60
fake.scene = { call = function(self, name, v)
  if fake.speed_error then error("call refused") end
  assert(name == "set_TimeScale")
  table.insert(fake.scale_calls, v)
end }
sdk_get_native = function(name)
  if name == "via.Application" or name == "via.SceneManager" then return { name = name } end
  return nil
end
sdk = {
  find_type_definition = function(name)
    if name == "via.Application" or name == "via.SceneManager" then return { name = name } end
    if name ~= "gBattle" or fake.no_battle then return nil end
    return { get_field = function(self, f) return { get_data = function() return battle[f] end } end }
  end,
  get_native_singleton = function(name) return sdk_get_native(name) end,
  call_native_func = function(obj, t, method, value)
    if fake.speed_error then error("call refused") end
    if method == "get_CurrentScene" then return fake.scene end
    if method == "get_MaxFps" then return fake.fps end
    if method == "set_MaxFps" then table.insert(fake.fps_calls, value); return end
    assert(method == "set_GlobalSpeed")
    table.insert(fake.speeds, value)
  end,
}
reframework = { is_key_down = function(self, vk) return fake.keys[vk] == true end }
imgui = {
  tree_node = function() return true end, tree_pop = function() end,
  text = function(t) table.insert(fake.ui_text, t) end,
  checkbox = function(label, v)
    if fake.toggle == label then return true, not v end
    return false, v
  end,
  slider_int = function(label, v, lo, hi) if fake.slide and fake.slide[1] == label then return true, fake.slide[2] end return false, v end,
  slider_float = function(label, v, lo, hi) if fake.slide and fake.slide[1] == label then return true, fake.slide[2] end return false, v end,
  button = function(label) return fake.press == label end,
  get_display_size = function() return { x = 1920, y = 1080 } end,
  begin_window = function(name) fake.window = name; return true end, end_window = function() end,
  progress_bar = function(frac, size, text) table.insert(fake.bars, { frac = frac, text = text }) end,
}
Vector2f = { new = function(x, y) return { x = x, y = y } end }
fake.draws = {}
local function rec(kind) return function(...)
  if fake.draw_error then error("draw refused") end
  table.insert(fake.draws, { kind, ... })
end end
draw = { filled_rect = rec("fill"), outline_rect = rec("outline"), text = rec("text") }
fake.bars = {}
json = {
  dump_file = function(path, tbl) if fake.save_error then error("disk full") end fake.saved[path] = tbl; return true end,
  load_file = function(path) return fake.preload and fake.preload[path] or nil end,
}
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

    def _ui(self, lua):
        lua.execute("fake.ui_text = {}; for _, cb in ipairs(fake.ui_cbs) do cb() end")
        return " ".join(str(v) for v in lua.eval("fake.ui_text").values())

    def _arm_smash_and_land(self, lua):
        self.frame(lua)
        lua.execute("fake.keys[112] = true; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.keys[112] = false; battle.Game.stage_timer = 2")
        self.frame(lua)
        lua.execute("fake.keys[112] = true; battle.Game.stage_timer = 3")
        self.frame(lua)
        lua.execute("fake.keys[112] = false; battle.Game.stage_timer = 4")
        self.frame(lua)
        lua.execute("players[1].vital_new = 900; battle.Game.stage_timer = 5")
        self.frame(lua)

    def test_slowmo_is_off_by_default_so_a_landing_does_not_touch_game_speed(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self._arm_smash_and_land(lua)
        self.assertIn("Heat Smash LANDED", self._ui(lua))
        self.assertEqual(len(list(lua.eval("fake.speeds").values())), 0)

    def test_slowmo_slows_then_restores_when_enabled(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'global_speed'")
        self._arm_smash_and_land(lua)
        speeds = list(lua.eval("fake.speeds").values())
        self.assertEqual(speeds, [0.5])
        for n in range(6, 6 + 50):
            lua.execute(f"battle.Game.stage_timer = {n}")
            self.frame(lua)
        speeds = list(lua.eval("fake.speeds").values())
        self.assertEqual(speeds, [0.5, 1.0])  # speed handed back after the effect

    def test_slowmo_restores_if_switched_off_midway(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'global_speed'")
        self._arm_smash_and_land(lua)
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = false; battle.Game.stage_timer = 9")
        self.frame(lua)
        self.assertEqual(list(lua.eval("fake.speeds").values()), [0.5, 1.0])

    def test_script_reset_restores_normal_speed(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.reset_cb()")
        self.assertEqual(list(lua.eval("fake.speeds").values()), [1.0])

    def test_refused_slowmo_turns_itself_off_and_says_why(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'global_speed'; fake.speed_error = true")
        self._arm_smash_and_land(lua)  # must not raise
        self.assertFalse(lua.eval("SF6_TEKKEN.MECH.slowmo_fx.enabled"))
        self.assertIn("Slow-motion error: ", self._ui(lua))

    def test_hit_freeze_candidates_show_live_and_missing_fields_say_n_a(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("players[0].hit_stop = nil; players[1].hit_stop = nil")
        self.frame(lua)
        lua.execute("players[1].sleep_time = 7; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("players[1].sleep_time = 0; battle.Game.stage_timer = 2")
        self.frame(lua)
        ui = self._ui(lua)
        self.assertIn("Hit-freeze candidate sleep_time: now P1 0 / P2 0, highest seen P1 0 / P2 7", ui)
        self.assertIn("Hit-freeze candidate hit_stop: now P1 n/a / P2 n/a", ui)  # the fake has no such field

    def _run_effect(self, lua, extra_frames=50):
        self._arm_smash_and_land(lua)
        for n in range(6, 6 + extra_frames):
            lua.execute(f"battle.Game.stage_timer = {n}")
            self.frame(lua)

    def test_scene_time_scale_method_slows_then_restores(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'scene_time_scale'")
        self._run_effect(lua)
        self.assertEqual(list(lua.eval("fake.scale_calls").values()), [0.5, 1.0])
        # restoring also sends "normal speed" to the other methods, so nothing can be left slowed
        self.assertEqual(list(lua.eval("fake.speeds").values()), [1.0])

    def test_max_fps_method_lowers_the_cap_then_restores_the_original(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'max_fps'")
        self._run_effect(lua)
        calls = list(lua.eval("fake.fps_calls").values())
        self.assertAlmostEqual(calls[0], 30.0)  # 50% of 60
        self.assertEqual(calls[1], 60)  # the original cap, not a guess

    def test_max_fps_with_no_cap_uses_sixty_as_the_base_and_restores_no_cap(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.fps = 0; SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'max_fps'")
        self._run_effect(lua)
        calls = list(lua.eval("fake.fps_calls").values())
        self.assertAlmostEqual(calls[0], 30.0)
        self.assertEqual(calls[1], 0)

    def test_max_fps_that_cannot_be_read_refuses_instead_of_guessing(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.fps = nil; SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'max_fps'")
        self._arm_smash_and_land(lua)
        self.assertEqual(len(list(lua.eval("fake.fps_calls").values())), 0)
        self.assertIn("Slow-motion error: max_fps: ", self._ui(lua))

    def test_script_reset_puts_the_frame_cap_back(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.slowmo_fx.enabled = true; SF6_TEKKEN.MECH.slowmo_fx.fx_method = 'max_fps'")
        self._arm_smash_and_land(lua)
        lua.execute("fake.reset_cb()")
        self.assertEqual(list(lua.eval("fake.fps_calls").values())[-1], 60)

    def test_panel_buttons_switch_the_slowmo_method(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.assertIn("Slow-motion method: max_fps", self._ui(lua))
        lua.execute("fake.press = 'use method: scene_time_scale'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.press = nil")
        self.assertIn("Slow-motion method: scene_time_scale", self._ui(lua))

    def test_hit_freeze_boost_is_on_by_default(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("players[1].vital_new = 900; battle.Game.stage_timer = 1")
        self.frame(lua)
        self.assertEqual((lua.eval("players[0].hit_stop"), lua.eval("players[1].hit_stop")), (3, 3))

    def test_hit_freeze_boost_can_be_switched_off(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.hitstop_boost.enabled = false")
        self.frame(lua)
        lua.execute("players[1].vital_new = 900; battle.Game.stage_timer = 1")
        self.frame(lua)
        self.assertEqual((lua.eval("players[0].hit_stop"), lua.eval("players[1].hit_stop")), (0, 0))

    def test_hit_freeze_boost_adds_frames_to_both_fighters_on_a_hit(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.hitstop_boost.enabled = true")
        self.frame(lua)
        lua.execute("players[0].hit_stop = 4; players[1].hit_stop = 4; players[1].vital_new = 900; battle.Game.stage_timer = 1")
        self.frame(lua)
        self.assertEqual((lua.eval("players[0].hit_stop"), lua.eval("players[1].hit_stop")), (7, 7))  # +3
        self.assertIn("Hit freeze boosts applied: 1", self._ui(lua))

    def test_big_boost_on_a_smash(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.hitstop_boost.enabled = true")
        self._arm_smash_and_land(lua)
        self.assertEqual(lua.eval("players[1].hit_stop"), 10)

    def test_refused_hit_freeze_write_turns_the_boost_off_and_says_so(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.hitstop_boost.enabled = true")
        lua.execute("""
            local real = players[1]
            players[1] = setmetatable({}, { __index = real, __newindex = function(t, k, v)
                if k == "hit_stop" then error("read-only field") end rawset(real, k, v) end })
        """)
        self.frame(lua)
        lua.execute("players[1].vital_new = 900; battle.Game.stage_timer = 1")
        self.frame(lua)  # must not raise
        self.assertFalse(lua.eval("SF6_TEKKEN.MECH.hitstop_boost.enabled"))
        self.assertIn("Hit freeze error: ", self._ui(lua))

    PATH = "sf6_tekken/settings.json"

    def _saved(self, lua):
        return lua.eval(f'fake.saved["{self.PATH}"]')

    def test_settings_are_loaded_at_start(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(FAKE_REFRAMEWORK)
        lua.execute('fake.preload = { ["sf6_tekken/settings.json"] = { hitstop_boost = { enabled = false, boost_frames = 6 }, slowmo_fx = { enabled = true, fx_method = "scene_time_scale", fx_speed_scale = 0.7, fx_frames = 40 }, rage = { enabled = false } } }')
        lua.execute((ROOT / "reframework" / "autorun" / "sf6_tekken_mode.lua").read_text())
        self.assertEqual(lua.eval("SF6_TEKKEN.MECH.hitstop_boost.boost_frames"), 6)
        self.assertFalse(lua.eval("SF6_TEKKEN.MECH.hitstop_boost.enabled"))
        self.assertFalse(lua.eval("SF6_TEKKEN.MECH.rage.enabled"))
        self.assertEqual(lua.eval("SF6_TEKKEN.MECH.slowmo_fx.fx_method"), "scene_time_scale")
        self.assertAlmostEqual(lua.eval("SF6_TEKKEN.MECH.slowmo_fx.fx_speed_scale"), 0.7)
        self.assertIn("Settings: loaded 7 saved settings", self._ui(lua))

    def test_bad_saved_values_are_ignored_or_clamped(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(FAKE_REFRAMEWORK)
        lua.execute('''fake.preload = { ["sf6_tekken/settings.json"] = {
            hitstop_boost = { enabled = "yes", boost_frames = 9999, big_boost_frames = -5 },
            slowmo_fx = { fx_method = "rm -rf", fx_speed_scale = 0, fx_frames = "a lot" },
            heat = 5, unknown_mod = { enabled = true } } }''')
        lua.execute((ROOT / "reframework" / "autorun" / "sf6_tekken_mode.lua").read_text())
        m = lua.eval("SF6_TEKKEN.MECH")
        self.assertTrue(m.hitstop_boost.enabled)  # "yes" is not a boolean: default kept
        self.assertEqual(m.hitstop_boost.boost_frames, 20)  # clamped
        self.assertEqual(m.hitstop_boost.big_boost_frames, 0)  # clamped
        self.assertEqual(m.slowmo_fx.fx_method, "max_fps")  # not a known method: default kept
        self.assertAlmostEqual(m.slowmo_fx.fx_speed_scale, 0.1)  # clamped
        self.assertEqual(m.slowmo_fx.fx_frames, 30)  # a string is not a number: default kept
        self.assertTrue(m.heat.enabled)

    def test_a_non_table_settings_file_is_ignored(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(FAKE_REFRAMEWORK)
        lua.execute('fake.preload = { ["sf6_tekken/settings.json"] = "garbage" }')
        lua.execute((ROOT / "reframework" / "autorun" / "sf6_tekken_mode.lua").read_text())
        self.assertTrue(lua.eval("SF6_TEKKEN.MECH.rage.enabled"))

    def test_changing_a_checkbox_saves_settings(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.assertIsNone(self._saved(lua))
        lua.execute("fake.toggle = 'rage enabled'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.toggle = nil")
        self.frame(lua)  # the save happens on the next frame
        saved = self._saved(lua)
        self.assertFalse(saved.rage.enabled)
        self.assertTrue(saved.hitstop_boost.enabled)
        self.assertEqual(saved.hitstop_boost.boost_frames, 3)

    def test_moving_a_slider_saves_the_new_value(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.slide = { 'hit freeze boost (frames)', 6 }; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.slide = nil")
        self.frame(lua)
        self.assertEqual(self._saved(lua).hitstop_boost.boost_frames, 6)

    def test_nothing_is_written_until_something_changes(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("battle.Game.stage_timer = 1")
        self.frame(lua)
        self.assertIsNone(self._saved(lua))

    def test_a_failing_save_is_reported_and_does_not_break_the_mod(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.save_error = true; fake.toggle = 'rage enabled'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.toggle = nil")
        self.frame(lua)  # must not raise
        self.assertIn("Settings: save failed", self._ui(lua))

    def test_reset_button_restores_defaults_and_saves_them(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.hitstop_boost.boost_frames = 9; SF6_TEKKEN.MECH.rage.enabled = false")
        lua.execute("fake.press = 'reset settings to defaults'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.press = nil")
        self.frame(lua)
        self.assertEqual(lua.eval("SF6_TEKKEN.MECH.hitstop_boost.boost_frames"), 3)
        self.assertTrue(lua.eval("SF6_TEKKEN.MECH.rage.enabled"))
        self.assertEqual(self._saved(lua).hitstop_boost.boost_frames, 3)

    # ---- Heat gauge drawn on the screen
    def _draws(self, lua):
        return [list(d.values()) for d in lua.eval("fake.draws").values()]

    def _start_heat_p1(self, lua):
        self.frame(lua)
        lua.execute("fake.keys[112] = true; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.keys[112] = false; battle.Game.stage_timer = 2; fake.draws = {}")
        self.frame(lua)

    def test_gauge_for_heat_is_orange_under_p1_and_a_dim_label_under_p2(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self._start_heat_p1(lua)
        d = self._draws(lua)
        fills = [x for x in d if x[0] == "fill"]
        g = lua.eval("SF6_TEKKEN.MECH.heat_gauge")
        edge, top, width = 1920 * g.gauge_edge_pct / 100, 1080 * g.gauge_y_pct / 100, 1920 * g.gauge_w_pct / 100
        self.assertAlmostEqual(fills[0][1], edge - 2)  # P1's background starts at the left margin
        self.assertAlmostEqual(fills[0][2], top - 2)
        bar = [f for f in fills if f[5] == 0xFF1E9BFF][0]
        self.assertAlmostEqual(bar[1], edge)  # starts at the left edge for P1
        self.assertAlmostEqual(bar[3], width * (599 / 600), places=1)  # nearly full: Heat just started
        texts = [x[1] for x in d if x[0] == "text"]
        self.assertTrue(any(t.startswith("P1 HEAT  ") for t in texts), texts)
        self.assertIn("P2 HEAT", texts)  # P2 still has Heat available

    def test_p2_gauge_sits_at_the_right_edge(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("fake.keys[113] = true; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("fake.keys[113] = false; battle.Game.stage_timer = 2; fake.draws = {}")
        self.frame(lua)
        fills = [x for x in self._draws(lua) if x[0] == "fill"]
        g = lua.eval("SF6_TEKKEN.MECH.heat_gauge")
        edge = 1920 * g.gauge_edge_pct / 100
        bar = [f for f in fills if f[5] == 0xFF1E9BFF][0]
        full_right = 1920 - edge
        self.assertAlmostEqual(bar[1] + bar[3], full_right, places=0)  # drains toward its own (right) edge

    def test_gauge_shrinks_as_heat_runs_down(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self._start_heat_p1(lua)
        for n in range(3, 303):
            lua.execute(f"battle.Game.stage_timer = {n}; fake.draws = {{}}")
            self.frame(lua)
        bar = [x for x in self._draws(lua) if x[0] == "fill" and x[5] == 0xFF1E9BFF][0]
        g = lua.eval("SF6_TEKKEN.MECH.heat_gauge")
        self.assertAlmostEqual(bar[3], 1920 * g.gauge_w_pct / 100 * 0.5, delta=3)

    def test_gauge_turns_pale_blue_while_the_timer_is_paused(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self._start_heat_p1(lua)
        lua.execute("players[1].damage_time = 20; battle.Game.stage_timer = 3; fake.draws = {}")
        self.frame(lua)
        colors = [x[5] for x in self._draws(lua) if x[0] == "fill"]
        self.assertIn(0xFFFFDCAA, colors)
        self.assertNotIn(0xFF1E9BFF, colors)

    def test_gauge_flashes_red_when_nearly_out(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.heat.duration_ticks = 40")
        self._start_heat_p1(lua)
        seen = set()
        for n in range(3, 3 + 36):
            lua.execute(f"battle.Game.stage_timer = {n}; fake.draws = {{}}")
            self.frame(lua)
            seen |= {x[5] for x in self._draws(lua) if x[0] == "fill"}
        self.assertIn(0xFF1E1EE6, seen)  # red phase
        self.assertIn(0xFF1E9BFF, seen)  # orange phase

    def test_no_label_for_heat_that_has_been_used_up(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.heat.duration_ticks = 5")
        self._start_heat_p1(lua)
        for n in range(3, 20):
            lua.execute(f"battle.Game.stage_timer = {n}; fake.draws = {{}}")
            self.frame(lua)
        texts = [x[1] for x in self._draws(lua) if x[0] == "text"]
        self.assertNotIn("P1 HEAT", texts)
        self.assertNotIn("P1 HEAT  0.0", texts)
        self.assertIn("P2 HEAT", texts)

    def test_gauge_shows_a_thin_recoverable_bar_after_chip(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self._start_heat_p1(lua)
        lua.execute("players[1].guard_time = 12; battle.Game.stage_timer = 3")  # P2 blocks: chip -> recoverable
        self.frame(lua)
        lua.execute("players[1].guard_time = 0; battle.Game.stage_timer = 4; fake.draws = {}")
        self.frame(lua)
        thin = [x for x in self._draws(lua) if x[0] == "fill" and x[5] == 0xD0F0F0F0]
        self.assertTrue(thin, "recoverable bar missing")
        self.assertEqual(thin[0][4], 4)  # thin: 4 px

    def test_gauge_shows_a_rage_label_in_red(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self.frame(lua)
        lua.execute("players[1].vital_new = 100; battle.Game.stage_timer = 1")
        self.frame(lua)
        lua.execute("battle.Game.stage_timer = 2; fake.draws = {}")
        self.frame(lua)
        texts = [(x[1], x[4]) for x in self._draws(lua) if x[0] == "text"]
        self.assertIn(("P2 RAGE", 0xFF3C3CFF), texts)

    def test_gauge_error_stays_until_it_is_switched_back_on(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.draw_error = true")
        self._start_heat_p1(lua)
        lua.execute("battle.Game.stage_timer = 3"); self.frame(lua)
        lua.execute("battle.Game.stage_timer = 4"); self.frame(lua)
        self.assertIn("Heat gauge error: ", self._ui(lua))  # still there two frames later
        lua.execute("fake.draw_error = nil; fake.toggle = 'heat_gauge enabled'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.toggle = nil")
        self.assertNotIn("Heat gauge error: ", self._ui(lua))
        self.assertTrue(lua.eval("SF6_TEKKEN.MECH.heat_gauge.enabled"))

    def test_gauge_labels_for_armed_stand_in_moves(self):
        lua = self.boot("sf6_tekken_mode.lua")
        self._arm_smash_and_land(lua)  # lands, so nothing armed afterwards
        lua.execute("SF6_TEKKEN.MECH.hitstop_boost.enabled = false")
        self.frame(lua)
        lua2 = self.boot("sf6_tekken_mode.lua")
        self.frame(lua2)
        lua2.execute("fake.keys[112] = true; battle.Game.stage_timer = 1")
        self.frame(lua2)
        lua2.execute("fake.keys[112] = false; battle.Game.stage_timer = 2")
        self.frame(lua2)
        lua2.execute("fake.keys[112] = true; battle.Game.stage_timer = 3")
        self.frame(lua2)
        lua2.execute("fake.keys[112] = false; battle.Game.stage_timer = 4; fake.draws = {}")
        self.frame(lua2)
        texts = [x[1] for x in self._draws(lua2) if x[0] == "text"]
        self.assertIn("P1 HEAT SMASH ARMED", texts)

    def test_gauge_can_be_switched_off(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("SF6_TEKKEN.MECH.heat_gauge.enabled = false; fake.draws = {}")
        self._start_heat_p1(lua)
        self.assertEqual(self._draws(lua), [])

    def test_gauge_failure_turns_it_off_and_leaves_the_rules_alone(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.draw_error = true")
        self._start_heat_p1(lua)  # must not raise
        self.assertFalse(lua.eval("SF6_TEKKEN.MECH.heat_gauge.enabled"))
        ui = self._ui(lua)
        self.assertIn("Heat gauge error: ", ui)
        self.assertIn("P1  rage: false  heat: true", ui)  # Heat itself still works

    def test_gauge_layout_sliders_change_and_save_the_layout(self):
        lua = self.boot("sf6_tekken_mode.lua")
        lua.execute("fake.slide = { 'gauge thickness (pixels)', 24 }; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.slide = nil")
        self.frame(lua)
        self.assertEqual(lua.eval("SF6_TEKKEN.MECH.heat_gauge.gauge_h_px"), 24)
        self.assertEqual(self._saved(lua).heat_gauge.gauge_h_px, 24)
        lua.execute("fake.slide = { 'gauge height on screen (%)', 25.5 }; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.slide = nil")
        self.assertAlmostEqual(lua.eval("SF6_TEKKEN.MECH.heat_gauge.gauge_y_pct"), 25.5)

    def test_saved_gauge_layout_is_loaded_and_clamped(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(FAKE_REFRAMEWORK)
        lua.execute('fake.preload = { ["sf6_tekken/settings.json"] = { heat_gauge = { gauge_w_pct = 999, gauge_y_pct = 12.5, gauge_h_px = -3 } } }')
        lua.execute((ROOT / "reframework" / "autorun" / "sf6_tekken_mode.lua").read_text())
        g = lua.eval("SF6_TEKKEN.MECH.heat_gauge")
        self.assertEqual(g.gauge_w_pct, 45)
        self.assertAlmostEqual(g.gauge_y_pct, 12.5)
        self.assertEqual(g.gauge_h_px, 4)

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
        self.assertTrue(by_id["global_speed"]["ok"])
        self.assertTrue(by_id["scene_time_scale"]["ok"])
        self.assertTrue(by_id["max_fps"]["ok"])
        self.assertTrue(by_id["draw_screen"]["ok"])
        self.assertTrue(by_id["hit_stop"]["ok"])
        self.assertTrue(by_id["sleep_time"]["ok"])

    def run_write_test(self, lua, frames=125):
        lua.execute("fake.press = 'Run write test (adds 1 to a P1 value)'; for _, cb in ipairs(fake.ui_cbs) do cb() end; fake.press = nil")
        for _ in range(frames):
            self.frame(lua)
        return lua.eval('fake.saved["sf6_tekken/write_test_report.json"]')

    def test_write_test_reports_a_kept_write(self):
        lua = self.boot("sf6_tekken_probe.lua")
        report = self.run_write_test(lua)
        self.assertIsNotNone(report)
        res = {r["id"]: r for r in report.results.values()}
        self.assertEqual(sorted(res), ["hit_stop", "hp_now"])  # only the writable hooks
        r = res["hp_now"]
        self.assertTrue(r["write_ok"])
        self.assertEqual((r["before"], r["after_write"], r["after_1_frame"], r["after_30_frames"], r["after_120_frames"]),
                         (1000, 1001, 1001, 1001, 1001))  # +1, never negative

    def test_write_test_reports_a_reverted_write(self):
        lua = self.boot("sf6_tekken_probe.lua")
        # the game puts the old value back on the next frame
        lua.execute("table.insert(fake.frame_cbs, 1, function() players[0].vital_new = 1000 end)")
        report = self.run_write_test(lua)
        r = {r["id"]: r for r in report.results.values()}["hp_now"]
        self.assertEqual(r["after_write"], 1001)
        self.assertEqual(r["after_1_frame"], 1000)
        self.assertEqual(r["after_120_frames"], 1000)

    def test_write_test_reports_a_refused_write(self):
        lua = self.boot("sf6_tekken_probe.lua")
        lua.execute("""
            local real = players[0]
            players[0] = setmetatable({}, { __index = real, __newindex = function() error("read-only field") end })
        """)
        report = self.run_write_test(lua)
        r = {r["id"]: r for r in report.results.values()}["hp_now"]
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
