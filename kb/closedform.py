"""Closed-form expectations - the engine's independent test oracle.

ADR 012 keeps the closed-form calculator as the cross-check for the event
engine's arithmetic: the simulation must converge to these expectations,
and a disagreement is a defect in one of the two, never a matter of taste
(guide-combat-math.md section 4).

Everything here is expectation over the v0 white-swing model: a swing
either crits or hits (no miss/dodge/parry/glancing/armor - the same
deliberate limitation the engine carries, kb/engine/damage.py).
"""

from kb import yardstick
from kb.engine import damage


class ClosedFormError(Exception):
    pass


def average_swing_damage(weapon_min, weapon_max, attack_power,
                         weapon_speed_ms):
    """Expected non-crit white swing damage.

    Weapon roll is uniform on [min, max]; attack power adds
    AP/14 * weapon_speed_seconds per swing (Unit.cpp, CalculateMinMaxDamage
    family).
    """
    if weapon_max < weapon_min:
        raise ClosedFormError("weapon_max below weapon_min")
    if weapon_speed_ms <= 0:
        raise ClosedFormError("weapon_speed_ms must be positive")
    speed_s = weapon_speed_ms / 1000.0
    return ((weapon_min + weapon_max) / 2.0
            + attack_power / yardstick.AP_PER_DPS * speed_s)


def white_dps(weapon_min, weapon_max, attack_power, weapon_speed_ms,
              crit_chance_pct, aura163_amounts=()):
    """Expected white-swing DPS under the v0 model.

    crit multiplier comes from the white path (Path B): damage doubled,
    then aura 163 applied as a multiplier product on the whole doubled
    number - kb/engine/damage.py holds the source-asserted forms.
    """
    if not 0.0 <= crit_chance_pct <= 100.0:
        raise ClosedFormError(
            "crit chance %r outside 0..100" % (crit_chance_pct,))
    avg = average_swing_damage(
        weapon_min, weapon_max, attack_power, weapon_speed_ms)
    crit_mult = damage.white_crit_multiplier(aura163_amounts)
    c = crit_chance_pct / 100.0
    expected_mult = (1.0 - c) + c * crit_mult
    return avg * expected_mult / (weapon_speed_ms / 1000.0)


def uptime_weighted(value_up, value_down, uptime_fraction):
    """Expectation over an aura window cycle: up * u + down * (1 - u)."""
    if not 0.0 <= uptime_fraction <= 1.0:
        raise ClosedFormError(
            "uptime fraction %r outside 0..1" % (uptime_fraction,))
    return value_up * uptime_fraction + value_down * (1.0 - uptime_fraction)
