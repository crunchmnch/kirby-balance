"""Targeted Spell.dbc reader - numeric fields only, for resolving item
equip auras (and later, spell scaling) without a running server.

Field indices asserted S243 against the core fork's own
src/server/shared/DataStores/DBCStructure.h (SpellEntry, 234 fields):
Effect 71-73, EffectDieSides 74-76, EffectRealPointsPerLevel 77-79,
EffectBasePoints 80-82, EffectApplyAuraName 95-97, EffectMiscValue
110-112, SchoolMask 225. The reader self-validates against Blood Fury
20572 (BasePoints 5, DieSides 1, PerLevel 4.0, aura 99) - the values
design 025 section 6 measured - and refuses to serve data if that spell
does not read back correctly.

Value convention (SpellEffectInfo::CalcValue): the granted amount of a
non-level-scaled equip aura is BasePoints + 1 when DieSides is 1,
BasePoints when DieSides is 0. Level-scaled spells additionally add
int((level - max(BaseLevel, SpellLevel)) * RealPointsPerLevel) - full
CalcValue support arrives when spell scaling moves into the export.
"""

import struct

SPELL_ENTRY_FIELDS = 234

F_ID = 0
F_MAXLEVEL, F_BASELEVEL, F_SPELLLEVEL = 37, 38, 39
F_EFFECT = 71          # 3 slots
F_DIESIDES = 74
F_PERLEVEL = 77
F_BASEPOINTS = 80
F_AURANAME = 95
F_MISCVALUE = 110
F_SCHOOLMASK = 225

EFFECT_APPLY_AURA = 6

# SPELL_AURA_* ids this module maps (AzerothCore SpellAuraDefines.h)
AURA_MOD_DAMAGE_DONE = 13
AURA_MOD_CRIT_PERCENT = 52
AURA_MOD_HIT_CHANCE = 54
AURA_MOD_SPELL_HIT_CHANCE = 55
AURA_MOD_SPELL_CRIT_CHANCE = 57
AURA_MOD_POWER_REGEN = 85
AURA_MOD_ATTACK_POWER = 99
AURA_MOD_RANGED_ATTACK_POWER = 124
AURA_MOD_HEALING_DONE = 135
AURA_MOD_RATING = 189

SCHOOL_MASK_PHYSICAL = 0x01
SCHOOL_MASK_ALL_MAGIC = 0x7E


class SpellDbcError(Exception):
    pass


class SpellDbc(object):
    """Random access to numeric SpellEntry fields by spell id."""

    def __init__(self, path):
        with open(path, "rb") as f:
            data = f.read()
        magic, nrec, nfield, recsize, strsize = struct.unpack_from(
            "<4sIIII", data, 0)
        if magic != b"WDBC":
            raise SpellDbcError("%s: not a WDBC file" % path)
        if nfield != SPELL_ENTRY_FIELDS or recsize != SPELL_ENTRY_FIELDS * 4:
            raise SpellDbcError(
                "%s: %d fields x record size %d does not match the 3.3.5 "
                "SpellEntry layout (234 fields) this reader was asserted "
                "against" % (path, nfield, recsize))
        self._body = data[20:20 + nrec * recsize]
        self._recsize = recsize
        self._index = {}
        for i in range(nrec):
            (spell_id,) = struct.unpack_from("<I", self._body, i * recsize)
            self._index[spell_id] = i
        self._self_validate(path)

    def _self_validate(self, path):
        bf = self.effects(20572)
        if not bf:
            raise SpellDbcError("%s: Blood Fury 20572 missing" % path)
        e0 = bf[0]
        if not (e0["base_points"] == 5 and e0["die_sides"] == 1
                and abs(e0["per_level"] - 4.0) < 1e-6
                and e0["aura"] == AURA_MOD_ATTACK_POWER):
            raise SpellDbcError(
                "%s: Blood Fury 20572 reads %r - field offsets are wrong, "
                "refusing to serve data" % (path, e0))

    def _u32(self, rec, field):
        (v,) = struct.unpack_from("<I", self._body,
                                  rec * self._recsize + field * 4)
        return v

    def _i32(self, rec, field):
        (v,) = struct.unpack_from("<i", self._body,
                                  rec * self._recsize + field * 4)
        return v

    def _f32(self, rec, field):
        (v,) = struct.unpack_from("<f", self._body,
                                  rec * self._recsize + field * 4)
        return v

    def has(self, spell_id):
        return spell_id in self._index

    def effects(self, spell_id):
        """The three effect slots of a spell, raw numeric fields."""
        rec = self._index.get(spell_id)
        if rec is None:
            return []
        out = []
        for slot in range(3):
            eff = self._u32(rec, F_EFFECT + slot)
            if not eff:
                continue
            out.append({
                "effect": eff,
                "aura": self._u32(rec, F_AURANAME + slot),
                "base_points": self._i32(rec, F_BASEPOINTS + slot),
                "die_sides": self._i32(rec, F_DIESIDES + slot),
                "per_level": self._f32(rec, F_PERLEVEL + slot),
                "misc_value": self._i32(rec, F_MISCVALUE + slot),
                "school_mask": self._u32(rec, F_SCHOOLMASK),
            })
        return out

    @staticmethod
    def flat_value(effect):
        """Granted amount for a non-level-scaled effect (see module doc)."""
        v = effect["base_points"]
        if effect["die_sides"] == 1:
            v += 1
        return v


