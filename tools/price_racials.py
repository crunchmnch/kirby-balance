"""Phase 1c (v3, S243): price the NEW racials against the ORIGINAL Blood
Fury - the strongest stock DPS racial and the pass's soft power ceiling
(user, S243). Writes docs/racial-pricing-report.md.

v2 changes, all from user review of v1:
- race/class validity enforced from CharBaseInfo.dbc via the export -
  v1 priced Strong Voodoo on a troll warlock, which does not exist.
- crit basis now includes per-spec TALENT packages (v1 was untalented,
  which read as implausibly low base crit). Packages are RECALLED and
  labelled so, pending a Talent.dbc read.
- removals (Heroic Presence, weapon specs) deliberately NOT tabulated -
  the group cares about new racials vs the old ceiling, not the nerfs
  everyone shares.
- a crit transparency appendix shows exactly how each profile's crit
  number is built, term by term.

v3 changes (user review of v2): marksmanship hunter added as a fourth
anchor spec (ranged model - Auto Shot has no Path-B white); Berserking
measured from Spell.dbc and tabled beside Strong Voodoo as the racial
trolls already own; the x-Blood-Fury ratio appears on EVERY priced row.

v3.1 (S244): the talent packages are MEASURED, no longer recalled -
every value confirmed from dev Spell.dbc + Talent.dbc rank chains (see
SPEC_TALENTS below for the spell ids). All values matched the recalled
ones, so no number in the report moved. NOTE: the S244 Phase 1d DESIGN
decisions (haste OotS, Gorged v2, Light Within v2, Endurance) are NOT
re-priced here - design 024 carries those numbers with provenance; this
report remains the S243 basis the decisions were made from.

Usage (from the repo root):  py -3 tools\\price_racials.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import export as export_mod
from kb import pricing, raceclass, yardstick

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "data", "export", "gametables.json")

# sweep register (docs/racial-pricing-worksheet.md)
WHITE_SHARE = (0.20, 0.35, 0.50)
PROC_SHARE = (0.00, 0.08, 0.15)
SP_FRACTION = (0.40, 0.50, 0.60)

# Talent packages - MEASURED S244 from dev Spell.dbc + Talent.dbc rank
# chains (was RECALLED S243; every measured value matched). crit_pp is
# added to the profile's derived crit; crit_dmg feeds the ability path
# (SPELLMOD_CRIT_DAMAGE_BONUS, compounds after aura 163 per the guide).
# Measured rows: Cruelty r5 12856 aura 52 +5; Berserker Stance passive
# 7381 aura 52 +3 (applied by the shapeshift handler,
# SpellAuraEffects.cpp:1384); Impale r2 16494 aura 108 misc 15 +20;
# Malice r5 14142 +5; Lethality r5 14137 aura 108/15 +30; Lethal Shots
# r5 19431 +5; Mortal Shots r5 19490 aura 108/15 +30 (its second +60
# effect carries an unread EffectSpellClassMask - flagged, not summed).
SPEC_TALENTS = {
    "fury warrior": {"crit_pp": 8.0,   # Cruelty 5 + Berserker Stance 3
                     "crit_dmg_pct": 20.0},  # Impale
    "combat rogue": {"crit_pp": 5.0,   # Malice
                     "crit_dmg_pct": 30.0},  # Lethality (builders)
    "marksmanship hunter": {"crit_pp": 5.0,   # Lethal Shots
                            "crit_dmg_pct": 30.0},  # Mortal Shots
    "affliction warlock": {"crit_pp": 0.0, "crit_dmg_pct": 0.0},
}

# Strong Voodoo: DoT damage share sweeps per VALID troll class.
# Midpoints are placeholders pending the wowsims reference harvest.
TROLL_DOT_SHARES = [
    ("shadow priest", 5, (0.35, 0.45, 0.60)),
    ("rogue (poisons + Rupture)", 4, (0.08, 0.14, 0.20)),
    ("hunter (Serpent Sting)", 3, (0.02, 0.05, 0.08)),
    ("warrior (Deep Wounds + Rend)", 1, (0.03, 0.06, 0.10)),
    ("shaman (Flame Shock)", 7, (0.03, 0.05, 0.08)),
    ("fire mage (Ignite ticks)", 8, (0.00, 0.05, 0.10)),
]

RACE = {"human": 1, "orc": 2, "dwarf": 3, "nightelf": 4, "undead": 5,
        "tauren": 6, "gnome": 7, "troll": 8, "bloodelf": 10, "draenei": 11}


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


def pricing_crit(prof):
    """Profile-derived crit plus the spec's talent package."""
    pkg = SPEC_TALENTS.get(prof["spec"], {})
    return prof["melee_crit_pct"] + pkg.get("crit_pp", 0.0)


