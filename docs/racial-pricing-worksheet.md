# Racial Pricing Worksheet - Phase 1a

**Written S243 from a full read of design 024 (kirby-server,
`docs/design/024-racial-abilities-rework.md`, the S233 revision). This is
the 1a deliverable: every racial in the pass mapped onto pricing
primitives, with a named pricing route each. The numbers land in the 1c
report; this document is the map that makes 1c mechanical.**

Units: the per-level Blood Fury yardstick (design 025 section 6;
`kb/yardstick.py`). BF grants `4*level+2` AP and `2*level+3` SP; sustained
value is the 15s/120s cycle = 12.5 percent uptime. "Percent-seconds" =
mean gain percent during the effect x its duration, per 120s cycle,
matching 024's own unit.

## Pricing primitives the tool knows

| primitive | mechanism | route |
|---|---|---|
| flat AP / SP, timed or sustained | aura 99/13 family | closed form (design 025 section 4.1 - multipliers cancel) |
| crit chance | aura 290 / rating / agility | closed form via gt tables |
| crit damage | aura 163, PATH-SPLIT (white x2 semantics vs ability/spell bonus-scaling) | closed form + engine run |
| percent damage done (own or taken) | flat multiplier | closed form (uptime x amount) |
| DoT/HoT percent | multiplier on a damage SHARE | closed form x swept share |
| expertise | dodge reduction off the attack table | closed form (1 expertise = 0.25 pp dodge; boss dodge 6.5 pp baseline) |
| hit chance | attack-table miss reduction, hard-capped | closed form, capped at the miss chance remaining |
| proc-rate scaling (crit-triggered effects) | crit chance ratio x proc damage share | closed form x swept share |
| resource return (mana/energy/runic) | resource -> damage conversion | DEFERRED to the mana phase; bounded estimate only |
| survivability / economy / utility | - | NOT DPS-PRICEABLE - listed, not numbered |

## The ten races

### 1. Night Elf - Out of the Shadows. THE HEADLINE. Route: closed form + engine run + sweep.

The racial design 025 exists because of. On leaving Shadowmeld: +15 pp
crit chance (aura 290) and +15 crit damage (aura 163), decaying a fifth
every 2s over 10s, on Shadowmeld's 120s cooldown restarted on exit.

Pricing components, per 2s window at stack s (amount `3s` for s=5..1):

- white swings: crit mult `2 * (1 + 0.03s)` (Path B, multiplier on the
  doubled damage), crit chance `c + 3s` pp.
- abilities: crit mult `1 + 1.0 * (1 + 0.03s) * (1 + t/100)` with t the
  spec's SPELLMOD_CRIT_DAMAGE_BONUS talent (Impale 20, Lethality up to 30,
  Mortal Shots 30) - talent COMPOUNDS (guide section 1).
- spells: crit mult `1 + 0.5 * (1 + 0.03s) * (1 + t/100)`.
- crit-triggered procs (Deep Wounds, Ignite): value scales with the crit
  RATE ratio `(c + 3s) / c` on the proc's damage share. SHARE IS SWEPT -
  this is the input design 025 section 4.4 flags as the wide one.
- healing crit (aura 50 in the buff): not DPS; note for resto specs.

Per-spec inputs: crit c (from profile via gt tables), white share w
(SWEPT 20-50 percent for melee), talent t (from spec), proc share p
(SWEPT 0-15 percent). 024's own table assumed Path A uniformly at 25
percent base crit with no talents and no procs - the S235 finding is that
this UNDERSTATES melee; 1c re-derives at 60 and 70.

### 2. Orc - keeps Blood Fury (the yardstick itself), loses Axe Spec, gains Warband Fury. Route: closed form.

- Removal: Axe Specialization +5 expertise = -1.25 pp boss dodge = about
  +1.34 percent melee white/ability damage (024's measured figure; only
  while axes/fists are equipped - itemization-conditional, the cage).
  Priced as a LOSS for axe users, zero for everyone else.
- Warband Fury: every group member gets `0.25 * BF` = `level+0.5` AP and
  `0.5*level+0.75` SP for the same 15s/120s. Per recipient: closed form,
  same shape as BF itself. Group value = sum over the actual roster
  (S243 roster: heavy melee+hybrid). Refresh-not-stack with two orcs.
