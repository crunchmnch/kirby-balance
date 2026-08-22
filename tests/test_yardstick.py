"""Pins the Blood Fury closed forms to design 025 section 6's MEASURED
table (kirby-server repo) - including the DieSides +1 that both
guide-combat-math.md and ADR 012 briefly dropped from the spell power line
(corrected S243).
"""

import unittest

from kb import yardstick

# design 025 section 6, measured from patchV-Spell.dbc via CalcValue
MEASURED_AP = {10: 42, 20: 82, 30: 122, 40: 162, 50: 202, 60: 242,
               70: 282, 80: 322}
MEASURED_SP = {10: 23, 20: 43, 30: 63, 40: 83, 50: 103, 60: 123,
               70: 143, 80: 163}


class YardstickTests(unittest.TestCase):
    def test_attack_power_matches_measured_table(self):
        for level, ap in MEASURED_AP.items():
            self.assertEqual(yardstick.blood_fury_attack_power(level), ap)

    def test_spell_power_matches_measured_table(self):
        for level, sp in MEASURED_SP.items():
            self.assertEqual(yardstick.blood_fury_spell_power(level), sp)

    def test_spell_power_carries_the_diesides_plus_one(self):
        # 2*level+2 is the slip the documents carried; it must fail here.
        self.assertNotEqual(yardstick.blood_fury_spell_power(70), 142)
        self.assertEqual(yardstick.blood_fury_spell_power(70), 143)

    def test_fails_closed_outside_range(self):
        with self.assertRaises(yardstick.YardstickError):
            yardstick.blood_fury_attack_power(0)
        with self.assertRaises(yardstick.YardstickError):
            yardstick.blood_fury_attack_power(81)
        with self.assertRaises(yardstick.YardstickError):
            yardstick.blood_fury_attack_power(70.0)  # non-integer level

    def test_gain_fraction_shape(self):
        # design 025 section 7.2: the yardstick's own percent gain shrinks
        # as base damage grows - the unit moves with gear and level.
        rich = yardstick.blood_fury_gain_fraction(70, 104.0, 1900.0)
        poor = yardstick.blood_fury_gain_fraction(40, 40.0, 500.0)
        self.assertLess(rich, poor)
        # spot value: X=282, X/14=20.142..; base 103.9 + 135.7 = 239.6
        self.assertAlmostEqual(rich, (282 / 14.0) / (104.0 + 1900 / 14.0),
                               places=9)
