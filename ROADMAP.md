# kirby-balance ROADMAP

**This is the orientation document for every session that works on this
repo.** Read `CLAUDE.md` here first (the rules), then this file (the plan),
and for any phase touching combat math, the governing docs in the
`kirby-server` repo: `docs/adr/012-balance-modelling-build-our-own.md`,
`docs/design/025-balance-modelling.md`, `docs/guide-combat-math.md`.

**STANDING RULE: when a slice closes, update THIS file in the same
session** - phase status, completion-test results, and anything the slice
proved wrong. The next session reads the plan, not the log (the log lives
in kirby-server's `SESSION-LOG.md`). Appending is not correcting.

---

## The north star (user, S243)

A simulation lab the designers open when they want to know what a change
does before anyone builds it:

> Show how various classes / races / specs / gear perform at a variety of
> levels in fights of varying length. Load in known values like pre-raid
> level 60 gear, select class/race/spec, the type of fight to sim, adjust
> values - maybe an experimental gear set with never-before-used procs -
> and see what that does in a fight over time. Where did players run out
> of mana, what does the DPS curve look like, when did the tank die.

Everything below walks toward that. The engine API comes first, the
frontend last (ADR 012 point 6); the phases are ordered so each one
produces something the group can use the day it lands.

**PERFECT BALANCE IS NOT A GOAL** (design 025). The tool makes power gaps
visible before they ship; whether a gap is acceptable stays a human call.

---

## Decision inputs - recorded S243, all from the user

These answers shape the phase ordering. Do not re-ask them; do re-confirm
if the plan they imply starts to feel wrong.

1. **Gear bands (design 025 P1 - ANSWERED).** Level 40: quest rewards and
   the odd dungeon drop. Level 60: pre-raid dungeon gear - wowisclassic
   BiS lists (phase 1) are a good identity source. Level 70: pre-raid -
   wowhead's TBC pre-raid BiS guides. **Identity only: which items. Stats
   are ALWAYS read from our own `item_template`** (ADR 012) - the whole
   point of the BiS shake-up is that our items will diverge from stock.
2. **Priority specs (build rotations in roughly this order):** prot and
   fury warrior; affliction warlock; all three shaman specs; combat
   rogue; all three paladin specs; frost and arcane mage; beast mastery
   and marksmanship hunter; feral and resto druid. These see heavy play
   early. Priest, death knight and the remaining specs are deprioritized,
   not excluded.
3. **Driving milestone: the 024 racial pass.** Unpausing it outranks tool
   polish. Tool development continues afterward regardless - the lab is
   wanted for experimental simulation long term.
4. **Date pressure: SOME confidence in the racial redesign within a
   couple of days of S243.** That is Phase 1, and it is sized to be
   reachable with sweeps standing in for unbuilt engine features. No
   other date pressure known.
5. **Frontend intent:** the quoted north star above, verbatim from S243.
6. **Combat-log validation is NOT reliable** - do not build the method on
   playtester logs (they may simply never appear). Validation leans on
   the closed-form oracle, cross-checks between independent
   implementations, and the target-dummy escape hatch for cases a sweep
   flags. A log parser stays on the backlog as opportunistic, not load-
   bearing. (This amends design 025 section 5's weighting; noted there.)

---

## Phase status

| phase | name | status |
|---|---|---|
| 0 | Engine skeleton, data layer, oracle | **DONE S243** |
| 1 | Racial confidence pass (date-pressured) | **1a-1c DONE S243; 1d (the decision) with the group** |
| 2 | Real white combat (full attack table) | not started |
| 3 | Abilities, resources, rotations | not started |
| 4 | Procs as data, experimental procs | not started |
| 5 | Mana readout | not started |
| 6 | Incoming damage and tank survivability | not started |
| 7 | Fight library | not started |
| 8 | The lab frontend | not started |

Phases 2-8 are ordered by dependency, not sacredness - reorder with a
reason, and record the reason here.

---

## Phase 0 - Engine skeleton, data layer, oracle. DONE S243.

What exists: WDBC reader and stamped-export contract (fail closed); game
tables reproducing known 3.3.5 values (pinned); integer-ms deterministic
event timeline; actor/aura/white-swing pipeline with the three aura-163
crit paths asserted against source; Blood Fury yardstick with provenance;
scenario runner whose reports echo inputs and limitations; 42 tests.

Completion test, PASSED on HOME S243: full suite green, export
regenerated on HOME with identical payload hash (`7bcd81b9...`), Blood
Fury scenario reproduced bit-for-bit (sim +1.053% vs closed form +1.051%).

---

## Phase 1 - RACIAL CONFIDENCE PASS. The next work. Target: 1-3 sessions.

**Goal: re-derive design 024's comparison table (its section 11.4) with
this tool, at levels 60 and 70, well enough for the group to accept or
adjust the racial budgets. Exit is a human decision, not a build.**

The date pressure is met by the design 025 method, not by building the
full engine first: derive what the data gives, SWEEP what it does not
(white-damage share, proc damage shares), and flag any racial whose sweep
is wide enough to change a decision as the dummy-measurement candidate.

- **1a. Racial inventory.** Read 024 in full (it is long; it is the
  spec). Map each of the ten racials onto pricing primitives: flat
  AP/SP, crit chance, crit damage (aura 163 with the Path A/B split),
  flat percent, proc uptime x effect, unpriceable-by-DPS (utility).
  Name the pricing route for each: closed form / sweep / engine run /
  explicitly not DPS-priceable. **Completion: a worksheet doc in this
  repo covering all ten races with a route each; no racial silently
  skipped.**
- **1b. Real gear profiles for anchor specs.** Extend the export with
  `item_template` stats (a new export section; same stamp contract) for
  the items named by the L60 and L70 identity lists. Build profiles for
  two or three anchor specs - **fury warrior first** (largest white
  share, so the spec 024's arithmetic understated most), combat rogue
  second, one caster third. **Completion: profile files whose every item
  carries id + source-list provenance, and whose stats assert against
  `dev_world.item_template` by query.**
- **1c. The pricing run.** Price all ten racials at 60 and 70 in
  per-level Blood Fury units. Sweep underived unknowns; report each
  number WITH its sweep band. Flag wide sweeps (expected: crit-triggered
  procs - Deep Wounds family) as target-dummy candidates per design 025
  section 4.4. **Completion: a committed report re-deriving 024's table,
  every row carrying its derivation route and band; 024's own table
  corrected from it (provenance tagged, per design 025 section 9).**
- **1d. The decision (user, group).** Accept or adjust budgets; unpause
  024 or revise it. Recorded in kirby-server, not here.

**1a-1c COMPLETED S243.** Worksheet: `docs/racial-pricing-worksheet.md`.
Profiles: `data/profiles/` (six, from the S243 item_template dump, with
equip auras resolved through Spell.dbc). Report:
`docs/racial-pricing-report.md`. Headline findings: the Blood Fury
yardstick is worth FAR more on pre-raid gear than 024's raid-geared
figure, so Out of the Shadows sits below it pre-raid and overtakes it
as gear grows (the S235 concern confirmed, made precise); Strong Voodoo
is the sleeper (~1.5 percent sustained passive on affliction); Gorged
is strong pre-pull and net-negative mid-combat; Heroic Presence removal
is the largest single number in the pass. The one dummy-measurement
candidate: the crit-proc (Deep Wounds/Ignite) damage share. Known
profile gaps, recorded in the report and identity files: proc trinkets
excluded (Phase 4), Mark of Fordring stats not yet dumped, L60 Well Fed
food rows unread.

**v2 corrections (user review, S243):** race/class validity is now
enforced from CharBaseInfo.dbc via the export (v1 priced Strong Voodoo
on a troll warlock - impossible; headline withdrawn, realistic ceiling
is a troll shadow priest ~+1 percent). Crit basis now carries per-spec
talent packages (RECALLED, replace via Talent.dbc in Phase 3). Removals
are not tabulated - the report compares new racials to the original
Blood Fury ceiling only. NEXT SLICE (named, small): **the wowsims
reference harvest** - pull stock DoT-share, crit-proc-share and
composition midpoints for the priority specs from wowsims preset/report
data as GUIDANCE (design 025 section 4.5's legitimate use; ADR 012's
cross-check role), replacing the placeholder sweep midpoints with
provenance-tagged references before any dummy session is spent.

---

## Phase 2 - Real white combat

Full white attack table: miss, dodge, parry, glancing (and its damage
penalty), block on the target where relevant, armor mitigation, weapon
skill, dual wield penalty, haste. Extend the closed-form oracle in step
so sim-vs-oracle parity holds at every addition. Mechanics are read from
OUR core's source and recorded in `guide-combat-math.md` (kirby-server)
BEFORE being implemented here - the guide stays the spec, this repo
stays the implementation. **Completion: parity tests for each table
entry, and absolute white DPS declared trustworthy (the v0 limitation
line about absolute DPS is removed in the same session).**

## Phase 3 - Abilities, resources, rotations

Ability damage (Path A crits, already pinned), rage/energy/mana
generation and spending, cooldowns and GCD on the timeline, and a
committed rotation-file format (priority list first; APL only if needed -
**this is the format decision ADR 012 deliberately deferred; decide it
here with the engine in front of us and record it in this file**).
Implement the priority roster in the S243 order, DPS specs first.
**Completion per spec: a committed rotation file, sim output in plausible
family versus known references, and a test pinning its resource math.**

## Phase 4 - Procs as data

`spell_proc` semantics exactly as guide-combat-math section 3 records
them: ICD checked before the roll, flat chance vs PPM (PPM uses weapon
speed, or cast time floored at 1500 ms for spells), talent chance mods,
`PROC_ATTR_REDUCE_PROC_60` (minus one third of proc chance from 60 to
70 - directly relevant to our two gates). Plus an EXPERIMENTAL proc
definition format so never-before-used procs load as scenario data - this
is the north star's "custom item" requirement and the BiS shake-up's
tool. **Completion: PPM weapon-speed-neutrality test, ICD test,
REDUCE_PROC_60 pinned at 60/65/70, and one synthetic experimental proc
scenario running end to end.**

## Phase 5 - Mana readout

"Where did this spec run out of mana." Mana costs from the export
(per-rank Vanilla/TBC model per design 023 - OUR values, not stock),
regen per designs 022/023 (our custom regen - another reason no stock
simulator could ever answer this), the five-second rule, potions on the
2-minute TBC cooldown (locked constraint). Output becomes a timeline
series, not just a mean. **Completion: knowable cases assert against
design 022/023's measured numbers; a caster scenario reports its
oom-point and the report shows mana over time.**

## Phase 6 - Incoming damage and tank survivability

"When did the tank die." Mob/boss damage profiles from `creature`
templates plus OUR mob damage scaling (designs 005/006) via the export;
avoidance/mitigation from phase 2's table run in reverse; health pools
real on the actor (the stub finally spends). Prot warrior, prot paladin,
feral bear. **Completion: internal-consistency tests plus one in-game
spot check against a known dev mob, procedure recorded.**

## Phase 7 - Fight library

Scenario schema v2: fight archetypes beyond the stand-still patchwerk -
movement windows, target swaps, adds, burst demands, fight-length
sweeps. Timeline-series output (DPS curve over time) becomes a first-
class report artifact here if phase 5 has not already forced it.
**Completion: schema documented in this file's companion
(`docs/` in this repo), two archetypes beyond patchwerk running.**

## Phase 8 - The lab frontend

The north star screen: standard-library local web server over the engine
API (no dependencies, runs offline, forever). Select profile / race /
spec / level / fight; overlay runs; DPS curve, resource timelines, death
markers; load experimental gear and procs. Built LAST because an
interface built early gets rewritten (ADR 012). **Completion: the user
runs a comparison and reads the answer without editing JSON by hand.**

---

## Cross-cutting policies

- **Validation** (amended S243): the closed-form oracle is extended in
  every phase and parity is a standing test; independent cross-checks
  preferred; the target-dummy escape hatch is spent only where a sweep
  is wide enough to change a decision. A combat-log parser is BACKLOG,
  opportunistic - built only if real logs actually materialize.
- **The guide is the spec.** New combat mechanics are source-read and
  recorded in kirby-server's `guide-combat-math.md` before or alongside
  implementation here. Model-vs-guide disagreement is a defect in one of
  them, found and fixed, never split.
- **Every number reports its inputs and limitations.** No code path may
  emit a bare number. This held in v0; keep it holding.

## Backlog (not scheduled, not forgotten)

- Extract the Blood Fury spell fields (and future spell scaling) from
  `Spell.dbc` into the stamped export, retiring `kb/yardstick.py`'s
  transcription (its docstring carries the provenance until then).
- `close-session.ps1` (kirby-server) does not know this repo exists - it
  is not swept by the state dump and not pushed by closeout. Add it, in
  a kirby-server session.
- GitHub remote for this repo (backup + collaborator visibility).
- wowsims tolerance-band comparison (design 025 section 4.5) - deferred;
  drop it entirely if the group's gap tolerance turns out to be settled
  by taste.
- Opportunistic combat-log parser (see validation policy).
