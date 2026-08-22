"""kirby-balance command line runner.

Usage (from the repo root):

    py -3 sim.py scenarios\\l70-synthetic-warrior-bloodfury.json
    kb.bat scenarios\\l70-synthetic-warrior-bloodfury.json

Runs the scenario and prints a report: every input echoed, the results,
the closed-form cross-check where the comparison supports one, and the
model limitations - every time, so a number never travels without them.
"""

import json
import sys

from kb import scenario


def format_report(report):
    lines = []
    add = lines.append
    add("KIRBY-BALANCE REPORT - scenario: %s" % report["scenario"])
    add("=" * 72)
    inp = report["inputs"]
    add("export: generated %s  payload %s" % (
        inp["export_stamp"]["generated_at"],
        inp["export_stamp"]["payload_sha256"][:16]))
    add("seed %d, fight %.1f s" % (inp["seed"],
                                   inp["duration_ms"] / 1000.0))
    actor = inp["actor"]
    add("actor: class %s level %s" % (actor["class_id"], actor["level"]))
    add("  provenance: %s" % actor["provenance"])
    add("  AP %s  agi %s  crit rating %s  weapon %s-%s @ %s ms" % (
        actor["attack_power"], actor["agility"], actor["crit_rating"],
        actor["weapon_min"], actor["weapon_max"], actor["weapon_speed_ms"]))
    for aura in inp["auras"]:
        effs = ", ".join(
            "%s %+g%s" % (e["kind"], e["amount"],
                          " (%s)" % e["resolved_from"]
                          if "resolved_from" in e else "")
            for e in aura["effects"])
        timing = ("permanent" if not aura.get("period_ms")
                  else "%g s up every %g s" % (
                      aura.get("duration_ms", 0) / 1000.0,
                      aura["period_ms"] / 1000.0))
        add("aura: %s [%s] - %s" % (aura["name"], timing, effs))
    add("-" * 72)
    res = report["results"]
    add("dps %.2f   swings %d   crits %d (observed %.2f%%)" % (
        res["dps"], res["swings"], res["crits"], res["observed_crit_pct"]))
    if "comparison" in report:
        cmp_ = report["comparison"]
        add("-" * 72)
        add("comparison: without %s" % ", ".join(cmp_["removed"]))
        add("  baseline dps %.2f" % cmp_["baseline_dps"])
        add("  mean gain %.3f%%" % cmp_["gain_pct_mean"])
        if "closed_form_gain_pct_mean" in cmp_:
            add("  closed form %.3f%%  (sim - closed form = %+.3f pp)"
                % (cmp_["closed_form_gain_pct_mean"],
                   cmp_["sim_vs_closed_form_pp"]))
    add("-" * 72)
    add("MODEL LIMITATIONS (v0):")
    for lim in report["model_limitations"]:
        add("  - %s" % lim)
    return "\n".join(lines)


def main(argv):
    args = [a for a in argv[1:] if a != "--json"]
    want_json = "--json" in argv[1:]
    if len(args) != 1:
        print(__doc__)
        return 2
    try:
        doc = scenario.load(args[0])
        report = scenario.run(doc)
    except Exception as e:  # fail closed, loudly, with the reason
        print("ERROR: %s" % e)
        return 1
    print(format_report(report))
    if want_json:
        print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
