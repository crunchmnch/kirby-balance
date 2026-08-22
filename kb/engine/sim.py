"""The simulation: wires timeline, actor, auras and the damage pipeline
into one run, and returns a Result that carries its own inputs.

Determinism: one seeded random.Random drives every roll; equal-time events
fire in scheduling order (timeline.py). Same scenario + same export =>
same Result, forever.
"""

import random

from kb.engine import actor as actor_mod
from kb.engine import auras as auras_mod
from kb.engine import damage
from kb.engine import timeline as timeline_mod

MODEL_LIMITATIONS = (
    "v0 attack table is crit-or-hit only: no miss, dodge, parry, glancing,"
    " armor, or weapon skill",
    "white melee swings only: no abilities, rotations, procs, or resources",
    "no haste, no windfury, no dual wield",
    "absolute DPS is NOT trustworthy yet; multiplier-cancelling comparisons"
    " are the supported readout (design 025 section 4.1)",
)


class SimError(Exception):
    pass


class AuraSchedule(object):
    """An aura that applies on a cycle: up for duration_ms every period_ms.

    period_ms == 0 means permanently up from t=0. duration_ms is required
    otherwise, and must not exceed period_ms (v0 refuses overlap).
    """

    def __init__(self, aura, duration_ms, period_ms):
        if period_ms < 0 or duration_ms < 0:
            raise SimError("aura %r has negative timing" % aura.name)
        if period_ms and duration_ms == 0:
            raise SimError(
                "aura %r cycles every %d ms but has no duration"
                % (aura.name, period_ms))
        if period_ms and duration_ms > period_ms:
            raise SimError(
                "aura %r duration %d exceeds its period %d - v0 does not "
                "model overlapping reapplication"
                % (aura.name, duration_ms, period_ms))
        self.aura = aura
        self.duration_ms = duration_ms
        self.period_ms = period_ms

    def uptime_fraction(self, fight_ms):
        if self.period_ms == 0:
            return 1.0
        cycles, rem = divmod(fight_ms, self.period_ms)
        up = cycles * self.duration_ms + min(rem, self.duration_ms)
        return up / float(fight_ms)


class Result(object):
    def __init__(self, duration_ms, seed, total_damage, swings, crits,
                 profile, aura_names, stamp):
        self.duration_ms = duration_ms
        self.seed = seed
        self.total_damage = total_damage
        self.swings = swings
        self.crits = crits
        self.profile = profile          # echoed inputs, design 025 rule 1
        self.aura_names = aura_names
        self.export_stamp = stamp
        self.limitations = MODEL_LIMITATIONS

    @property
    def dps(self):
        return self.total_damage / (self.duration_ms / 1000.0)

    @property
    def observed_crit_pct(self):
        if not self.swings:
            return 0.0
        return 100.0 * self.crits / self.swings


def run(profile, tables, aura_schedules, duration_ms, seed):
    """Run one fight. Returns a Result."""
    if duration_ms <= 0:
        raise SimError("duration_ms must be positive")
    rng = random.Random(seed)
    tl = timeline_mod.Timeline()
    act = actor_mod.Actor(profile, tables)

    state = {"damage": 0.0, "swings": 0, "crits": 0}

    def apply_aura(schedule):
        def _apply():
            act.auras.apply(schedule.aura)
            tl.schedule_in(schedule.duration_ms, _remove)
        def _remove():
            act.auras.remove(schedule.aura.name)
        return _apply

    for sched in aura_schedules:
        if sched.period_ms == 0:
            act.auras.apply(sched.aura)  # permanent, up before first swing
        else:
            t = 0
            while t < duration_ms:
                tl.schedule(t, apply_aura(sched))
                t += sched.period_ms

    wmin, wmax, wspeed = act.weapon()

    def swing():
        dmg, is_crit = damage.roll_white_swing(
            rng, wmin, wmax, act.attack_power(), wspeed,
            act.melee_crit_pct(), act.aura163_amounts())
        state["damage"] += dmg
        state["swings"] += 1
        if is_crit:
            state["crits"] += 1
        tl.schedule_in(wspeed, swing)

    # First swing lands at t=0 (weapon ready at the pull), aura events at
    # t=0 were scheduled first so they resolve before it.
    tl.schedule(0, swing)
    tl.run_until(duration_ms)

    return Result(duration_ms, seed, state["damage"], state["swings"],
                  state["crits"], act.profile,
                  [s.aura.name for s in aura_schedules], tables.stamp)


def build_schedules(aura_specs):
    """Turn scenario aura dicts into AuraSchedule objects."""
    out = []
    for spec in aura_specs:
        aura = auras_mod.Aura(spec["name"], spec["effects"])
        out.append(AuraSchedule(
            aura, spec.get("duration_ms", 0), spec.get("period_ms", 0)))
    return out
