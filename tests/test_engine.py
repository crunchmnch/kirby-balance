"""The engine-vs-oracle contract: the event simulation must converge to
the closed-form expectation (ADR 012: the closed form is the independent
test oracle for the engine's crit arithmetic), and a run must be exactly
reproducible from its seed.
"""

import os
import unittest

from kb import closedform, gametables
from kb.engine import auras, sim, timeline

EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "export", "gametables.json")

PROFILE = {
    "class_id": 1,
    "level": 70,
    "provenance": "test fixture, synthetic",
    "attack_power": 1900,
    "agility": 180,
    "crit_rating": 250,
    "weapon_min": 274,
    "weapon_max": 412,
    "weapon_speed_ms": 3300,
}

HOUR_MS = 3600 * 1000


class TimelineTests(unittest.TestCase):
    def test_deterministic_order_at_equal_time(self):
        tl = timeline.Timeline()
        fired = []
        tl.schedule(5, lambda: fired.append("a"))
        tl.schedule(5, lambda: fired.append("b"))
        tl.schedule(3, lambda: fired.append("c"))
        tl.run_until(10)
        self.assertEqual(fired, ["c", "a", "b"])

    def test_refuses_past_events(self):
        tl = timeline.Timeline()
        tl.schedule(5, lambda: tl.schedule(2, lambda: None))
        with self.assertRaises(timeline.TimelineError):
            tl.run_until(10)

    def test_end_is_exclusive(self):
        tl = timeline.Timeline()
        fired = []
        tl.schedule(10, lambda: fired.append("x"))
        tl.run_until(10)
        self.assertEqual(fired, [])


class EngineOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gt = gametables.GameTables.from_export(EXPORT_PATH)

    def test_sim_converges_to_closed_form_no_auras(self):
        result = sim.run(PROFILE, self.gt, [], 100 * HOUR_MS, seed=1)
        crit = self.gt.melee_crit_percent(1, 70, 180, 250)
        expected = closedform.white_dps(274, 412, 1900, 3300, crit)
        self.assertLess(abs(result.dps / expected - 1.0), 0.005)

    def test_sim_converges_with_aura163_windows(self):
        # A +15 crit-damage aura up 15 s of every 120 s: the sim must land
        # on the uptime-weighted closed form. This exercises Path B crit
        # multiplication AND the aura window machinery together.
        aura = auras.Aura("Test Crit Damage", [
            {"kind": "crit_damage_bonus_pct", "amount": 15.0}])
        sched = sim.AuraSchedule(aura, 15000, 120000)
        result = sim.run(PROFILE, self.gt, [sched], 100 * HOUR_MS, seed=2)
        crit = self.gt.melee_crit_percent(1, 70, 180, 250)
        up = closedform.white_dps(274, 412, 1900, 3300, crit, [15.0])
        down = closedform.white_dps(274, 412, 1900, 3300, crit)
        expected = closedform.uptime_weighted(up, down, 15.0 / 120.0)
        self.assertLess(abs(result.dps / expected - 1.0), 0.005)

    def test_same_seed_same_result(self):
        a = sim.run(PROFILE, self.gt, [], HOUR_MS, seed=42)
        b = sim.run(PROFILE, self.gt, [], HOUR_MS, seed=42)
        self.assertEqual(a.total_damage, b.total_damage)
        self.assertEqual(a.crits, b.crits)

    def test_different_seed_different_result(self):
        a = sim.run(PROFILE, self.gt, [], HOUR_MS, seed=42)
        b = sim.run(PROFILE, self.gt, [], HOUR_MS, seed=43)
        self.assertNotEqual(a.total_damage, b.total_damage)

    def test_observed_crit_tracks_input(self):
        result = sim.run(PROFILE, self.gt, [], 100 * HOUR_MS, seed=3)
        crit = self.gt.melee_crit_percent(1, 70, 180, 250)
        self.assertLess(abs(result.observed_crit_pct - crit), 0.5)

    def test_profile_without_provenance_is_refused(self):
        from kb.engine import actor
        bad = dict(PROFILE)
        bad["provenance"] = "  "
        with self.assertRaises(actor.ActorError):
            sim.run(bad, self.gt, [], HOUR_MS, seed=1)
        del bad["provenance"]
        with self.assertRaises(actor.ActorError):
            sim.run(bad, self.gt, [], HOUR_MS, seed=1)

    def test_overlapping_reapplication_is_refused(self):
        aura = auras.Aura("Too Long", [
            {"kind": "attack_power", "amount": 100}])
        with self.assertRaises(sim.SimError):
            sim.AuraSchedule(aura, 30000, 20000)
