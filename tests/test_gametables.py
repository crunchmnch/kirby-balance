"""Pins the P2 assertion forever: the parsed game tables reproduce known
3.3.5 reference values. Asserted S243 against the Windows dev's extracted DBC,
a tree deleted in S288; the current source is the Linux dev over the WSL share.
If these fail, either the export was regenerated from different data (check
the stamp) or the reader's indexing broke.
"""

import os
import unittest

from kb import gametables

EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "export", "gametables.json")

WARRIOR, PALADIN, HUNTER, ROGUE = 1, 2, 3, 4
DRUID = 11


class KnownValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gt = gametables.GameTables.from_export(EXPORT_PATH)

    def test_base_melee_crit(self):
        self.assertAlmostEqual(
            self.gt.melee_crit_base_percent(WARRIOR), 3.1891, places=3)
        self.assertAlmostEqual(
            self.gt.melee_crit_base_percent(PALADIN), 3.2685, places=3)
        self.assertAlmostEqual(
            self.gt.melee_crit_base_percent(HUNTER), -1.5320, places=3)
        self.assertAlmostEqual(
            self.gt.melee_crit_base_percent(ROGUE), -0.2950, places=3)
        self.assertAlmostEqual(
            self.gt.melee_crit_base_percent(DRUID), 7.4755, places=3)

    def test_agility_per_percent_at_80(self):
        # canonical WotLK values: warrior 62.5, rogue and hunter 83.33
        agi_per_pct = 1.0 / self.gt.melee_crit_per_agi_percent(WARRIOR, 80)
        self.assertAlmostEqual(agi_per_pct, 62.50, places=1)
        agi_per_pct = 1.0 / self.gt.melee_crit_per_agi_percent(ROGUE, 80)
        self.assertAlmostEqual(agi_per_pct, 83.33, places=1)

    def test_crit_rating_conversion(self):
        self.assertAlmostEqual(
            self.gt.rating_per_percent(gametables.CR_CRIT_MELEE, 60),
            14.0, places=3)
        self.assertAlmostEqual(
            self.gt.rating_per_percent(gametables.CR_CRIT_MELEE, 80),
            45.906, places=2)
        self.assertAlmostEqual(
            self.gt.rating_per_percent(gametables.CR_HIT_SPELL, 80),
            26.232, places=2)

    def test_yardstick_instability_across_levels(self):
        # The design 025 section 7.1 fact the tool exists to expose: the
        # agi-to-crit conversion moves sharply between the 60 and 70 gates.
        w60 = 1.0 / self.gt.melee_crit_per_agi_percent(WARRIOR, 60)
        w70 = 1.0 / self.gt.melee_crit_per_agi_percent(WARRIOR, 70)
        self.assertLess(w60, w70)

    def test_fails_closed(self):
        with self.assertRaises(gametables.GameTableError):
            self.gt.melee_crit_base_percent(10)   # the class-id gap
        with self.assertRaises(gametables.GameTableError):
            self.gt.melee_crit_per_agi_percent(WARRIOR, 0)
        with self.assertRaises(gametables.GameTableError):
            self.gt.melee_crit_per_agi_percent(WARRIOR, 101)
        with self.assertRaises(gametables.GameTableError):
            self.gt.spell_crit_per_int_percent(WARRIOR, 60)  # zero ratio
        with self.assertRaises(gametables.GameTableError):
            self.gt.rating_per_percent(32, 60)

    def test_melee_crit_percent_composes(self):
        # base + agi + rating, additively, warrior level 70
        base = self.gt.melee_crit_base_percent(WARRIOR)
        agi = 180 * self.gt.melee_crit_per_agi_percent(WARRIOR, 70)
        rating = 250 / self.gt.rating_per_percent(gametables.CR_CRIT_MELEE, 70)
        total = self.gt.melee_crit_percent(WARRIOR, 70, 180, 250)
        self.assertAlmostEqual(total, base + agi + rating, places=6)
