"""Regenerate data/export/gametables.json from the server's gt*.dbc files.

Usage (from the repo root):

    py -3 tools\\refresh_export.py
    py -3 tools\\refresh_export.py --dbc-dir "D:\\Server\\dev\\Data\\dbc" --out data\\export\\gametables.json

Reads the six gt* game tables the engine needs, validates their shapes
(fail closed), and writes a stamped export per kb/export.py. Two exports
generated from identical source data carry the same payload_sha256, so a
regeneration can be compared to the committed export by that one field.

Standard library only. ASCII only.
"""

import argparse
import datetime
import hashlib
import json
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb import dbc, export

GT_MAX_LEVEL = 100
NUM_CLASS_ROWS = 11        # class ids 1..11; 10 is the unused gap in 3.3.5
NUM_RATING_ROWS = 32

DEFAULT_DBC_DIR = "D:\\Server\\dev\\Data\\dbc"
DEFAULT_OUT = os.path.join("data", "export", "gametables.json")

SOURCES = {
    "gtChanceToMeleeCrit.dbc": ("melee_crit_per_agi", NUM_CLASS_ROWS * GT_MAX_LEVEL),
    "gtChanceToMeleeCritBase.dbc": ("melee_crit_base", NUM_CLASS_ROWS),
    "gtChanceToSpellCrit.dbc": ("spell_crit_per_int", NUM_CLASS_ROWS * GT_MAX_LEVEL),
    "gtChanceToSpellCritBase.dbc": ("spell_crit_base", NUM_CLASS_ROWS),
    "gtCombatRatings.dbc": ("combat_ratings", NUM_RATING_ROWS * GT_MAX_LEVEL),
}
PAIR_SOURCE = "gtOCTClassCombatRatingScalar.dbc"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dbc-dir", default=DEFAULT_DBC_DIR,
                    help="directory holding the gt*.dbc files "
                         "(default: %(default)s)")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="output path (default: %(default)s)")
    args = ap.parse_args(argv)

    payload = {
        "gt_max_level": GT_MAX_LEVEL,
        "num_class_rows": NUM_CLASS_ROWS,
        "num_rating_rows": NUM_RATING_ROWS,
    }
    source_files = {}

    for filename, (key, expect) in sorted(SOURCES.items()):
        path = os.path.join(args.dbc_dir, filename)
        payload[key] = dbc.read_float_column(path, expect_records=expect)
        source_files[filename] = {
            "bytes": os.path.getsize(path),
            "sha256": sha256_file(path),
        }

    path = os.path.join(args.dbc_dir, PAIR_SOURCE)
    payload["oct_class_combat_rating_scalar"] = [
        list(pair) for pair in dbc.read_index_float_pairs(path)]
    source_files[PAIR_SOURCE] = {
        "bytes": os.path.getsize(path),
        "sha256": sha256_file(path),
    }

    generated_at = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    generator = "tools/refresh_export.py on host %s" % socket.gethostname()
    doc = export.make_export(
        payload, generated_at, generator, args.dbc_dir, source_files)

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    text = json.dumps(doc, sort_keys=True, indent=1)
    text.encode("ascii")  # refuse to write non-ASCII, per the standing rule
    with open(args.out, "w", encoding="ascii", newline="\n") as f:
        f.write(text)
        f.write("\n")

    # Prove the round trip before claiming success: load() re-verifies the
    # payload hash from disk, so a truncated or mangled write fails here.
    export.load(args.out)
    print("wrote %s" % args.out)
    print("payload_sha256 %s" % doc["stamp"]["payload_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
