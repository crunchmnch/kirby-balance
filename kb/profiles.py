"""Derived gear profiles: identity lists + item_template dump + level
stats -> the numbers the pricing needs, with every input asserted.

AP formulas asserted from source S243 (StatSystem.cpp:395-401):
  warrior/paladin/DK melee AP = 3*level + 2*str - 20
  rogue/hunter/shaman melee AP = 2*level + str + agi - 20
  warlock and other casters carry no melee AP worth modelling here.

Fail-closed rules: every identity row must find its item in the dump AND
match its name (case-insensitive); a mismatch anywhere refuses the build
and reports EVERY mismatch at once, so one round of fixes suffices.
Random-suffix items (marked in the identity file note) are allowed to
carry zero stats - the base row is what our DB has.

v1 limitations, carried into every profile's provenance: no gems, no
socket bonuses, no enchants, no set bonuses, no buffs/talent stats.
Consistent across races, so racial comparisons mostly cancel them.
"""

import json

from kb import gametables
from kb import spelldbc as spelldbc_mod

# 3.3.5 ItemModType -> profile bucket (subset the pricing consumes)
ITEM_MOD = {
    3: "agility", 4: "strength", 5: "intellect", 6: "spirit", 7: "stamina",
    31: "hit_rating", 32: "crit_rating", 36: "haste_rating",
    37: "expertise_rating", 38: "attack_power", 44: "armor_pen_rating",
    41: "spell_healing_done", 42: "spell_damage_done", 45: "spell_power",
    43: "mp5",
}

SPEC_CLASS = {
    "fury warrior": 1,
    "combat rogue": 4,
    "affliction warlock": 9,
}

INVTYPE_WEAPON = {13, 17, 21, 22}  # 1h, 2h, mainhand, offhand weapons
INVTYPE_RANGED = {15, 25, 26, 28}


class ProfileError(Exception):
    pass


def parse_tsv(path):
    """Parse a mysql tab-separated dump (header row + data rows)."""
    with open(path, "r", encoding="ascii") as f:
        lines = [ln.rstrip("\r\n") for ln in f if ln.strip()]
    if not lines:
        raise ProfileError("%s is empty" % path)
    header = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        vals = ln.split("\t")
        if len(vals) != len(header):
            raise ProfileError(
                "%s: row has %d fields, header has %d: %r"
                % (path, len(vals), len(header), ln[:80]))
        rows.append(dict(zip(header, vals)))
    return rows


def load_item_dump(path):
    out = {}
    for row in parse_tsv(path):
        entry = int(row["entry"])
        stats = {}
        for i in range(1, 11):
            t = int(row.get("stat_type%d" % i) or 0)
            v = int(row.get("stat_value%d" % i) or 0)
            if t and v:
                key = ITEM_MOD.get(t, "unmapped_%d" % t)
                stats[key] = stats.get(key, 0) + v
        out[entry] = {
            "name": row["name"],
            "quality": int(row["Quality"]),
            "item_level": int(row["ItemLevel"]),
            "inventory_type": int(row["InventoryType"]),
            "stats": stats,
            "dmg_min": float(row["dmg_min1"] or 0),
            "dmg_max": float(row["dmg_max1"] or 0),
            "delay_ms": int(row["delay"] or 0),
            "spells": [
                (int(row.get("spellid_%d" % i) or 0),
                 int(row.get("spelltrigger_%d" % i) or 0))
                for i in range(1, 6)
                if int(row.get("spellid_%d" % i) or 0)],
        }
    return out


def load_levelstats(class_stats_path, race_stats_path):
    """Base stats per (race, class, level): this core computes final base
    stat as player_class_stats base + player_race_stats race modifier
    (asserted S243 against the local AzerothCore wiki, after
    player_levelstats turned out not to exist here)."""
    class_rows = {}
    for row in parse_tsv(class_stats_path):
        class_rows[(int(row["Class"]), int(row["Level"]))] = row
    race_rows = {}
    for row in parse_tsv(race_stats_path):
        race_rows[int(row["Race"])] = row
    out = {}
    for (class_id, level), c in class_rows.items():
        for race_id, r in race_rows.items():
            out[(race_id, class_id, level)] = {
                "str": int(c["Strength"]) + int(r["Strength"]),
                "agi": int(c["Agility"]) + int(r["Agility"]),
                "sta": int(c["Stamina"]) + int(r["Stamina"]),
                "int": int(c["Intellect"]) + int(r["Intellect"]),
                "spi": int(c["Spirit"]) + int(r["Spirit"]),
            }
    return out


def verify_identity(identity, items):
    """Return a list of mismatch strings; empty means clean."""
    problems = []
    for it in identity["items"]:
        if it.get("confidence") == "omitted-s243":
            continue  # recorded, bounded omission - not in the dump yet
        entry = items.get(it["id"])
        if entry is None:
            problems.append("id %d (%s, %s): NOT IN DUMP - id is wrong or "
                            "item absent from dev_world"
                            % (it["id"], it["slot"], it["name"]))
            continue
        if entry["name"].strip().lower() != it["name"].strip().lower():
            problems.append(
                "id %d (%s): identity says %r, item_template says %r"
                % (it["id"], it["slot"], it["name"], entry["name"]))
    return problems


