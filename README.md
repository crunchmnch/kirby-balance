# kirby-balance

The Kirby server's own balance model: one discrete event engine, in Python,
standard library only. Damage is the first readout; mana, tank
survivability and healing follow on the same timeline (that ordering is
decided, not aspirational).

**Governing documents live in the `kirby-server` repo and outrank this
README:** `docs/adr/012-balance-modelling-build-our-own.md` (what this is
and why we built rather than forked), `docs/design/025-balance-modelling.md`
(the derive-and-sweep method), and `docs/guide-combat-math.md` (how damage
actually computes in our core - the model implements that page, and a
disagreement between the two is a defect in one of them).

## Quickstart (from this directory)

    py -3 -m unittest discover        # 42 tests, all must pass
    kb.bat scenarios\l70-synthetic-warrior-bloodfury.json

The scenario runner prints every input alongside the results and the model
limitations every time - a number never travels without the profile that
produced it.

## Layout

    kb/                the importable engine (API first, interface last)
      dbc.py           WDBC reader, fail closed on any shape mismatch
      export.py        the stamped export contract - the only data door
      gametables.py    crit/rating lookups, indexed the way Player.cpp does
      yardstick.py     Blood Fury closed forms by level, with provenance
      closedform.py    expectation formulas - the engine's test oracle
      scenario.py      scenario files: load, resolve, run, report
      engine/
        timeline.py    integer-ms event heap, deterministic tie-break
        actor.py       profile + tables + auras -> resolved stats
        auras.py       aura container (sums flat kinds; aura 163 is
                       aggregated per damage path, see damage.py)
        damage.py      the three crit paths, asserted against source
        sim.py         wires it together; Result carries its inputs
    tools/
      refresh_export.py  regenerate data/export/gametables.json from
                         \\wsl.localhost\Ubuntu-24.04\opt\kirby\Data\dbc
                         (run on HOME; the source is the LINUX dev)
    data/export/       the stamped export, committed - a scenario plus an
                       export stamp reproduces forever
    scenarios/         committed run descriptions - the artifact
    tests/             pins: known 3.3.5 values, crit paths, oracle
                       convergence, fail-closed refusals
    sim.py, kb.bat     the command line (a thin shell; the API is the tool)

## The data contract

The engine NEVER reads the DBC directory or a database at run time. It
reads `data/export/gametables.json`, which carries a stamp: generation
time, generator, source files with hashes, and a payload hash the loader
re-verifies on every run. Regenerate with:

    py -3 tools\refresh_export.py

Two exports built from identical source data carry the same
`payload_sha256` whatever the generation time, so "did anything change?"
is one field comparison.

## Model scope (v0, S243)

White melee swings only, crit-or-hit attack table, no armor. Absolute DPS
is NOT trustworthy yet. The supported readout is the comparison in which
multipliers cancel (design 025 section 4.1) - the Blood Fury yardstick
scenario is the worked example, and the sim agrees with the closed form to
within noise.

Next, in rough order: the full white attack table (miss, dodge, parry,
glancing, armor), the gear query against `item_template` (blocked on the
per-band gear definition, design 025 P1), abilities and a rotation format,
procs (`spell_proc` semantics per guide-combat-math section 3, including
PPM and `PROC_ATTR_REDUCE_PROC_60`), then the mana readout.

## Rules inherited from the project

ASCII only in every file. Standard library only - a dependency the tool
does not have cannot rot. Fail closed: an input outside the data is an
error, never an interpolation. Every profile carries a `provenance` field
and the engine refuses one that does not say where its numbers came from.
