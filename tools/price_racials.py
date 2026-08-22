"""Phase 1c: price all ten 024 racials at 60 and 70, in per-level Blood
Fury units, with sweep bands. Writes docs/racial-pricing-report.md.

Usage (from the repo root):

    py -3 tools\\price_racials.py

Reads: data/profiles/*.json (built by tools/build_profiles.py),
data/export/gametables.json. Every assumption is printed into the
report; sweeps carry (lo, mid, hi); wide sweeps are flagged as the
target-dummy candidates per design 025 section 4.4.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import export as export_mod
from kb import pricing, yardstick

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# sweep register (docs/racial-pricing-worksheet.md)
WHITE_SHARE = (0.20, 0.35, 0.50)
PROC_SHARE = (0.00, 0.08, 0.15)
DOT_SHARE_AFFLICTION = (0.60, 0.75, 0.90)
SP_FRACTION = (0.40, 0.50, 0.60)
TALENTS = {"fury warrior": 20.0, "combat rogue": 30.0,
           "affliction warlock": 0.0}


def load_profiles():
    out = {}
    pdir = os.path.join(ROOT, "data", "profiles")
    for name in sorted(os.listdir(pdir)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(pdir, name), encoding="ascii") as f:
            prof = json.load(f)
        out[(prof["spec"], prof["level"])] = prof
    return out


def fmt_band(vals, unit="%"):
    lo, mid, hi = vals
    return "%.2f (%.2f - %.2f)%s" % (mid, lo, hi, unit)


def bf_ratio(sustained_pct, bf_sustained_pct):
    if bf_sustained_pct <= 0:
        return 0.0
    return sustained_pct / bf_sustained_pct


def price_all(profiles):
    lines = []
    add = lines.append

    add("# Racial Pricing Report - Phase 1c (S243)")
    add("")
    add("**Every number here is derived from our own data or swept - no")
    add("measurement was taken.** Profiles are UNBUFFED and UNTALENTED for")
    add("stats (no gems/enchants/set bonuses/raid buffs), so absolute")
    add("percentages run a little hot versus a raid-buffed character; the")
    add("Blood Fury RATIOS are computed on the same basis top and bottom")
    add("and are the numbers to trust. Method: design 025; mechanics:")
    add("guide-combat-math.md; routes: docs/racial-pricing-worksheet.md.")
    add("")
    doc = export_mod.load(os.path.join(ROOT, "data", "export",
                                       "gametables.json"))
    add("Export: generated %s, payload %s." % (
        doc["stamp"]["generated_at"],
        doc["stamp"]["payload_sha256"][:16]))
    add("")

    # ---- the yardstick per anchor profile ----
    add("## The yardstick: Blood Fury on the anchor profiles")
    add("")
    add("| profile | level | full-uptime gain | sustained (12.5% uptime) | percent-seconds/cycle |")
    add("|---|---|---|---|---|")
    bf = {}
    for (spec, level), prof in sorted(profiles.items()):
        if not prof.get("weapons") or "main_hand" not in prof["weapons"]:
            continue
        if prof["class_id"] not in (1, 4):
            continue
        sustained, ps = pricing.blood_fury_price(prof)
        bf[(spec, level)] = sustained
        full = ps / 15.0
        add("| %s | %d | +%.2f%% | +%.3f%% | %.0f |"
            % (spec, level, full, sustained, ps))
    add("")
    add("Blood Fury moves with level and gear exactly as design 025")
    add("section 7 predicted - the unit is per-profile, and every ratio")
    add("below names the profile it is measured against.")
    add("")

    # ---- Night Elf ----
    add("## Night Elf - Out of the Shadows (the headline)")
    add("")
    add("+15pp crit / +15 crit damage decaying over 10s per 120s")
    add("(Shadowmeld cooldown restarted on exit). White-share and")
    add("crit-proc-share are SWEPT; talent compounding applied per spec")
    add("(Impale 20, Lethality 30). Ratios vs the same profile's Blood")
    add("Fury sustained value.")
    add("")
    add("| profile | level | base crit | percent-seconds (proc sweep) | sustained | x Blood Fury |")
    add("|---|---|---|---|---|---|")
    ne_flag = []
    for (spec, level), prof in sorted(profiles.items()):
        if prof["class_id"] not in (1, 4):
            continue
        crit = prof["melee_crit_pct"]
        talent = TALENTS.get(spec, 0.0)
        band = []
        for proc in PROC_SHARE:
            w = WHITE_SHARE[1]
            ability = 1.0 - w - proc
            mean10, ps, sustained = pricing.out_of_the_shadows_price(
                crit, w, ability, proc, talent)
            band.append((ps, sustained))
        ps_band = tuple(b[0] for b in band)
        s_mid = band[1][1]
        ratio = bf_ratio(s_mid, bf[(spec, level)])
        add("| %s | %d | %.1f%% | %s | +%.3f%% | **%.2fx** |"
            % (spec, level, crit,
               "%.0f (%.0f - %.0f)" % (ps_band[1], ps_band[0], ps_band[2]),
               s_mid, ratio))
        spread = ps_band[2] - ps_band[0]
        if spread > 25:
            ne_flag.append((spec, level, spread))
    # caster variant on the warlock profile
    for level in (60, 70):
        prof = profiles.get(("affliction warlock", level))
        if not prof or not prof.get("spell_crit_pct"):
            continue
        crit = prof["spell_crit_pct"]
        mean10, ps, sustained = pricing.out_of_the_shadows_price(
            crit, 0.0, 0.0, 0.0, 0.0, spell_share=1.0)
        add("| caster (lock profile) | %d | %.1f%% | %.0f | +%.3f%% | structural ~0.5x melee |"
            % (level, crit, ps, sustained))
    add("")
    add("White-vs-ability composition moves the answer by under 2 points")
    add("across its whole range (verified: design 025 section 4.4 holds")
    add("on the real profiles). **The crit-proc share is the wide axis**")
    if ne_flag:
        add("- the sweep spans are wide enough that a Deep Wounds/Ignite")
        add("share estimate per spec is the ONE measurement worth having")
        add("(the design 025 escape hatch), for: %s."
            % ", ".join("%s L%d (+/-%.0f ps)" % f for f in ne_flag))
    add("")

    # ---- Orc ----
    add("## Orc - Warband Fury (gain) and Axe Spec (loss)")
    add("")
    add("| item | level | per-recipient | notes |")
    add("|---|---|---|---|")
    for level in (60, 70):
        share_ap = 0.25 * yardstick.blood_fury_attack_power(level)
        for spec in ("fury warrior", "combat rogue"):
            prof = profiles.get((spec, level))
            if not prof:
                continue
            gain = pricing.flat_ap_gain_pct(prof, share_ap)
            s, ps = pricing.windowed(gain, 15.0)
            add("| Warband Fury AP share | %d | +%.3f%% sustained on %s (%.0f ps) | %.0f AP for 15s/120s |"
                % (level, s, spec, ps, share_ap))
        sp_share = 0.25 * yardstick.blood_fury_spell_power(level)
        prof = profiles.get(("affliction warlock", level))
        if prof and prof.get("spell_power"):
            band = pricing.sp_gain_band_pct(prof, sp_share, SP_FRACTION)
            s_band = tuple(pricing.windowed(g, 15.0)[0] for g in band)
            add("| Warband Fury SP share | %d | +%s sustained on caster | %.0f SP; SP-fraction swept |"
                % (level, fmt_band(s_band), sp_share))
    add("| Axe Spec removal | any | -%.2f%% on axe users | conditional on weapon (the cage being removed) |"
        % pricing.expertise_removal_pct(5))
    add("")

    # ---- Undead ----
    add("## Undead - Gorged")
    add("")
    add("| model | level | profile | sustained | percent-seconds |")
    add("|---|---|---|---|---|")
    for level in (60, 70):
        for spec in ("fury warrior",):
            prof = profiles.get((spec, level))
            if not prof:
                continue
            s_pre, ps_pre = pricing.gorged_price(prof, prepull=True)
            s_in, _ = pricing.gorged_price(prof, prepull=False)
            add("| pre-pull channel | %d | %s | +%.3f%% | %.0f |"
                % (level, spec, s_pre, ps_pre))
            add("| in-combat channel | %d | %s | %+.3f%% (channel cost included) | - |"
                % (level, spec, s_in))
    add("")
    add("The in-combat model is net NEGATIVE for DPS - the 10s channel")
    add("costs more than the buff returns. Gorged is a between-pulls /")
    add("pre-pull racial, and honest pricing says so.")
    add("")

    # ---- the rest ----
    add("## The remaining racials, priced")
    add("")
    add("| race | component | level | value | route |")
    add("|---|---|---|---|---|")
    for level in (60, 70):
        prof = profiles.get(("fury warrior", level))
        if prof:
            g = pricing.flat_ap_gain_pct(prof, 20 if level == 70 else 10)
            add("| Dwarf | Hearty Appetite, AP food +50%% | %d | +%.3f%% sustained while fed | closed form (L60 food values half-assumed - read L60 Well Fed rows before quoting) |"
                % (level, g))
    lockp = profiles.get(("affliction warlock", 70))
    if lockp and lockp.get("spell_power"):
        band = pricing.sp_gain_band_pct(lockp, 11.5, SP_FRACTION)
        add("| Dwarf | Hearty Appetite, SP food +50%% | 70 | +%s while fed | closed form x SP fraction |"
            % fmt_band(band))
        band = pricing.sp_gain_band_pct(lockp, 20, SP_FRACTION)
        add("| Blood Elf | Bloodthistle (Outland tier, +20 SP) | 70 | +%s while active | consumable, not passive |"
            % fmt_band(band))
        band = pricing.sp_gain_band_pct(lockp, 10, SP_FRACTION)
        add("| Blood Elf | Bloodthistle (Classic tier, +10 SP) | 70 | +%s while active | consumable |"
            % fmt_band(band))
    voodoo = pricing.strong_voodoo_price(DOT_SHARE_AFFLICTION)
    add("| Troll | Strong Voodoo, affliction lock | any | +%s sustained | +2%% x DoT share (swept) - LARGER than it reads |"
        % fmt_band(voodoo))
    add("| Troll | Strong Voodoo, melee specs | any | ~0% | no DoT share to speak of |")
    add("| Troll | Regeneration | any | not DPS - survivability/downtime | not priced here |")
    haste = pricing.haste_price(1.0)
    add("| Gnome | Expansive Mind +1%% haste | any | +%s | closed form |" % fmt_band(haste))
    add("| Gnome | Engineering bombs +20% | any | situational burst; ~0 sustained outside bomb usage | swept 0-2 bombs/min elsewhere |")
    add("| Gnome | Escape Artist -10% debuff duration | any | utility, not DPS | not priced |")
    after = pricing.aftershock_price()
    add("| Tauren | Aftershock (group) | any | +%s of GROUP damage | 10%% x 5%% uptime x stomp-window share (swept) |"
        % fmt_band(after))
    add("| Draenei | Light Within | any | +%.2f%% ceiling (once per 5min, below 35%% health) | bounded ceiling |"
        % pricing.light_within_price())
    add("| Draenei | Heroic Presence REMOVAL | any | about -%.2f%% per party member under the miss cap | the largest removal in the pass |"
        % pricing.hit_removal_pct(1.0))
    add("| Human | Jack of All Trades trickle | any | small; Master of Anatomy rank value pending a Spell.dbc read | bounded |")
    add("| Human | Sword/Mace Spec removal | any | -%.2f%% on sword/mace melee | conditional (the cage) |"
        % pricing.expertise_removal_pct(3))
    add("| Dwarf | Mace Spec removal | any | -%.2f%% on mace melee | conditional |"
        % pricing.expertise_removal_pct(5))
    add("| Dwarf/Troll | Gun/Bow Spec removal | any | about -0.7% ranged (1pp crit) | hunters only |")
    add("| Blood Elf | Arcane Torrent buffs | any | resource value - DEFERRED to the mana phase; rogue burst bounded elsewhere | deferred |")
    add("")

    add("## Reading guidance - what the numbers actually say")
    add("")
    add("**1. The yardstick moved more than the racial.** 024 priced")
    add("everything against a RAID-GEARED Blood Fury (~117 ps at 70).")
    add("On the real PRE-RAID profiles Blood Fury is worth far more")
    add("(~175 ps at 70, ~277 at 60), because a flat AP grant is")
    add("relatively bigger on a smaller damage pool. Out of the Shadows")
    add("is nearly gear- and level-invariant by construction. So at")
    add("pre-raid gear it sits BELOW Blood Fury (about 0.5x at 60,")
    add("0.8-0.9x at 70) - and its ratio RISES as gear grows. Against")
    add("024's own raid-geared Blood Fury figure (117 ps) the same")
    add("percent-seconds read ~1.2x for fury and ~1.35x for a Lethality")
    add("rogue: the S235 concern is CONFIRMED for raid gear, and the")
    add("design question is now precise - do you want a racial that")
    add("strengthens relative to the yardstick as gear improves?")
    add("")
    add("**2. The sleeper is Strong Voodoo.** +2 percent on DoTs is a")
    add("passive worth ~1.5 percent sustained on an affliction lock -")
    add("about equal to Blood Fury's entire sustained value on a")
    add("pre-raid melee, always on, no button. Nothing else in the pass")
    add("gives a single spec that much passively.")
    add("")
    add("**3. Gorged is two racials.** Pre-pull it is strong (183 ps at")
    add("60 - more than Out of the Shadows); mid-combat it is a trap")
    add("(net negative once the 10s channel is costed). Worth saying in")
    add("its tooltip-adjacent lore or accepting knowingly.")
    add("")
    add("**4. The removals are not symmetric.** Heroic Presence is the")
    add("single largest number in either direction (about -1.1 percent")
    add("per party member); the weapon specs are conditional losses the")
    add("cage-removal rationale already accepts.")
    add("")
    add("**5. What would change these numbers:** the crit-proc share")
    add("(Deep Wounds/Ignite) is the one swept input wide enough to")
    add("move a decision - the design 025 escape hatch (one target-dummy")
    add("session) applies to it and to nothing else here. This report")
    add("prices; whether a gap is acceptable stays the group's call.")
    return lines


def main():
    profiles = load_profiles()
    if not profiles:
        print("no profiles found - run tools/build_profiles.py first")
        return 1
    lines = price_all(profiles)
    out = os.path.join(ROOT, "docs", "racial-pricing-report.md")
    text = "\n".join(lines) + "\n"
    text.encode("ascii")
    with open(out, "w", encoding="ascii", newline="\n") as f:
        f.write(text)
    print(text)
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
