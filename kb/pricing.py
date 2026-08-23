"""Racial pricing - the Phase 1c computations.

Every function returns sustained percent gain (mean over the cooldown
cycle) and, where the effect is windowed, percent-seconds per 120s cycle
(mean gain during the window x window seconds) - the unit design 024
uses. Swept inputs go in as (lo, mid, hi) and come out as bands.

Method: design 025 (derive, sweep, never trust an unlabelled number).
Crit arithmetic: kb/engine/damage.py, asserted against source.
The routes and shares per racial: docs/racial-pricing-worksheet.md.
"""

from kb import yardstick
from kb.engine import damage

BOSS_DODGE_BASELINE_PCT = 6.5   # level+3 boss vs capped weapon skill
EXPERTISE_PER_POINT_PCT = 0.25  # 1 expertise = 0.25 pp dodge/parry reduction


class PricingError(Exception):
    pass


def dual_wield_white_model(profile):
    """(weapon_dps_total, ap_coeff) for the white-damage closed form.

    MH swings get AP/14 * mh_speed per swing; OH the same with its speed
    but OH damage is halved (stock 50 percent penalty). So total white
    DPS = mh_wdps + 0.5*oh_wdps + (AP/14) * (1 + 0.5) for dual wield,
    or + (AP/14) * 1 for a single weapon. v0: no miss/glancing table -
    consistent numerator and denominator, so RATIOS survive (025 4.1).
    """
    weapons = profile["weapons"]
    if profile.get("class_id") == 3:
        # hunter: the ranged weapon is the white-damage source; the
        # profile's attack_power is RANGED AP (kb/profiles.py). Ammo and
        # quiver haste are NOT modelled - absolute DPS understated,
        # ratios unaffected (both sides share the omission).
        if "ranged" not in weapons:
            raise PricingError(
                "hunter profile %s has no ranged weapon" % profile["spec"])
        return weapons["ranged"]["dps"], 1.0
    if "main_hand" not in weapons:
        raise PricingError("profile %s has no main hand" % profile["spec"])
    wdps = weapons["main_hand"]["dps"]
    ap_coeff = 1.0
    if "off_hand" in weapons:
        wdps += 0.5 * weapons["off_hand"]["dps"]
        ap_coeff += 0.5
    return wdps, ap_coeff


def flat_ap_gain_pct(profile, extra_ap):
    """Full-uptime percent white-DPS gain from a flat AP grant."""
    wdps, ap_coeff = dual_wield_white_model(profile)
    base = wdps + profile["attack_power"] / yardstick.AP_PER_DPS * ap_coeff
    return (extra_ap / yardstick.AP_PER_DPS * ap_coeff) / base * 100.0


def windowed(gain_pct_during, duration_s, cycle_s=120.0):
    """(sustained_pct, percent_seconds) for a windowed effect."""
    return (gain_pct_during * duration_s / cycle_s,
            gain_pct_during * duration_s)


def blood_fury_price(profile):
    """The yardstick itself, on this profile: sustained pct and
    percent-seconds. Every other racial is quoted against this."""
    gain = flat_ap_gain_pct(profile, yardstick.blood_fury_attack_power(
        profile["level"]))
    return windowed(gain, 15.0)


def sp_gain_band_pct(profile, extra_sp, sp_damage_fraction=(0.40, 0.50, 0.60)):
    """Banded percent gain for a spell power grant on a caster.

    A caster's DPS is base + coeff*SP; without rotations the SP-driven
    fraction of damage is UNDERIVED, so it is swept (worksheet register).
    percent gain = (extra/SP) * fraction, per band point.
    """
    sp = profile.get("spell_power") or 0
    if sp <= 0:
        raise PricingError("profile %s has no spell power" % profile["spec"])
    return tuple(extra_sp / float(sp) * f * 100.0 for f in sp_damage_fraction)


def crit_burst_window_gain_pct(crit_pct, crit_delta_pp, aura163_amount,
                               white_share, ability_share, proc_share,
                               talent_bonus_pct=0.0, spell_share=0.0):
    """Percent damage gain during ONE window of a crit chance + crit
    damage buff (the Out of the Shadows shape), for a damage mix.

    Shares are of baseline damage and must sum to 1. Proc share scales
    with the crit RATE ratio (crit-triggered effects: Deep Wounds family).
    """
    total_share = white_share + ability_share + proc_share + spell_share
    if abs(total_share - 1.0) > 1e-9:
        raise PricingError("damage shares sum to %r, not 1" % total_share)
    c0 = crit_pct / 100.0
    c1 = min(1.0, c0 + crit_delta_pp / 100.0)
    if c0 <= 0.0:
        raise PricingError("zero base crit cannot price a crit-rate ratio")

    def factor(m0, m1):
        f0 = 1.0 + c0 * (m0 - 1.0)
        f1 = 1.0 + c1 * (m1 - 1.0)
        return f0, f1

    fw0, fw1 = factor(damage.white_crit_multiplier(),
                      damage.white_crit_multiplier([aura163_amount]))
    fa0, fa1 = factor(damage.ability_crit_multiplier((), talent_bonus_pct),
                      damage.ability_crit_multiplier([aura163_amount],
                                                     talent_bonus_pct))
    fs0, fs1 = factor(damage.spell_crit_multiplier((), talent_bonus_pct),
                      damage.spell_crit_multiplier([aura163_amount],
                                                   talent_bonus_pct))
    base = (white_share * fw0 + ability_share * fa0 + spell_share * fs0
            + proc_share * 1.0)
    buffed = (white_share * fw1 + ability_share * fa1 + spell_share * fs1
              + proc_share * (c1 / c0))
    return (buffed / base - 1.0) * 100.0


