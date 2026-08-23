"""Price Draenei Light's Providence as a PERMANENT flat crit-chance grant.

Written S245, after the user corrected the S244 decision: the passive
grants +1% CRIT, not +1% hit, so that it also benefits Draenei healing
specs (heal crits use the spell crit chance, and their bonus is
damage / 2 - the same +50 percent as spell damage - Unit.cpp:9551).

MECHANISM, asserted against the fork source S245, not recalled: one
effect, SPELL_AURA_MOD_CRIT_PCT (290), covers all three paths at once -
Player::UpdateWeaponDependentCritAuras adds it with NO item requirement
("these auras don't have item requirement (only Combat Expertise in
3.3.5a)", Player.cpp:7303) and Player::UpdateSpellCritChance adds it
directly (StatSystem.cpp:855). So this is ONE dial, not the aura 54+55
pair Heroic Presence used for hit.

THE QUESTION THIS TOOL EXISTS TO ANSWER (user, S245): does it scale too
hard on warriors and hunters, the crit-damage-talent classes a draenei
can be? Two sweeps below answer it directly - value against rising gear
crit, and value against the crit-damage package.

Usage (from the repo root):

    py -3 tools\\price_lights_providence.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import pricing, raceclass
from kb.engine import damage
from tools.price_racials import (EXPORT, PROC_SHARE, RACE, SPEC_TALENTS,
                                 WHITE_SHARE, load_profiles, pricing_crit)

DELTA_PP = 1.0
DRAENEI = RACE["draenei"]


def permanent_crit_gain(crit_pct, delta_pp, white, ability, proc,
                        talent_dmg=0.0, spell=0.0):
    """A permanent flat crit-CHANCE grant: no aura 163 (no crit damage
    component) and 100 percent uptime, so the window gain IS the
    sustained gain."""
    return pricing.crit_burst_window_gain_pct(
        crit_pct, delta_pp, 0.0, white, ability, proc, talent_dmg, spell)


def main():
    rc = raceclass.RaceClass.from_export(EXPORT)
    profiles = load_profiles()
    out = []
    add = out.append

    add("Light's Providence - permanent +%.0f pp crit (aura 290)" % DELTA_PP)
    add("=" * 62)
    add("")
    add("Reference: +1 pp HIT was worth %.3f%% (pricing.hit_removal_pct,"
        % pricing.hit_removal_pct(1.0))
    add("8 pp miss baseline) and is ANTI-SCALING - gear hit substitutes")
    add("against it and at the cap its damage value is exactly zero.")
    add("Crit has no cap, so the S244 justification for the number does")
    add("not transfer. That is what the sweeps below measure.")
    add("")
    add("Crit multipliers in play (kb/engine/damage.py, asserted vs source):")
    add("  white  %.2fx    ability %.2fx    spell/heal %.2fx"
        % (damage.white_crit_multiplier(),
           damage.ability_crit_multiplier(),
           damage.spell_crit_multiplier()))
    add("")

    add("## 1. Draenei-valid DPS profiles")
    add("")
    add("%-22s %-5s %-8s %-24s %s"
        % ("profile", "level", "crit", "sustained (mid, lo-hi)", "x Blood Fury"))
    for (spec, level), prof in sorted(profiles.items()):
        cid = prof["class_id"]
        if not rc.is_valid(DRAENEI, cid):
            add("%-22s %-5d SKIPPED - a draenei cannot be this class"
                % (spec, level))
            continue
        if cid not in (1, 3, 4):
            continue
        crit = pricing_crit(prof)
        talent_dmg = SPEC_TALENTS[spec]["crit_dmg_pct"]
        band = []
        for proc in PROC_SHARE:
            w = 0.0 if cid == 3 else WHITE_SHARE[1]
            band.append(permanent_crit_gain(
                crit, DELTA_PP, w, 1.0 - w - proc, proc, talent_dmg))
        bf_sustained, _ps = pricing.blood_fury_price(prof)
        add("%-22s %-5d %-8s %-24s %.2fx"
            % (spec, level, "%.1f%%" % crit,
               "+%.3f%% (%.3f-%.3f)" % (band[1], band[0], band[2]),
               band[1] / bf_sustained))
    add("")

    add("## 2. Caster / healer shape")
    add("")
    add("Draenei casters are priest, shaman and mage. The only caster")
    add("profile in the set is the affliction warlock, which a draenei")
    add("cannot be - used here as a SPELL-CRIT SHAPE proxy exactly as the")
    add("S243 report does for Out of the Shadows, never as a draenei row.")
    add("Healing throughput takes the SAME number: the heal crit bonus is")
    add("damage / 2 (+50 percent), identical to spell damage crit.")
    add("")
    for level in (60, 70):
        prof = profiles.get(("affliction warlock", level))
        if not prof:
            continue
        crit = prof["spell_crit_pct"]
        gain = permanent_crit_gain(crit, DELTA_PP, 0.0, 0.0, 0.0, 0.0, 1.0)
        add("  caster proxy L%d   spell crit %.1f%%   +%.3f%% damage AND healing"
            % (level, crit, gain))
    add("")

    add("## 3. SWEEP A - does it scale with GEAR crit?")
    add("")
    add("The user's question. Base crit is pushed up in 5 pp steps with")
    add("everything else held; if the number RISES the racial scales.")
    add("")
    for (spec, level) in (("fury warrior", 70), ("marksmanship hunter", 70)):
        prof = profiles.get((spec, level))
        if not prof:
            continue
        cid = prof["class_id"]
        base = pricing_crit(prof)
        talent_dmg = SPEC_TALENTS[spec]["crit_dmg_pct"]
        w = 0.0 if cid == 3 else WHITE_SHARE[1]
        proc = PROC_SHARE[1]
        row = []
        for extra in (0.0, 5.0, 10.0, 15.0, 20.0):
            g = permanent_crit_gain(base + extra, DELTA_PP, w,
                                    1.0 - w - proc, proc, talent_dmg)
            row.append("%+.0fpp: %.3f%%" % (extra, g))
        add("  %-22s %s" % (spec, "   ".join(row)))
    add("")

    add("## 4. SWEEP B - does it scale with the CRIT-DAMAGE package?")
    add("")
    add("Impale (warrior) is +20 percent and Mortal Shots (hunter) +30,")
    add("both MEASURED S244. 0 is the no-package case.")
    add("")
    for (spec, level) in (("fury warrior", 70), ("marksmanship hunter", 70)):
        prof = profiles.get((spec, level))
        if not prof:
            continue
        cid = prof["class_id"]
        crit = pricing_crit(prof)
        w = 0.0 if cid == 3 else WHITE_SHARE[1]
        proc = PROC_SHARE[1]
        row = []
        for td in (0.0, 20.0, 30.0):
            g = permanent_crit_gain(crit, DELTA_PP, w, 1.0 - w - proc,
                                    proc, td)
            row.append("crit_dmg %+.0f%%: %.3f%%" % (td, g))
        add("  %-22s %s" % (spec, "   ".join(row)))
    add("")

    text = "\n".join(out)
    text.encode("ascii")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
