"""The damage pipeline - crit arithmetic asserted against the core's source.

THE THREE CRIT PATHS (guide-combat-math.md section 1; source read S235,
core fork b42644b96). The same aura-163 amount means different things on
different damage:

  white melee swing   Unit.cpp:1834   damage *= 2 FIRST, then aura 163 as a
                      MULTIPLIER PRODUCT on the doubled number:
                          2.0 -> 2.0 * prod(1 + amt/100)
                      (+15 => 2.30x)
  melee/ranged ability  Unit.cpp:1553   aura 163 as a SUM scaling the crit
                      BONUS only:  bonus = damage, bonus *= (1 + sum/100)
                          2.0 -> 1 + 1.0 * (1 + sum/100)   (+15 => 2.15x)
  spell               Unit.cpp:9519   same shape, bonus = damage / 2:
                          1.5 -> 1 + 0.5 * (1 + sum/100)   (+15 => 1.575x)

Talent crit-damage modifiers (SPELLMOD_CRIT_DAMAGE_BONUS, the Impale
family) run AFTER the aura on the ability/spell paths and scale the
already-inflated bonus (Unit.cpp:1556-1565, 9522-9530) - they compound
multiplicatively with aura 163, they do not add.

RANGED white hits do not take the white path's aura-163 branch at all
(it sits in the else of a ranged test, Unit.cpp:1826-1836). Auto Shot is a
spell in this core and takes the ability path - asserted by source read
S243 (see tests and the session log).

The v0 attack table is CRIT OR HIT ONLY. No miss, dodge, parry, glancing,
armor, or weapon skill. Absolute DPS numbers are therefore NOT real yet;
comparisons that cancel multipliers (design 025 section 4.1) are the
supported readout. Every report says so.
"""

from kb import yardstick


class DamageError(Exception):
    pass


def white_crit_multiplier(aura163_amounts=()):
    """Total damage multiplier of a critical white melee swing.

    Path B: base doubling, then the aura-163 MULTIPLIER PRODUCT applied to
    the already-doubled damage.
    """
    mult = 1.0
    for amt in aura163_amounts:
        mult *= 1.0 + amt / 100.0
    return 2.0 * mult


def ability_crit_multiplier(aura163_amounts=(), talent_bonus_pct=0.0):
    """Total damage multiplier of a critical melee/ranged ability.

    Path A: crit bonus equals the damage (+100 percent base), aura 163
    scales the bonus by (1 + SUM/100), then talent SPELLMOD_CRIT_DAMAGE_BONUS
    scales the already-inflated bonus - compounding, not adding.
    """
    bonus = 1.0
    bonus *= 1.0 + sum(aura163_amounts) / 100.0
    bonus *= 1.0 + talent_bonus_pct / 100.0
    return 1.0 + bonus


def spell_crit_multiplier(aura163_amounts=(), talent_bonus_pct=0.0):
    """Total damage multiplier of a critical spell. Path A with bonus =
    damage / 2 (+50 percent base)."""
    bonus = 0.5
    bonus *= 1.0 + sum(aura163_amounts) / 100.0
    bonus *= 1.0 + talent_bonus_pct / 100.0
    return 1.0 + bonus


def roll_white_swing(rng, weapon_min, weapon_max, attack_power,
                     weapon_speed_ms, crit_chance_pct, aura163_amounts=()):
    """Resolve one white melee swing. Returns (damage, is_crit).

    Weapon roll uniform on [min, max]; AP adds AP/14 * speed_seconds.
    v0 table: crit else hit (limitation documented in the module docstring).
    """
    if weapon_max < weapon_min:
        raise DamageError("weapon_max below weapon_min")
    if not 0.0 <= crit_chance_pct <= 100.0:
        raise DamageError(
            "crit chance %r outside 0..100" % (crit_chance_pct,))
    speed_s = weapon_speed_ms / 1000.0
    dmg = (rng.uniform(weapon_min, weapon_max)
           + attack_power / yardstick.AP_PER_DPS * speed_s)
    is_crit = rng.random() < crit_chance_pct / 100.0
    if is_crit:
        dmg *= white_crit_multiplier(aura163_amounts)
    return dmg, is_crit
