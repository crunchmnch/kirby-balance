"""Phase 1b: build derived profiles from the identity lists, the
item_template dump, base stats and Spell.dbc equip auras.

Usage (from the repo root):

    py -3 tools\\build_profiles.py
    py -3 tools\\build_profiles.py --spell-dbc "\\\\wsl.localhost\\Ubuntu-24.04\\opt\\kirby\\Data\\dbc\\Spell.dbc"

Refuses on any identity/name mismatch, reports every equip aura it
could not map, and writes data/profiles/*.json.
"""

import argparse
import json
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import gametables, profiles
from kb.spelldbc import SpellDbc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The Linux dev's extracted Spell.dbc over the WSL share - see the note in
# tools/refresh_export.py. Repointed for F295-1.
DEFAULT_SPELL_DBC = "\\\\wsl.localhost\\Ubuntu-24.04\\opt\\kirby\\Data\\dbc\\Spell.dbc"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spell-dbc", default=DEFAULT_SPELL_DBC)
    args = ap.parse_args(argv)

    gear = os.path.join(ROOT, "data", "gear")
    items = profiles.load_item_dump(os.path.join(gear, "item_dump.tsv"))
    levelstats = profiles.load_levelstats(
        os.path.join(gear, "levelstats.tsv"),
        os.path.join(gear, "racestats.tsv"))
    tables = gametables.GameTables.from_export(
        os.path.join(ROOT, "data", "export", "gametables.json"))
    sdbc = SpellDbc(args.spell_dbc)

    outdir = os.path.join(ROOT, "data", "profiles")
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    failures = 0
    for path in sorted(glob.glob(os.path.join(gear, "identity", "*.json"))):
        if path.endswith("README.json"):
            continue
        ident = profiles.load_identity(path)
        try:
            prof = profiles.build_profile(ident, items, levelstats, tables,
                                          spelldbc=sdbc)
        except profiles.ProfileError as e:
            print("FAILED: %s" % e)
            failures += 1
            continue
        out = os.path.join(outdir, os.path.basename(path))
        text = json.dumps(prof, indent=1)
        text.encode("ascii")
        with open(out, "w", encoding="ascii", newline="\n") as f:
            f.write(text)
            f.write("\n")
        w = prof["weapons"]
        print("%-24s L%d  AP %4d  crit %-6s spellcrit %-6s SP %4d  "
              "hit%% %.1f  unmapped %d" % (
                  prof["spec"], prof["level"], prof["attack_power"],
                  ("%.2f" % prof["melee_crit_pct"])
                  if prof["melee_crit_pct"] is not None else "-",
                  ("%.2f" % prof["spell_crit_pct"])
                  if prof["spell_crit_pct"] is not None else "-",
                  prof["spell_power"],
                  prof.get("hit_pct_equip", 0)
                  + prof.get("spell_hit_pct_equip", 0),
                  len(prof["equip_unmapped"])))
        for u in prof["equip_unmapped"]:
            print("    UNMAPPED equip aura: spell %d aura %d misc %r" % u)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
