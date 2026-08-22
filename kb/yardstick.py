"""The Blood Fury yardstick - closed forms by level, with provenance.

PROVENANCE (do not re-derive, do not trust blindly - re-measure if Spell.dbc
changes): measured S235 by reading client/dbc-sources/patchV-Spell.dbc in the
kirby-server repo with field offsets from the core fork's DBCStructure.h, and
run through SpellEffectInfo::CalcValue (SpellInfo.cpp:409). Recorded in
docs/adr/012-balance-modelling-build-our-own.md and
docs/design/025-balance-modelling.md section 6 (kirby-server repo).

Spell 20572 (Blood Fury, the racial): BasePoints=5, DieSides=1,
RealPointsPerLevel=4.0, BaseLevel=SpellLevel=1, MaxLevel=0 (unclamped).
CalcValue: 5 + (level - 1) * 4, then DieSides=1 adds exactly +1:

    attack power = 4 * level + 2       (melee AND ranged AP - hunters too)

Spells 33697/33702 spell-power effect: BasePoints=4, DieSides=1,
RealPointsPerLevel=2.0:

    spell power = 2 * level + 3

NOTE S243: guide-combat-math.md and ADR 012 briefly carried "2 * level + 2"
for the spell power line - the DieSides +1 dropped, exactly the slip design
025 section 6 warns about. Design 025's measured table (23/43/../143/163) is
the correct one and both documents were corrected S243. The tests pin both
closed forms against that measured table.

TODO (recorded, not urgent): extract these five fields from Spell.dbc into
the stamped export so this module stops being a transcription. Until then
this docstring is the provenance tag the transcription rule requires.
"""

AP_PER_DPS = 14.0  # one DPS per 14 attack power, both paths in Unit.cpp


class YardstickError(Exception):
    pass


def _check_level(level):
    if not isinstance(level, int) or not 1 <= level <= 80:
        raise YardstickError("level %r outside 1..80" % (level,))


def blood_fury_attack_power(level):
    """AP granted by Blood Fury at the given level (spell 20572)."""
    _check_level(level)
    return 4 * level + 2


def blood_fury_spell_power(level):
    """Spell power granted by Blood Fury at the given level (33697/33702)."""
    _check_level(level)
    return 2 * level + 3


def blood_fury_gain_fraction(level, weapon_dps, attack_power):
    """Closed-form fractional white-DPS gain from Blood Fury at full uptime.

    Design 025 section 4.1: every multiplicative modifier cancels, so the
    gain is (X/14) / (weaponDPS + AP/14) with X the AP grant. Valid for the
    white-swing component of damage; ability damage shares the same AP
    coefficient family but per-ability coefficients arrive with rotations.
    """
    _check_level(level)
    if weapon_dps <= 0:
        raise YardstickError("weapon_dps must be positive")
    base = weapon_dps + attack_power / AP_PER_DPS
    return (blood_fury_attack_power(level) / AP_PER_DPS) / base