ON_EQUIP_TRIGGER = 1


def build_profile(identity, items, levelstats, tables, race_id=2,
                  race_name="orc", spelldbc=None):
    """Build a derived profile dict. Refuses on any identity mismatch."""
    problems = verify_identity(identity, items)
    if problems:
        raise ProfileError(
            "identity %s failed verification:\n  %s"
            % (identity["spec"], "\n  ".join(problems)))

    spec = identity["spec"]
    level = identity["level"]
    class_id = SPEC_CLASS.get(spec)
    if class_id is None:
        raise ProfileError("unknown spec %r" % spec)
    base = levelstats.get((race_id, class_id, level))
    if base is None:
        raise ProfileError(
            "no player_levelstats row for race %d class %d level %d"
            % (race_id, class_id, level))

    totals = {}
    weapons = {}
    omitted = []
    equip_unmapped = []
    equip_skipped = []
    for it in identity["items"]:
        if it.get("confidence") == "omitted-s243":
            omitted.append("%s (%s)" % (it["name"], it["slot"]))
            continue
        entry = items[it["id"]]
        for k, v in entry["stats"].items():
            totals[k] = totals.get(k, 0) + v
        for spell_id, trigger in entry.get("spells", ()):
            if trigger != ON_EQUIP_TRIGGER:
                continue
            if spelldbc is None:
                equip_skipped.append((it["id"], spell_id))
                continue
            buckets, unmapped = spelldbc_mod.resolve_equip_auras(
                spelldbc, spell_id)
            for k, v in buckets.items():
                totals[k] = totals.get(k, 0) + v
            equip_unmapped.extend(unmapped)
        if it["slot"] in ("main_hand", "off_hand") and entry["delay_ms"]:
            weapons[it["slot"]] = {
                "name": entry["name"],
                "dmg_min": entry["dmg_min"], "dmg_max": entry["dmg_max"],
                "delay_ms": entry["delay_ms"],
                "dps": ((entry["dmg_min"] + entry["dmg_max"]) / 2.0)
                       / (entry["delay_ms"] / 1000.0),
            }

    strength = base["str"] + totals.get("strength", 0)
    agility = base["agi"] + totals.get("agility", 0)
    intellect = base["int"] + totals.get("intellect", 0)

    if class_id == 1:
        attack_power = (3 * level + 2 * strength - 20
                        + totals.get("attack_power", 0))
    elif class_id == 4:
        attack_power = (2 * level + strength + agility - 20
                        + totals.get("attack_power", 0))
    else:
        attack_power = totals.get("attack_power", 0)

    crit_rating = totals.get("crit_rating", 0)
    if class_id in (1, 4):
        melee_crit = tables.melee_crit_percent(
            class_id, level, agility, crit_rating)
        melee_crit += totals.get("melee_crit_pct_equip", 0)
    else:
        melee_crit = None
    spell_crit = None
    if class_id == 9:
        # same shape as melee: base + int * per-int + rating
        spell_crit = (tables.spell_crit_base_percent(class_id)
                      + intellect * tables.spell_crit_per_int_percent(
                          class_id, level)
                      + crit_rating / tables.rating_per_percent(
                          gametables.CR_CRIT_SPELL, level))
        spell_crit += totals.get("spell_crit_pct_equip", 0)

    # school-specific +damage (e.g. Frozen Shadoweave's shadow/frost) is
    # fully live for a spec of that school - counted, and recorded apart
    # so a cross-school reuse of the profile can subtract it.
    spell_power = (totals.get("spell_power", 0)
                   + totals.get("spell_damage_done", 0)
                   + totals.get("spell_power_school", 0))

    return {
        "spec": spec, "level": level, "class_id": class_id,
        "race": race_name, "race_id": race_id,
        "provenance": ("DERIVED S243: identity %s; stats from "
                       "dev_world.item_template dump; base stats from "
                       "player_levelstats; AP formula asserted "
                       "StatSystem.cpp:395-401. v1 limitations: no gems/"
                       "sockets/enchants/set bonuses/buffs/talent stats."
                       % identity.get("source", "?")),
        "base_stats": base,
        "gear_totals": totals,
        "strength": strength, "agility": agility, "intellect": intellect,
        "attack_power": attack_power,
        "crit_rating": crit_rating,
        "melee_crit_pct": melee_crit,
        "spell_crit_pct": spell_crit,
        "spell_power": spell_power,
        "omitted_items": omitted,
        "equip_unmapped": equip_unmapped,
        "equip_spells_skipped_no_dbc": equip_skipped,
        "hit_pct_equip": totals.get("hit_pct_equip", 0),
        "spell_hit_pct_equip": totals.get("spell_hit_pct_equip", 0),
        "hit_rating": totals.get("hit_rating", 0),
        "haste_rating": totals.get("haste_rating", 0),
        "expertise_rating": totals.get("expertise_rating", 0),
        "weapons": weapons,
    }


def load_identity(path):
    with open(path, "r", encoding="ascii") as f:
        return json.load(f)
