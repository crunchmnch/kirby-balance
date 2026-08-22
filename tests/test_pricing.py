"""Pins the pricing math to hand-checkable values and to design 024's
own worked table where 024 was RIGHT (its assumptions reproduced), so
the 1c report's corrections are visibly method-driven, not drift."""

import unittest

from kb import pricing


PROFILE = {  # synthetic single-weapon melee for closed-form checks
    "spec": "test melee", "level": 70, "attack_power": 1900,
    "spell_power": 0,
    "weapons": {"main_hand": {"dps": 103.9, "dmg_min": 274, "dmg_max": 412,
                              "delay_ms": 3300}},
}


class PricingTests(unittest.TestCase):
    def test_blood_fury_matches_yardstick_closed_form(self):
        # single weapon: (282/14) / (103.9 + 1900/14) at full uptime
        sustained, ps = pricing.blood_fury_price(PROFILE)
        full = (282 / 14.0) / (103.9 + 1900 / 14.0) * 100.0
        self.assertAlmostEqual(ps, full * 15.0, places=6)
        self.assertAlmostEqual(sustained, full * 15.0 / 120.0, places=6)

    def test_dual_wield_raises_ap_coeff(self):
        p = dict(PROFILE)
        p["weapons"] = dict(p["weapons"])
        p["weapons"]["off_hand"] = {"dps": 80.0, "dmg_min": 100,
                                    "dmg_max": 200, "delay_ms": 1800}
        wdps, coeff = pricing.dual_wield_white_model(p)
        self.assertAlmostEqual(wdps, 103.9 + 40.0)
        self.assertAlmostEqual(coeff, 1.5)

    def test_oots_reproduces_024_table_under_024_assumptions(self):
        # 024 section 11.4: 25 percent crit, ability-path semantics
        # uniformly, no talents, no procs, no white distinction. Setting
        # white_share=0, ability_share=1 reproduces its first row:
        # 5 stacks -> +16.8 percent.
        g5 = pricing.crit_burst_window_gain_pct(
            25.0, 15.0, 15.0, white_share=0.0, ability_share=1.0,
            proc_share=0.0)
        self.assertAlmostEqual(g5, 16.8, places=1)
        # and the full decay lands near 024's mean 9.8 percent
        mean10, ps, sustained = pricing.out_of_the_shadows_price(
            25.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(mean10, 9.8, delta=0.15)
        self.assertAlmostEqual(ps, 98.0, delta=1.5)

    def test_oots_s235_correction_direction(self):
        # design 025 section 3.3: adding white share and Impale RAISES
        # the price for a warrior at 35 percent crit.
        base = pricing.out_of_the_shadows_price(35.0, 0.0, 1.0, 0.0)[1]
        real = pricing.out_of_the_shadows_price(
            35.0, 0.35, 0.65, 0.0, talent_bonus_pct=20.0)[1]
        self.assertGreater(real, base)

    def test_oots_proc_share_scales_with_crit_ratio(self):
        # pure proc damage at c=35, +15pp -> ratio 50/35 = +42.9 percent
        g = pricing.crit_burst_window_gain_pct(
            35.0, 15.0, 15.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(g, (50.0 / 35.0 - 1.0) * 100.0, places=6)

    def test_expertise_matches_024_measurement(self):
        # 024 section 5.2 table: +5 expertise = +1.34 percent melee
        self.assertAlmostEqual(pricing.expertise_removal_pct(5), 1.34,
                               places=2)

    def test_shares_must_sum_to_one(self):
        with self.assertRaises(pricing.PricingError):
            pricing.crit_burst_window_gain_pct(
                35.0, 15.0, 15.0, 0.5, 0.6, 0.0)

    def test_gorged_prepull_vs_incombat(self):
        pre_s, _ = pricing.gorged_price(PROFILE, prepull=True)
        in_s, _ = pricing.gorged_price(PROFILE, prepull=False)
        self.assertGreater(pre_s, 0)
        self.assertLess(in_s, pre_s)  # the channel costs real output

    def test_sp_band_shape(self):
        p = {"spec": "test caster", "level": 70, "spell_power": 700,
             "weapons": {}}
        lo, mid, hi = pricing.sp_gain_band_pct(p, 70)
        self.assertLess(lo, mid)
        self.assertLess(mid, hi)
        self.assertAlmostEqual(mid, 70 / 700 * 0.5 * 100.0)

    def test_light_within_ceiling(self):
        self.assertAlmostEqual(pricing.light_within_price(), 0.2667,
                               places=3)
