"""Game-table lookups: crit from stats, rating conversions. Fail closed.

Data comes exclusively from a stamped export (kb/export.py), never from the
DBC directory directly - regenerate with tools/refresh_export.py.

Indexing follows the core's own code, asserted against source S235/S243:
Player::GetMeleeCritFromAgility (Player.cpp:5302) indexes the per-stat gt
tables as (class - 1) * GT_MAX_LEVEL + (level - 1). gtCombatRatings is
indexed the same way by CombatRating enum row.

The CombatRating row constants below were cross-checked S243 against known
3.3.5 values read from our own gtCombatRatings.dbc: row 8 (CR_CRIT_MELEE)
reads 14.0 rating per 1 percent at level 60 and 45.906 at 80; row 7
(CR_HIT_SPELL) reads 26.232 at 80. tests/test_gametables.py pins these.

Class id 10 does not exist in 3.3.5 (the gap between warlock 9 and druid
11). The tables carry a row for it; looking it up is refused.
"""

from kb import export as export_mod


class GameTableError(Exception):
    """Raised for any lookup outside the data, per the fail-closed rule."""


# CombatRating enum rows (AzerothCore Unit.h), the ones priced so far.
CR_HIT_MELEE = 5
CR_HIT_RANGED = 6
CR_HIT_SPELL = 7
CR_CRIT_MELEE = 8
CR_CRIT_RANGED = 9
CR_CRIT_SPELL = 10

VALID_CLASS_IDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 11)
CLASS_NAMES = {
    1: "warrior", 2: "paladin", 3: "hunter", 4: "rogue", 5: "priest",
    6: "deathknight", 7: "shaman", 8: "mage", 9: "warlock", 11: "druid",
}


class GameTables(object):
    """Lookups over the exported gt tables. Construct via from_export()."""

    def __init__(self, payload, stamp):
        self.stamp = stamp
        self.gt_max_level = payload["gt_max_level"]
        self._melee_crit_base = payload["melee_crit_base"]
        self._melee_crit_per_agi = payload["melee_crit_per_agi"]
        self._spell_crit_base = payload["spell_crit_base"]
        self._spell_crit_per_int = payload["spell_crit_per_int"]
        self._combat_ratings = payload["combat_ratings"]

    @classmethod
    def from_export(cls, path):
        doc = export_mod.load(path)
        return cls(doc["payload"], doc["stamp"])

    # -- internals ---------------------------------------------------------

    def _check_class(self, class_id):
        if class_id not in VALID_CLASS_IDS:
            raise GameTableError(
                "class id %r is not a 3.3.5 class (valid: %s)"
                % (class_id, list(VALID_CLASS_IDS)))

    def _check_level(self, level):
        if not isinstance(level, int) or not 1 <= level <= self.gt_max_level:
            raise GameTableError(
                "level %r outside game-table range 1..%d"
                % (level, self.gt_max_level))

    def _stat_row(self, table, class_id, level):
        self._check_class(class_id)
        self._check_level(level)
        return table[(class_id - 1) * self.gt_max_level + (level - 1)]

    # -- crit from stats ---------------------------------------------------

    def melee_crit_base_percent(self, class_id):
        """Base melee crit for the class, in percent (can be negative)."""
        self._check_class(class_id)
        return self._melee_crit_base[class_id - 1] * 100.0

    def melee_crit_per_agi_percent(self, class_id, level):
        """Percent melee crit granted by one point of agility."""
        ratio = self._stat_row(self._melee_crit_per_agi, class_id, level)
        if ratio <= 0.0:
            raise GameTableError(
                "melee crit per agi is %r for class %d level %d - "
                "refusing to divide by it" % (ratio, class_id, level))
        return ratio * 100.0

    def spell_crit_base_percent(self, class_id):
        self._check_class(class_id)
        return self._spell_crit_base[class_id - 1] * 100.0

    def spell_crit_per_int_percent(self, class_id, level):
        """Percent spell crit granted by one point of intellect.

        Zero for non-caster classes in the table; that zero is refused
        rather than returned, because a caller asking for a warrior's
        spell crit per intellect is asking a wrong question.
        """
        ratio = self._stat_row(self._spell_crit_per_int, class_id, level)
        if ratio <= 0.0:
            raise GameTableError(
                "spell crit per int is %r for class %d level %d - "
                "this class has no spell crit from intellect"
                % (ratio, class_id, level))
        return ratio * 100.0

    # -- combat ratings ----------------------------------------------------

    def rating_per_percent(self, cr_row, level):
        """Rating points needed for 1 percent, for a CombatRating row."""
        if not isinstance(cr_row, int) or not 0 <= cr_row < 32:
            raise GameTableError("combat rating row %r outside 0..31" % cr_row)
        self._check_level(level)
        ratio = self._combat_ratings[cr_row * self.gt_max_level + (level - 1)]
        if ratio <= 0.0:
            raise GameTableError(
                "combat rating row %d has ratio %r at level %d - refusing"
                % (cr_row, ratio, level))
        return ratio

    # -- derived character numbers ----------------------------------------

    def melee_crit_percent(self, class_id, level, agility, crit_rating=0.0):
        """Total melee crit percent from base + agility + rating.

        Matches the additive shape of Player::UpdateCritPercentage: class
        base, plus agility over the per-level conversion, plus rating over
        the per-level rating conversion. Talents and auras are the
        engine's job, not this table's.
        """
        crit = self.melee_crit_base_percent(class_id)
        crit += agility * self.melee_crit_per_agi_percent(class_id, level)
        if crit_rating:
            crit += crit_rating / self.rating_per_percent(CR_CRIT_MELEE, level)
        return crit
