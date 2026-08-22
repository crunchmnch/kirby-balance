"""Scenario files - the committed artifact a run is described by.

ADR 012 point 5: a run is a committed file - spec, level, fight length,
auras, seed, export - so results are reproducible, diffable, and
answerable six months later. The report echoes every input (design 025,
calculator property 1) and prints the model limitations every time.

Symbolic amounts: an aura effect amount may be the string
"yardstick:blood_fury_ap" or "yardstick:blood_fury_sp" instead of a
number; it resolves through kb/yardstick.py at the actor's level. This
keeps level-scaled grants out of scenario files as transcribed constants.
"""

import json
import os

from kb import closedform, gametables, yardstick
from kb.engine import sim as sim_mod

SCHEMA_VERSION = 1

SYMBOLIC_AMOUNTS = {
    "yardstick:blood_fury_ap": yardstick.blood_fury_attack_power,
    "yardstick:blood_fury_sp": yardstick.blood_fury_spell_power,
}


class ScenarioError(Exception):
    pass


def load(path):
    """Load a scenario file. Fail closed on anything missing or unknown."""
    try:
        with open(path, "r", encoding="ascii") as f:
            doc = json.load(f)
    except OSError as e:
        raise ScenarioError("cannot read scenario %s: %s" % (path, e))
    except (ValueError, UnicodeDecodeError) as e:
        raise ScenarioError(
            "scenario %s is not valid ASCII JSON: %s" % (path, e))
    for key in ("schema", "name", "export", "seed", "duration_ms", "actor",
                "auras"):
        if key not in doc:
            raise ScenarioError(
                "scenario %s is missing field %r" % (path, key))
    if doc["schema"] != SCHEMA_VERSION:
        raise ScenarioError(
            "scenario %s has schema %r, this engine reads schema %d"
            % (path, doc["schema"], SCHEMA_VERSION))
    doc["_path"] = path
    return doc


def resolve_amounts(doc):
    """Resolve symbolic effect amounts in place, at the actor's level."""
    level = doc["actor"]["level"]
    for aura in doc["auras"]:
        for eff in aura["effects"]:
            amount = eff["amount"]
            if isinstance(amount, str):
                fn = SYMBOLIC_AMOUNTS.get(amount)
                if fn is None:
                    raise ScenarioError(
                        "unknown symbolic amount %r (known: %s)"
                        % (amount, ", ".join(sorted(SYMBOLIC_AMOUNTS))))
                eff["amount"] = fn(level)
                eff["resolved_from"] = amount


def run(doc):
    """Run a loaded scenario. Returns a dict report.

    If the scenario names auras in "compare_without", a second run without
    those auras is made on the same seed and the delta reported, with the
    closed-form expectation beside it.
    """
    resolve_amounts(doc)
    export_path = doc["export"]
    if not os.path.isabs(export_path):
        export_path = os.path.join(
            os.path.dirname(os.path.abspath(doc["_path"])), "..",
            export_path)
        export_path = os.path.normpath(export_path)
    tables = gametables.GameTables.from_export(export_path)

    schedules = sim_mod.build_schedules(doc["auras"])
    result = sim_mod.run(doc["actor"], tables, schedules,
                         doc["duration_ms"], doc["seed"])

    report = {
        "scenario": doc["name"],
        "inputs": {
            "actor": result.profile,
            "auras": doc["auras"],
            "duration_ms": doc["duration_ms"],
            "seed": doc["seed"],
            "export_stamp": {
                "generated_at": result.export_stamp["generated_at"],
                "payload_sha256": result.export_stamp["payload_sha256"],
            },
        },
        "results": {
            "dps": result.dps,
            "total_damage": result.total_damage,
            "swings": result.swings,
            "crits": result.crits,
            "observed_crit_pct": result.observed_crit_pct,
        },
        "model_limitations": list(sim_mod.MODEL_LIMITATIONS),
    }

    without = doc.get("compare_without") or []
    if without:
        for name in without:
            if not any(a["name"] == name for a in doc["auras"]):
                raise ScenarioError(
                    "compare_without names %r, which is not in auras" % name)
        base_scheds = sim_mod.build_schedules(
            [a for a in doc["auras"] if a["name"] not in without])
        base = sim_mod.run(doc["actor"], tables, base_scheds,
                           doc["duration_ms"], doc["seed"])
        gain_pct = (result.dps / base.dps - 1.0) * 100.0
        comparison = {
            "removed": list(without),
            "baseline_dps": base.dps,
            "gain_pct_mean": gain_pct,
        }
        # Closed-form cross-check for the one comparison v0 fully covers:
        # a single flat-AP aura schedule (the Blood Fury yardstick shape).
        cf = _closed_form_gain(doc, tables)
        if cf is not None:
            comparison["closed_form_gain_pct_mean"] = cf
            comparison["sim_vs_closed_form_pp"] = gain_pct - cf
        report["comparison"] = comparison
    return report


def _closed_form_gain(doc, tables):
    """Closed-form mean gain, when the compared auras are all flat AP.

    Returns None when the comparison involves effect kinds the closed form
    does not cover - reported as absent rather than wrong.
    """
    without = set(doc.get("compare_without") or [])
    actor = doc["actor"]
    extra_ap = 0.0
    uptime = None
    for aura in doc["auras"]:
        if aura["name"] not in without:
            continue
        for eff in aura["effects"]:
            if eff["kind"] != "attack_power":
                return None
            extra_ap += eff["amount"]
        sched = sim_mod.AuraSchedule(
            sim_mod.auras_mod.Aura(aura["name"], aura["effects"]),
            aura.get("duration_ms", 0), aura.get("period_ms", 0))
        u = sched.uptime_fraction(doc["duration_ms"])
        if uptime is not None and u != uptime:
            return None  # differing uptimes: closed form not implemented
        uptime = u
    if uptime is None:
        return None
    speed = actor["weapon_speed_ms"]
    crit = tables.melee_crit_percent(
        actor["class_id"], actor["level"], actor["agility"],
        actor["crit_rating"])
    dps_base = closedform.white_dps(
        actor["weapon_min"], actor["weapon_max"], actor["attack_power"],
        speed, crit)
    dps_up = closedform.white_dps(
        actor["weapon_min"], actor["weapon_max"],
        actor["attack_power"] + extra_ap, speed, crit)
    mean = closedform.uptime_weighted(dps_up, dps_base, uptime)
    return (mean / dps_base - 1.0) * 100.0
