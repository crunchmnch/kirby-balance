"""Pins the three crit paths to guide-combat-math.md section 1's worked
numbers, and the talent compounding order. If the guide and this model ever
disagree, one of them is defective - never a matter of taste (guide,
section 4).
"""

import unittest

from kb.engine import damage


class CritPathTests(unittest.TestCase):
    def test_white_path_b(self):
        # +15 aura 163: already-doubled damage multiplied: 2.00 -> 2.30
        self.assertAlmostEqual(damage.white_crit_multiplier([15.0]), 2.30)
        self.assertAlmostEqual(damage.white_crit_multiplier([]), 2.00)

    def test_ability_path_a(self):
        # +15 aura 163 scales the bonus only: 2.00 -> 2.15
        self.assertAlmostEqual(damage.ability_crit_multiplier([15.0]), 2.15)
        self.assertAlmostEqual(damage.ability_crit_multiplier([]), 2.00)

    def test_spell_path_a(self):
        # +15 aura 163 on the half-bonus: 1.50 -> 1.575
        self.assertAlmostEqual(damage.spell_crit_multiplier([15.0]), 1.575)
        self.assertAlmostEqual(damage.spell_crit_multiplier([]), 1.50)

    def test_same_aura_worth_double_on_white(self):
        # The guide's headline: the same amount is worth ~2x on a white
        # swing. Extra multiplier over base, white vs ability:
        white_extra = damage.white_crit_multiplier([15.0]) - 2.0
        ability_extra = damage.ability_crit_multiplier([15.0]) - 2.0
        self.assertAlmostEqual(white_extra / ability_extra, 2.0)

    def test_talent_compounds_multiplicatively(self):
        # Impale +20 on top of aura +15: bonus 1.0 -> 1.15 -> 1.38,
        # never 1.35 (guide section 1, design 025 section 3.1).
        mult = damage.ability_crit_multiplier([15.0], talent_bonus_pct=20.0)
        self.assertAlmostEqual(mult, 1.0 + 1.0 * 1.15 * 1.20)
        self.assertAlmostEqual(mult, 2.38)
        self.assertNotAlmostEqual(mult, 2.35)

    def test_path_aggregation_differs_with_two_auras(self):
        # White path multiplies per aura; ability path sums. One aura:
        # identical. Two auras of +15: white 2*1.15*1.15=2.645 vs
        # ability 1 + 1.30 = 2.30 + doubling shape - they must diverge.
        white = damage.white_crit_multiplier([15.0, 15.0])
        ability = damage.ability_crit_multiplier([15.0, 15.0])
        self.assertAlmostEqual(white, 2.0 * 1.15 * 1.15)
        self.assertAlmostEqual(ability, 1.0 + 1.30)
        self.assertNotAlmostEqual(white - 2.0, (ability - 2.0) * 2.0)