def price_all(profiles, rc):
    lines = []
    add = lines.append

    add("# Racial Pricing Report - Phase 1c v3 (S243)")
    add("")
    add("**The question this report answers: how does each NEW racial")
    add("compare to the ORIGINAL Blood Fury - historically the strongest")
    add("DPS racial and this pass's soft power ceiling (user, S243).**")
    add("Removals are deliberately not tabulated: they nerf broadly and")
    add("the group does not steer by them (user, S243).")
    add("")
    add("Basis: gear from the six derived pre-raid profiles (our own")
    add("item_template; no gems/enchants/set bonuses/proc trinkets), crit")
    add("INCLUDING per-spec talent packages (MEASURED S244 from Talent.dbc")
    add("+ Spell.dbc rank chains - see the appendix), no raid buffs. Race/class")
    add("pairs validated against CharBaseInfo.dbc - a racial is only")
    add("priced on a class that race can be.")
    add("")
    doc = export_mod.load(EXPORT)
    add("Export: generated %s, payload %s." % (
        doc["stamp"]["generated_at"], doc["stamp"]["payload_sha256"][:16]))
    add("")

    # ---- the ceiling ----
    add("## The soft ceiling: original Blood Fury on the anchor profiles")
    add("")
    add("| profile | level | gain while active | sustained | percent-seconds/cycle |")
    add("|---|---|---|---|---|")
    bf = {}
    for (spec, level), prof in sorted(profiles.items()):
        if prof["class_id"] not in (1, 3, 4):
            continue
        sustained, ps = pricing.blood_fury_price(prof)
        bf[(spec, level)] = sustained
        add("| %s | %d | +%.2f%% | +%.3f%% | %.0f |"
            % (spec, level, ps / 15.0, sustained, ps))
    bf_caster = {}
    for level in (60, 70):
        prof = profiles.get(("affliction warlock", level))
        if prof and prof.get("spell_power"):
            band = pricing.sp_gain_band_pct(
                prof, yardstick.blood_fury_spell_power(level), SP_FRACTION)
            bf_caster[level] = band[1] * 0.125
            add("| caster proxy (BF spell power variant) | %d | +%.2f%% (mid) | +%.3f%% | %.0f |"
                % (level, band[1], bf_caster[level], band[1] * 15.0))
    add("")
    add("Hunter note: Blood Fury 20572 grants melee AND ranged AP")
    add("(measured, design 025 section 6), so the hunter rows are the")
    add("full grant on the ranged model. Ammo and quiver haste are not")
    add("modelled - both sides of every hunter ratio share the omission.")
    add("")
    add("A flat AP grant is relatively larger on a smaller damage pool,")
    add("so the ceiling itself is HIGHER at 60 and on pre-raid gear than")
    add("the raid-geared ~117 ps design 024 used. Ratios below always")
    add("name the profile they are measured against.")
    add("")

    # ---- Night Elf ----
    add("## Night Elf - Out of the Shadows")
    add("")
    add("Valid night elf DPS: warrior, hunter, rogue, priest, druid.")
    add("Melee rows use the anchor profiles + talent packages; the")
    add("crit-proc share (Deep Wounds family) is the swept axis.")
    add("")
    add("| basis | level | crit (talented) | percent-seconds (proc sweep) | sustained | x Blood Fury (same profile) |")
    add("|---|---|---|---|---|---|")
    for (spec, level), prof in sorted(profiles.items()):
        if prof["class_id"] not in (1, 3, 4):
            continue
        crit = pricing_crit(prof)
        talent_dmg = SPEC_TALENTS[spec]["crit_dmg_pct"]
        band = []
        for proc in PROC_SHARE:
            # hunters have NO Path-B white: Auto Shot takes the ability
            # path (P3, asserted S243), so their white share is zero.
            w = 0.0 if prof["class_id"] == 3 else WHITE_SHARE[1]
            mean10, ps, sustained = pricing.out_of_the_shadows_price(
                crit, w, 1.0 - w - proc, proc, talent_dmg)
            band.append((ps, sustained))
        ps_b = tuple(b[0] for b in band)
        s_mid = band[1][1]
        add("| %s | %d | %.1f%% | %.0f (%.0f - %.0f) | +%.3f%% | **%.2fx** |"
            % (spec, level, crit, ps_b[1], ps_b[0], ps_b[2], s_mid,
               s_mid / bf[(spec, level)]))
    for level in (60, 70):
        prof = profiles.get(("affliction warlock", level))
        if not prof:
            continue
        crit = prof["spell_crit_pct"]
        mean10, ps, sustained = pricing.out_of_the_shadows_price(
            crit, 0.0, 0.0, 0.0, 0.0, spell_share=1.0)
        add("| caster shape (gear-band proxy; NE casters are priest/druid) | %d | %.1f%% | %.0f | +%.3f%% | structurally ~half the melee value |"
            % (level, crit, ps, sustained))
    add("")

    # ---- Orc ----
    add("## Orc - Warband Fury (rides Blood Fury's own press)")
    add("")
    add("| recipient | level | sustained | percent-seconds | x Blood Fury (same basis) |")
    add("|---|---|---|---|---|")
    for level in (60, 70):
        ap = 0.25 * yardstick.blood_fury_attack_power(level)
        for spec in ("fury warrior", "combat rogue", "marksmanship hunter"):
            prof = profiles.get((spec, level))
            if not prof:
                continue
            s, ps = pricing.windowed(pricing.flat_ap_gain_pct(prof, ap), 15.0)
            add("| %s | %d | +%.3f%% | %.0f | %.2fx |"
                % (spec, level, s, ps, s / bf[(spec, level)]))
        sp = 0.25 * yardstick.blood_fury_spell_power(level)
        prof = profiles.get(("affliction warlock", level))
        if prof and prof.get("spell_power") and level in bf_caster:
            band = tuple(pricing.windowed(g, 15.0)[0] for g in
                         pricing.sp_gain_band_pct(prof, sp, SP_FRACTION))
            add("| caster (gear-band proxy) | %d | +%s | - | %.2fx |"
                % (level, fmt_band(band), band[1] / bf_caster[level]))
    add("")
    add("Per recipient it is a quarter-strength Blood Fury; the racial's")
    add("value is the SUM over everyone in range when the orc presses it.")
    add("")

    # ---- Undead ----
    add("## Undead - Gorged")
    add("")
    add("| usage | level | sustained | percent-seconds | x Blood Fury (fury basis) |")
    add("|---|---|---|---|---|")
    for level in (60, 70):
        prof = profiles.get(("fury warrior", level))
        if not prof:
            continue
        s_pre, ps_pre = pricing.gorged_price(prof, prepull=True)
        s_in, _ = pricing.gorged_price(prof, prepull=False)
        fury_bf = bf[("fury warrior", level)]
        add("| pre-pull channel (corpse available) | %d | +%.3f%% | %.0f | %.2fx |"
            % (level, s_pre, ps_pre, s_pre / fury_bf))
        add("| mid-combat channel | %d | %+.3f%% net | - | negative |" % (level, s_in))
    add("")
    add("Strong exactly when a fight allows a short break AND a corpse is")
    add("nearby - a situational spike, and that shape is the point")
    add("(user, S243). Mid-combat channelling prices net negative.")
    add("")

    # ---- Troll ----
    add("## Troll - Strong Voodoo (+2% own DoTs and HoTs)")
    add("")
    add("Troll CANNOT be a warlock (CharBaseInfo.dbc) - v1 priced this on")
    add("an affliction lock and that row was wrong. Valid troll classes")
    add("with a DoT share, swept; share midpoints await the wowsims")
    add("reference harvest:")
    add("")
    add("| troll class | DoT share (swept) | sustained gain | x Blood Fury (L70 basis) |")
    add("|---|---|---|---|")
    basis_for = {1: ("fury warrior", 70), 4: ("combat rogue", 70),
                 3: ("marksmanship hunter", 70)}
    for label, class_id, shares in TROLL_DOT_SHARES:
        rc.validate(RACE["troll"], class_id)
        band = pricing.strong_voodoo_price(shares)
        key = basis_for.get(class_id)
        if key and key in bf:
            ratio = "%.2fx" % (band[1] / bf[key])
        elif 70 in bf_caster:
            ratio = "%.2fx (caster proxy)" % (band[1] / bf_caster[70])
        else:
            ratio = "-"
        add("| %s | %s | +%s | %s |"
            % (label, fmt_band(shares, ""), fmt_band(band), ratio))
    add("")
    add("The ceiling case is a shadow priest near +1%; every other troll")
    add("sits well under half a percent. The v1 headline ('the sleeper')")
    add("is WITHDRAWN - it rested on an impossible combo.")
    add("")
    add("### Berserking - the racial trolls ALREADY own")
    add("")
    add("Measured S243 from our own Spell.dbc (26297): **+20 percent")
    add("melee/ranged/cast speed, flat** (no low-health scaling in this")
    add("core's data), 10s duration, 180s cooldown.")
    add("")
    bsk, bsk_ps = pricing.berserking_price()
    add("| basis | level | Berserking sustained | x Blood Fury (same profile) |")
    add("|---|---|---|---|")
    for (spec, level) in sorted(bf):
        add("| %s | %d | +%.3f%% | **%.2fx** |"
            % (spec, level, bsk, bsk / bf[(spec, level)]))
    for level in sorted(bf_caster):
        add("| caster proxy (cast speed) | %d | +%.3f%% | **%.2fx** |"
            % (level, bsk, bsk / bf_caster[level]))
    add("")
    add("Berserking is throughput-linear and gear-invariant, so its")
    add("Blood Fury ratio RISES with gear exactly like Out of the")
    add("Shadows does. Context for the Strong Voodoo decision: a troll")
    add("already carries one of the game's two ceiling racials; Strong")
    add("Voodoo would stack a passive on top of it. The table above and")
    add("the one before it are the two numbers to weigh together.")
    add("")

    # ---- the rest ----
    add("## The remaining new racials")
    add("")
    add("| race | racial | level | value | x Blood Fury (basis) | valid classes note |")
    add("|---|---|---|---|---|---|")
    fury70 = bf.get(("fury warrior", 70))
    for level in (60, 70):
        prof = profiles.get(("fury warrior", level))
        if prof:
            g = pricing.flat_ap_gain_pct(prof, 20 if level == 70 else 10)
            add("| Dwarf | Hearty Appetite, AP food +50%% | %d | +%.3f%% while fed | %.2fx (fury L%d) | any dwarf melee; L60 food value half-assumed |"
                % (level, g, g / bf[("fury warrior", level)], level))
    lockp = profiles.get(("affliction warlock", 70))
    if lockp and lockp.get("spell_power") and 70 in bf_caster:
        band = pricing.sp_gain_band_pct(lockp, 11.5, SP_FRACTION)
        add("| Dwarf | Hearty Appetite, SP food +50%% | 70 | +%s while fed | %.2fx (caster proxy) | dwarf's only cloth caster is PRIEST |"
            % (fmt_band(band), band[1] / bf_caster[70]))
        for grant, name in ((20, "Outland tier +20 SP"),
                            (10, "Classic tier +10 SP")):
            band = pricing.sp_gain_band_pct(lockp, grant, SP_FRACTION)
            add("| Blood Elf | Bloodthistle, %s | 70 | +%s while active | %.2fx (caster proxy) | BE casters: paladin, priest, mage, warlock (warlock VALID for BE) |"
                % (name, fmt_band(band), band[1] / bf_caster[70]))
    haste = pricing.haste_price(1.0)
    add("| Gnome | Expansive Mind +1%% haste | any | +%s | %.2fx (fury L70) | gnome: warrior, rogue, mage, warlock, DK |"
        % (fmt_band(haste), (haste[1] / fury70) if fury70 else 0))
    add("| Gnome | Engineering bombs +20% | any | burst only; ~0 sustained without bombs | - | usage-dependent |")
    after = pricing.aftershock_price()
    add("| Tauren | Aftershock | any | +%s of GROUP damage in stomp range | %.2fx (vs one fury L70 Blood Fury - but it pays the whole group) | tauren: warrior, hunter, shaman, druid, DK |"
        % (fmt_band(after), (after[1] / fury70) if fury70 else 0))
    lw = pricing.light_within_price()
    add("| Draenei | Light Within | any | +%.2f%% ceiling (8s per 5min below 35%% health) | %.2fx (fury L70) | any draenei |"
        % (lw, (lw / fury70) if fury70 else 0))
    add("| Human | Jack of All Trades combat trickle | any | small (Master of Anatomy crit rating; value pending Spell.dbc read) | well under 0.2x | economy racial first |")
    add("| Blood Elf | Arcane Torrent | any | resource value - deferred to the mana phase | - | rogue full-energy noted as the big one |")
    add("| Troll | Regeneration | any | survivability, not DPS | - | - |")
    add("")

    # ---- crit transparency ----
    add("## Appendix - where each crit number comes from")
    add("")
    add("| profile | class base | agility -> crit | + gear equip crit | = derived | + talent pkg (measured S244) | = pricing crit |")
    add("|---|---|---|---|---|---|---|")
    for (spec, level), prof in sorted(profiles.items()):
        if prof["class_id"] not in (1, 3, 4):
            continue
        derived = prof["melee_crit_pct"]
        pkg = SPEC_TALENTS[spec]["crit_pp"]
        base = {1: 3.1891, 3: -1.5320, 4: -0.2950}[prof["class_id"]]
        equip = prof["gear_totals"].get("melee_crit_pct_equip", 0)
        agi_and_rating = derived - base - equip
        add("| %s L%d | %.2f | agi %d + rating %d -> +%.2f pp | +%.1f | %.2f%% | +%.1f | **%.1f%%** |"
            % (spec, level, base, prof["agility"], prof["crit_rating"],
               agi_and_rating, equip, derived, pkg, derived + pkg))
    add("")
    add("Derived crit = gtChanceToMeleeCritBase + agility x gtChanceToMeleeCrit")
    add("+ crit rating / gtCombatRatings + item equip-spell crit, all from")
    add("our own DBC/item_template data (pinned by tests). NOT included:")
    add("buffs (Leader of the Pack, Mongoose...), weapon-skill vs defense")
    add("depression, proc trinkets. Talent packages were the one recalled")
    add("input; MEASURED S244 from Talent.dbc + Spell.dbc rank chains, all")
    add("values confirmed (ids in tools/price_racials.py). Mortal Shots")
    add("19490 carries a second +60 aura-108 effect with an unread class")
    add("mask - flagged, not summed; resolve it when rotations arrive.")
    add("")

    add("## Reading guidance")
    add("")
    add("Berserking context: trolls already own a ~0.7-0.8x-of-Blood-Fury")
    add("racial at pre-raid 70 that scales up with gear; any Strong")
    add("Voodoo grant stacks on top of that.")
    add("")
    add("Against the original Blood Fury on the SAME profile: Out of the")
    add("Shadows is the only new racial that approaches the ceiling for a")
    add("single character, and its ratio rises with gear because Blood")
    add("Fury's flat AP dilutes as damage grows - against 024's")
    add("raid-geared Blood Fury figure it crosses 1x. Everything else")
    add("prices well under half a Blood Fury for any single recipient;")
    add("Warband Fury's group sum and Gorged's corpse-and-a-break spike")
    add("are the two that can exceed that in the right moment, which is")
    add("the stated intent (moments over stats). Two inputs are worth")
    add("firming before the group locks numbers: the crit-proc share and")
    add("the DoT shares behind Strong Voodoo - both are wowsims")
    add("reference-harvest candidates before any dummy session is spent.")
    return lines


def main():
    profiles = load_profiles()
    if not profiles:
        print("no profiles found - run tools/build_profiles.py first")
        return 1
    rc = raceclass.RaceClass.from_export(EXPORT)
    lines = price_all(profiles, rc)
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
