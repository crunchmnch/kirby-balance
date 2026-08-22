"""The stamped data export - the only door game data enters the engine by.

ADR 012 point 8: the engine reads a generated, stamped export, never a live
database or the raw DBC directory. A scenario file plus an export stamp
yields the same answer forever; a result that no longer reproduces says so
loudly instead of silently returning a different number.

The stamp records when the export was generated, by what, from where, and a
content hash of the payload. load() recomputes the payload hash and REFUSES
an export whose stamp is missing, malformed, or does not match - fail
closed, per the project's standing rules.

The payload hash covers the canonical JSON of the payload only (sorted keys,
no whitespace), so two exports generated at different times from identical
source data carry the same payload_sha256 and are directly comparable.
"""

import hashlib
import json

SCHEMA_VERSION = 1


class ExportError(Exception):
    """Raised when an export is missing, unstamped, or fails verification."""


def payload_hash(payload):
    """Canonical content hash of an export payload (dict)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def make_export(payload, generated_at, generator, source_dir, source_files):
    """Assemble a stamped export dict ready to be written to disk.

    source_files: dict of filename -> {"bytes": int, "sha256": str} for
    every input file the payload was derived from.
    """
    return {
        "stamp": {
            "schema": SCHEMA_VERSION,
            "generated_at": generated_at,
            "generator": generator,
            "source_dir": source_dir,
            "source_files": source_files,
            "payload_sha256": payload_hash(payload),
        },
        "payload": payload,
    }


def load(path):
    """Load and verify a stamped export. Returns the full export dict.

    Refuses to return data unless the stamp parses, the schema version is
    known, and the payload hash matches the stamp.
    """
    try:
        with open(path, "r", encoding="ascii") as f:
            doc = json.load(f)
    except OSError as e:
        raise ExportError("cannot read export %s: %s" % (path, e))
    except (ValueError, UnicodeDecodeError) as e:
        raise ExportError("export %s is not valid ASCII JSON: %s" % (path, e))

    if not isinstance(doc, dict) or "stamp" not in doc or "payload" not in doc:
        raise ExportError(
            "export %s carries no stamp - refusing to run against it "
            "(ADR 012 point 8)" % path)
    stamp = doc["stamp"]
    for key in ("schema", "generated_at", "generator", "source_dir",
                "source_files", "payload_sha256"):
        if key not in stamp:
            raise ExportError(
                "export %s stamp is missing field %r - refusing"
                % (path, key))
    if stamp["schema"] != SCHEMA_VERSION:
        raise ExportError(
            "export %s has schema %r, this engine reads schema %d"
            % (path, stamp["schema"], SCHEMA_VERSION))
    actual = payload_hash(doc["payload"])
    if actual != stamp["payload_sha256"]:
        raise ExportError(
            "export %s FAILS verification: payload hash %s does not match "
            "stamp %s - the file was edited or corrupted after generation"
            % (path, actual, stamp["payload_sha256"]))
    return doc