def resolve_equip_auras(spelldbc, spell_id):
    """Map one on-equip spell into profile stat buckets.

    Returns (buckets, unmapped): buckets is {bucket: amount}; unmapped
    lists aura ids seen but not handled, so nothing disappears silently.
    """
    buckets = {}
    unmapped = []
    for eff in spelldbc.effects(spell_id):
        if eff["effect"] != EFFECT_APPLY_AURA:
            continue
        amt = SpellDbc.flat_value(eff)
        aura = eff["aura"]
        if aura == AURA_MOD_DAMAGE_DONE:
            mask = eff["misc_value"] & 0xFF
            if mask == SCHOOL_MASK_PHYSICAL:
                continue  # physical damage-done items: not modelled yet
            key = ("spell_power" if (mask & SCHOOL_MASK_ALL_MAGIC)
                   == SCHOOL_MASK_ALL_MAGIC else "spell_power_school")
            buckets[key] = buckets.get(key, 0) + amt
        elif aura == AURA_MOD_HEALING_DONE:
            buckets["spell_healing_done"] = (
                buckets.get("spell_healing_done", 0) + amt)
        elif aura == AURA_MOD_CRIT_PERCENT:
            buckets["melee_crit_pct_equip"] = (
                buckets.get("melee_crit_pct_equip", 0) + amt)
        elif aura == AURA_MOD_SPELL_CRIT_CHANCE:
            buckets["spell_crit_pct_equip"] = (
                buckets.get("spell_crit_pct_equip", 0) + amt)
        elif aura == AURA_MOD_HIT_CHANCE:
            buckets["hit_pct_equip"] = buckets.get("hit_pct_equip", 0) + amt
        elif aura == AURA_MOD_SPELL_HIT_CHANCE:
            buckets["spell_hit_pct_equip"] = (
                buckets.get("spell_hit_pct_equip", 0) + amt)
        elif aura == AURA_MOD_ATTACK_POWER:
            buckets["attack_power"] = buckets.get("attack_power", 0) + amt
        elif aura == AURA_MOD_RANGED_ATTACK_POWER:
            buckets["ranged_attack_power"] = (
                buckets.get("ranged_attack_power", 0) + amt)
        elif aura == AURA_MOD_POWER_REGEN:
            buckets["mp5_equip"] = buckets.get("mp5_equip", 0) + amt
        elif aura == AURA_MOD_RATING:
            # misc is a CombatRating bit mask; split evenly is WRONG, so
            # only map single-bit masks and report the rest unmapped.
            mask = eff["misc_value"]
            bit_to_bucket = {1 << 5: "hit_rating", 1 << 6: "hit_rating",
                             1 << 7: "hit_rating", 1 << 8: "crit_rating",
                             1 << 9: "crit_rating", 1 << 10: "crit_rating",
                             # combined masks 3.3.5 converted old items to
                             # (measured S243: spell 7597 = crit mask 1792)
                             0x700: "crit_rating",   # all three crit bits
                             0x0E0: "hit_rating",    # all three hit bits
                             0x300: "crit_rating",   # melee+ranged crit
                             0x060: "hit_rating"}    # melee+ranged hit
            if mask in bit_to_bucket:
                buckets[bit_to_bucket[mask]] = (
                    buckets.get(bit_to_bucket[mask], 0) + amt)
            else:
                unmapped.append((spell_id, aura, mask))
        else:
            unmapped.append((spell_id, aura, eff["misc_value"]))
    return buckets, unmapped