def out_of_the_shadows_price(crit_pct, white_share, ability_share,
                             proc_share, talent_bonus_pct=0.0,
                             spell_share=0.0):
    """The full decaying burst: 5 windows of 2s, amounts 15,12,9,6,3 on
    both crit chance (pp) and crit damage (aura 163), per design 024
    section 11.4. Returns (mean_gain_pct_over_10s, percent_seconds,
    sustained_pct) on the 120s Shadowmeld cycle."""
    total_ps = 0.0
    for stacks in (5, 4, 3, 2, 1):
        amt = 3.0 * stacks
        g = crit_burst_window_gain_pct(
            crit_pct, amt, amt, white_share, ability_share, proc_share,
            talent_bonus_pct, spell_share)
        total_ps += g * 2.0
    mean10 = total_ps / 10.0
    return mean10, total_ps, total_ps / 120.0


def expertise_removal_pct(points=5):
    """Percent melee damage LOST when an expertise racial is removed,
    for a weapon-matched melee vs a dodging boss (v0 attack-table-free
    approximation: recovered dodges land as normal hits)."""
    dodge_removed = min(points * EXPERTISE_PER_POINT_PCT,
                        BOSS_DODGE_BASELINE_PCT)
    return dodge_removed / (100.0 - BOSS_DODGE_BASELINE_PCT) * 100.0


def hit_removal_pct(pp=1.0, miss_baseline_pct=8.0):
    """Percent damage per party member lost with Heroic Presence, while
    under the miss cap (default: dual-wield-ish white miss baseline;
    casters vs +3 boss sit near 9 pp short of cap - both above 1 pp)."""
    return pp / (100.0 - miss_baseline_pct) * 100.0


def gorged_price(profile, stacks=5, prepull=True):
    """Undead Gorged: level*0.4 AP + level*0.2 SP per stack, 30s buff,
    120s cd. Pre-pull model: buff overlaps the fight for its remaining
    ~20s after a 10s channel = 20s effective window, no DPS cost.
    In-combat model: full 30s window minus 10s of zero output."""
    level = profile["level"]
    ap = level * 0.4 * stacks
    gain = flat_ap_gain_pct(profile, ap)
    if prepull:
        return windowed(gain, 20.0)
    sustained, ps = windowed(gain, 30.0)
    channel_cost_pct = 10.0 / 120.0 * 100.0
    return sustained - channel_cost_pct, ps - channel_cost_pct * 120.0


def aftershock_price(window_share=(0.3, 0.65, 1.0)):
    """Tauren Aftershock: +10 percent damage taken on stomped targets,
    6s per 120s. Swept on the share of group damage landing on stomped
    targets during the window."""
    return tuple(windowed(10.0 * s, 6.0)[0] for s in window_share)


def light_within_price():
    """Draenei: +10 percent for 8s per 300s IF it triggers - ceiling."""
    return 10.0 * 8.0 / 300.0


def haste_price(pct=1.0):
    """Gnome Expansive Mind haste: throughput band (fixed rotations
    realize slightly less than white-speed scaling)."""
    return (0.8 * pct, 0.9 * pct, 1.0 * pct)


def strong_voodoo_price(dot_share):
    """Troll: +2 percent own DoTs/HoTs x DoT damage share (swept)."""
    return tuple(2.0 * s for s in dot_share)


def on_use_haste_price(haste_pct, duration_s, cooldown_s):
    """Sustained percent gain of an on-use haste racial (Berserking
    shape): throughput scales ~linearly with combat speed, so the
    sustained value is haste x duration / cooldown.

    Berserking (26297) MEASURED S243 from our Spell.dbc: aura 193
    (melee + ranged + cast speed), BasePoints 19 + DieSides 1 = +20
    percent flat (no low-health scaling in this core's row),
    DurationIndex 1 = 10000 ms, RecoveryTime = 180000 ms.
    """
    if cooldown_s <= 0 or duration_s <= 0:
        raise PricingError("berserking shape needs positive timing")
    return haste_pct * duration_s / cooldown_s


def berserking_price():
    """(sustained_pct, percent_seconds_per_own_cycle) for Berserking."""
    return on_use_haste_price(20.0, 10.0, 180.0), 20.0 * 10.0
