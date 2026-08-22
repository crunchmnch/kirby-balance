# CLAUDE.md - kirby-balance

The Kirby server's balance model. Separate repo by decision (ADR 012 in
`D:\Projects\kirby-server`); it has its own lifecycle and tests, and no
reason to share the server repo's history. The server repo's `CLAUDE.md`
governs anything touching servers, databases or machines; this file
governs work inside this repo.

## Hard rules

- **ASCII ONLY in everything written to disk.** Same rule, same reason,
  same verification as the server repo: read the file back directly and
  check the lines you added; `-` not em-dashes, `'`/`"` not curly quotes,
  `->` not arrows.
- **Standard library only.** A dependency the tool does not have cannot
  rot, and the tool must still run in ten years. The pattern is
  `client/mpq_read.py` in the server repo.
- **Fail closed, everywhere.** A class id outside 3.3.5, a level outside
  the tables, a zero conversion ratio, an unstamped export, a profile
  without provenance - all errors, never interpolations or defaults. A
  check that cannot fail reads identically to one that passes.
- **The engine reads the stamped export only** (`kb/export.py`), never a
  DBC directory or a database at run time. Regeneration is
  `tools/refresh_export.py`, run on HOME where `D:\Server\dev\Data\dbc`
  exists. The payload hash is generation-time independent by design.
- **Scenario files are the artifact** - a run is a committed file, and
  every report echoes its inputs and prints the model limitations. Do not
  add a code path that outputs a number without them.
- **`docs/guide-combat-math.md` (server repo) is the mechanics spec.**
  The model implements what that page says; when the two disagree, one of
  them is defective - find which, fix it, and update the other. Never
  split the difference.
- **Tests pin measured values, not wishes.** `tests/test_gametables.py`
  carries the S243 P2 assertion (known 3.3.5 crit values); the yardstick
  tests carry design 025 section 6's measured Blood Fury table. If a pin
  fails after regenerating the export, the DATA changed - check the stamp
  before touching the pin.
- **Claude does not run git write operations** - hand commands over.
- **No transcribed game constants without a provenance tag.** The one
  deliberate exception so far is `kb/yardstick.py` (Blood Fury closed
  forms), whose docstring carries the measurement provenance and the TODO
  to extract the spell fields into the export.

## Running

    py -3 -m unittest discover                      # all tests
    kb.bat scenarios\<scenario>.json                # one run
    py -3 tools\refresh_export.py                   # regenerate export

## Session logging

This repo keeps no session log. Work here is recorded in the server
repo's `SESSION-LOG.md` entry for the session, per that repo's checklist.
