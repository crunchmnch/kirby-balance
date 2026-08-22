"""Actor: a character's stats, resolved through the game tables and the
currently active auras.

The profile carries what a character HAS (level, class, agility, ratings,
weapon, base AP); the game tables turn stats into chances the same way
Player.cpp does; the aura container layers what is temporarily up. Health
and resource pools are stubs by intent - they exist so the mana and
survivability readouts land on this same object rather than on a rewrite
(ADR 012 point 3).
"""

from kb import gametables
from kb.engine import auras as auras_mod


class ActorError(Exception):
    pass

REQUIRED_FIELDS = (
    "class_id", "level", "provenance", "attack_power", "agility",
    "crit_rating", "weapon_min", "weapon_max", "weapon_speed_ms",
)


class Actor(object):
    def __init__(self, profile, tables):
        for field in REQUIRED_FIELDS:
            if field not in profile:
                raise ActorError(
                    "actor profile is missing %r - a profile without it is "
                    "not checkable (design 025: results must carry their "
                    "inputs)" % field)
        if not str(profile["provenance"]).strip():
            raise ActorError(
                "actor profile carries an empty provenance - say where the "
                "numbers came from, or mark them ASSUMED")
        self.profile = dict(profile)
        self.tables = tables
        self.class_id = profile["class_id"]
        self.level = profile["level"]
        self.auras = auras_mod.AuraContainer()
        # Pools: present so later readouts extend rather than rewrite.
        self.health = None
        self.mana = None
        # Fail closed NOW on a class/level outside the tables, not at the
        # first swing three minutes into a run.
        tables.melee_crit_percent(
            self.class_id, self.level, profile["agility"],
            profile["crit_rating"])

    # -- resolved stats (base + auras) ------------------------------------

    def attack_power(self):
        return (self.profile["attack_power"]
                + self.auras.flat_total("attack_power"))

    def melee_crit_pct(self):
        crit = self.tables.melee_crit_percent(
            self.class_id, self.level,
            self.profile["agility"], self.profile["crit_rating"])
        crit += self.auras.flat_total("melee_crit_pct")
        # Chance is clamped, never allowed negative or above certain.
        return max(0.0, min(100.0, crit))

    def aura163_amounts(self):
        return self.auras.amounts("crit_damage_bonus_pct")

    def weapon(self):
        p = self.profile
        return p["weapon_min"], p["weapon_max"], p["weapon_speed_ms"]