- Note: BF's own value moves with level (design 025 section 7) - the orc
  columns in 1c must quote it per level, not inherit 70.

### 3. Undead - Gorged. Route: closed form + scenario sweep.

5 stacks after a full 10s Cannibalize channel: `2*level` AP + `level` SP
for 30s, 120s cooldown. At 70: 140 AP / 70 SP - half a BF for twice the
duration (deliberate anchor, 024 section 5.5).

The price is the CHANNEL: 10s of not attacking. Sweep the usage model:
(a) pre-pull channel, buff carries ~20-25s into the fight = the AP at
17-21 percent effective uptime, no DPS cost; (b) in-combat channel =
25 percent uptime minus ~8.3 percent of a cycle spent channelling -
usually net negative for DPS, positive only between pulls. Priced both
ways; (a) is the honest headline. Corpse availability is a scenario
assumption - state it.

### 4. Dwarf - Hearty Appetite. Route: closed form.

+50 percent on every Well Fed effect. DPS piece at 70: AP food 40 -> 60
(+20 AP sustained), spell food 23 -> 34.5 (+11.5 SP), hit food 20 -> 30
(+10 hit rating - worth 10/15.77 = 0.63 pp hit at 70, capped by
remaining miss). 024 sized it at 57 percent of BF-sustained; 1c converts
per anchor profile at 60 and 70 (the L60 food table differs - read the
L60 Well Fed spells from Spell.dbc, do not reuse 70's).
Removals: Gun Spec +1 pp ranged crit (hunters), Mace Spec +5 expertise
(melee, mace-only). Both priced as conditional losses.

### 5. Troll - Regeneration + Strong Voodoo. Route: split.

- Regeneration (12 percent max health/min in combat, 25 percent OOC):
  NOT DPS-PRICEABLE - survivability/downtime economy. Listed with a
  note: interacts with the death-has-weight pillar, not with this
  yardstick. Downtime reduction is a mana-phase-adjacent readout later.
- Strong Voodoo (+2 percent own DoTs and HoTs): closed form x DoT damage
  share, swept per VALID troll class only. **CORRECTED S243: troll
  cannot be a warlock (CharBaseInfo.dbc) - the first draft priced this
  on an affliction lock, which does not exist.** The realistic ceiling
  is a troll shadow priest (~+1 percent); rogue poisons/Rupture next;
  everything else small. Every pricing row must pass the race/class
  validity check (kb/raceclass.py, data from our own client).
- Removals: Bow/Throwing Spec +1 pp ranged crit (hunters only).
- Berserking (kept, unchanged) is noted as context in the per-race
  totals: troll hunters/casters already carry a real offensive racial.

### 6. Gnome - three small gains. Route: closed form + bounded.

- Expansive Mind +1 percent haste (aura 193, melee+ranged+cast): closed
  form ~ +1 percent throughput for any spec whose damage scales with
  speed; slightly less for fixed-cast rotations with GCD gaps - price at
  +0.8 to +1.0 percent band.
- Engineering Specialization +20 percent bomb damage: situational burst;
  bounded estimate swept on bombs-per-fight (0-2 per 60s); flagged
  usage-dependent, not sustained.
- Escape Artist -10 percent debuff duration: NOT DPS-PRICEABLE, utility.
- Intellect half of Expansive Mind: +5 percent int -> spell crit via gt
  tables for casters (already stock, unchanged - context only).

### 7. Tauren - Aftershock. Route: closed form.

War Stomp targets (up to 5, 8yd) take +10 percent damage for 6s, 120s
cd = 5 percent uptime on affected targets. Group-facing: value = 10
percent x 5 percent x (share of group damage landing on stomped targets
during the window). 024's own estimate ~0.5 percent of group damage;
1c re-derives against the S243 roster and notes the melee-range
requirement (a caster-heavy group waiting on stomp timing realizes
less). Single-target boss case: works (applied on cast, immune-proof by
design) = flat +10 percent x 5 percent = +0.5 percent group sustained.

### 8. Draenei - Light Within, loses Heroic Presence. Route: closed form, both directions.

- Loss: Heroic Presence was PARTY-WIDE +1 pp hit (physical spell 6562 /
  caster 28878). Party value: 1 pp hit per member below the miss cap -
  at 70 vs bosses (9 pp spell miss, 5.6 pp/8 pp melee) nearly always
  live value: ~1 percent damage per party member = the single largest
  REMOVAL in the pass. 1c prices the loss explicitly so the group sees
  what the removal costs, not only what replaces it.
- Gain: Light Within +10 percent damage/healing for 8s, once per 5 min,
  below 35 percent health: 8/300 = 2.7 percent uptime IF it triggers
  every cycle -> +0.27 percent sustained ceiling, realistically less.
  Priced as the bounded ceiling + the absorb noted as survivability.

### 9. Blood Elf - Bloodthistle + Arcane Torrent. Route: closed form + deferred.

- Bloodthistle: +10 SP (Classic tier) / +20 SP (Outland tier, level 55+)
  consumable while active - closed form vs caster profile SP;
  withdrawal (-5/-15 spirit) noted, negligible for DPS. Priced as a
  consumable line, not a passive: cost/availability noted.
- Arcane Torrent: mana 6->10 percent, rogue 15 energy -> FULL energy
  bar, DK 15 -> 10 percent runic. Resource-to-damage conversion is
  mana-phase work; 1c gives a bounded estimate for the rogue (100 energy
  = ~2.4 Sinister Strikes = one bounded burst per 2 min) and defers the
  mana version with a pointer. Flag: the rogue buff is LARGE in feel;
  the bounded math keeps it honest.

### 10. Human - Jack of All Trades. Route: bounded closed form + not-priceable remainder.

Third gathering profession at full strength: economy racial. DPS trickle
= the third gathering perk nobody else can have: Master of Anatomy
(Skinning) crit rating, Toughness (Mining) stamina, or Lifeblood
(Herbalism) self-heal. Priced: Master of Anatomy top reachable rank at
60 and 70 (crit rating -> pp via gt tables; rank values read from
SkillLineAbility/Spell.dbc at 1c time - do not trust memory). Perception
(track two resources) and removals (Sword/Mace Spec +3 expertise,
melee-only): expertise loss priced same shape as Orc's.

## The removals - deliberately NOT tabulated (user, S243)

The group steers by the new racials against the ORIGINAL Blood Fury -
the soft power ceiling - not by the removals, which nerf broadly
(Heroic Presence) or hit conditional cases the cage-removal rationale
already accepts (weapon specs, on classes far ahead anyway). Pricing
functions for removals stay in kb/pricing.py for the record; the report
does not print them.

## The removals, as their own table (RETIRED S243 - see above)

Balance confidence means seeing both directions. 1c's report carries a
removals table: Human -3 expertise (swords/maces), Dwarf -5 expertise
(maces) and -1 pp ranged crit (guns), Orc -5 expertise (axes), Troll
-1 pp ranged crit (bows/throwing), Draenei -1 pp party-wide hit x2
variants, Night Elf -Wisp Spirit (zero here by measurement). Weapon-spec
losses are conditional on weapon choice - the cage being removed - and
the 1c table says so per row.

## Sweep register (the inputs 1c varies instead of measuring)

| input | range | applies to |
|---|---|---|
| white damage share (melee) | 20-50 percent | Night Elf, crit pricing |
| crit-proc damage share (Deep Wounds/Ignite family) | 0-15 percent | Night Elf |
| DoT damage share | 0-90 percent by spec | Troll Strong Voodoo |
| Gorged usage model | pre-pull vs in-combat; 2-5 stacks | Undead |
| bombs per minute | 0-2 | Gnome |
| stomp-window group damage share | 30-100 percent | Tauren |
| fight length | 60-600 s | anything uptime-shaped |

## What 1b must supply

Anchor profiles (levels 60 and 70, item stats from `dev_world.item_template`
only): fury warrior (white-share worst case), combat rogue (Lethality
compounding), affliction warlock (DoT share + caster crit). These three
cover every route above that needs a profile; other roster specs reuse
the shapes with their own sweeps.
