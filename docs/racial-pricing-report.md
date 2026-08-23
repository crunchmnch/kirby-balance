# Racial Pricing Report - Phase 1c v3 (S243)

**The question this report answers: how does each NEW racial
compare to the ORIGINAL Blood Fury - historically the strongest
DPS racial and this pass's soft power ceiling (user, S243).**
Removals are deliberately not tabulated: they nerf broadly and
the group does not steer by them (user, S243).

Basis: gear from the six derived pre-raid profiles (our own
item_template; no gems/enchants/set bonuses/proc trinkets), crit
INCLUDING per-spec talent packages (recalled, labelled, pending a
Talent.dbc read - see the appendix), no raid buffs. Race/class
pairs validated against CharBaseInfo.dbc - a racial is only
priced on a class that race can be.

Export: generated 2026-08-23T00:16:00Z, payload f242ab353c4647de.

## The soft ceiling: original Blood Fury on the anchor profiles

| profile | level | gain while active | sustained | percent-seconds/cycle |
|---|---|---|---|---|
| combat rogue | 60 | +19.38% | +2.422% | 291 |
| combat rogue | 70 | +11.59% | +1.449% | 174 |
| fury warrior | 60 | +18.09% | +2.261% | 271 |
| fury warrior | 70 | +11.70% | +1.462% | 175 |
| marksmanship hunter | 60 | +17.26% | +2.158% | 259 |
| marksmanship hunter | 70 | +8.64% | +1.080% | 130 |
| caster proxy (BF spell power variant) | 60 | +20.57% (mid) | +2.571% | 309 |
| caster proxy (BF spell power variant) | 70 | +9.14% (mid) | +1.143% | 137 |

Hunter note: Blood Fury 20572 grants melee AND ranged AP
(measured, design 025 section 6), so the hunter rows are the
full grant on the ranged model. Ammo and quiver haste are not
modelled - both sides of every hunter ratio share the omission.

A flat AP grant is relatively larger on a smaller damage pool,
so the ceiling itself is HIGHER at 60 and on pre-raid gear than
the raid-geared ~117 ps design 024 used. Ratios below always
name the profile they are measured against.

## Night Elf - Out of the Shadows

Valid night elf DPS: warrior, hunter, rogue, priest, druid.
Melee rows use the anchor profiles + talent packages; the
crit-proc share (Deep Wounds family) is the swept axis.

| basis | level | crit (talented) | percent-seconds (proc sweep) | sustained | x Blood Fury (same profile) |
|---|---|---|---|---|---|
| combat rogue | 60 | 22.7% | 139 (121 - 155) | +1.160% | **0.48x** |
| combat rogue | 70 | 18.6% | 146 (122 - 167) | +1.215% | **0.84x** |
| fury warrior | 60 | 29.7% | 129 (117 - 139) | +1.071% | **0.47x** |
| fury warrior | 70 | 27.3% | 130 (117 - 143) | +1.086% | **0.74x** |
| marksmanship hunter | 60 | 19.6% | 144 (122 - 163) | +1.197% | **0.55x** |
| marksmanship hunter | 70 | 16.7% | 150 (123 - 175) | +1.254% | **1.16x** |
| caster shape (gear-band proxy; NE casters are priest/druid) | 60 | 7.3% | 51 | +0.428% | structurally ~half the melee value |
| caster shape (gear-band proxy; NE casters are priest/druid) | 70 | 12.0% | 52 | +0.435% | structurally ~half the melee value |

## Orc - Warband Fury (rides Blood Fury's own press)

| recipient | level | sustained | percent-seconds | x Blood Fury (same basis) |
|---|---|---|---|---|
| fury warrior | 60 | +0.565% | 68 | 0.25x |
| combat rogue | 60 | +0.606% | 73 | 0.25x |
| marksmanship hunter | 60 | +0.540% | 65 | 0.25x |
| caster (gear-band proxy) | 60 | +0.64 (0.51 - 0.77)% | - | 0.25x |
| fury warrior | 70 | +0.365% | 44 | 0.25x |
| combat rogue | 70 | +0.362% | 43 | 0.25x |
| marksmanship hunter | 70 | +0.270% | 32 | 0.25x |
| caster (gear-band proxy) | 70 | +0.29 (0.23 - 0.34)% | - | 0.25x |

Per recipient it is a quarter-strength Blood Fury; the racial's
value is the SUM over everyone in range when the orc presses it.

## Undead - Gorged

| usage | level | sustained | percent-seconds | x Blood Fury (fury basis) |
|---|---|---|---|---|
| pre-pull channel (corpse available) | 60 | +1.495% | 179 | 0.66x |
| mid-combat channel | 60 | -6.091% net | - | negative |
| pre-pull channel (corpse available) | 70 | +0.968% | 116 | 0.66x |
| mid-combat channel | 70 | -6.882% net | - | negative |

Strong exactly when a fight allows a short break AND a corpse is
nearby - a situational spike, and that shape is the point
(user, S243). Mid-combat channelling prices net negative.

## Troll - Strong Voodoo (+2% own DoTs and HoTs)

Troll CANNOT be a warlock (CharBaseInfo.dbc) - v1 priced this on
an affliction lock and that row was wrong. Valid troll classes
with a DoT share, swept; share midpoints await the wowsims
reference harvest:

| troll class | DoT share (swept) | sustained gain | x Blood Fury (L70 basis) |
|---|---|---|---|
| shadow priest | 0.45 (0.35 - 0.60) | +0.90 (0.70 - 1.20)% | 0.79x (caster proxy) |
| rogue (poisons + Rupture) | 0.14 (0.08 - 0.20) | +0.28 (0.16 - 0.40)% | 0.19x |
| hunter (Serpent Sting) | 0.05 (0.02 - 0.08) | +0.10 (0.04 - 0.16)% | 0.09x |
| warrior (Deep Wounds + Rend) | 0.06 (0.03 - 0.10) | +0.12 (0.06 - 0.20)% | 0.08x |
| shaman (Flame Shock) | 0.05 (0.03 - 0.08) | +0.10 (0.06 - 0.16)% | 0.09x (caster proxy) |
| fire mage (Ignite ticks) | 0.05 (0.00 - 0.10) | +0.10 (0.00 - 0.20)% | 0.09x (caster proxy) |

The ceiling case is a shadow priest near +1%; every other troll
sits well under half a percent. The v1 headline ('the sleeper')
is WITHDRAWN - it rested on an impossible combo.

### Berserking - the racial trolls ALREADY own

Measured S243 from our own Spell.dbc (26297): **+20 percent
melee/ranged/cast speed, flat** (no low-health scaling in this
core's data), 10s duration, 180s cooldown.

| basis | level | Berserking sustained | x Blood Fury (same profile) |
|---|---|---|---|
| combat rogue | 60 | +1.111% | **0.46x** |
| combat rogue | 70 | +1.111% | **0.77x** |
| fury warrior | 60 | +1.111% | **0.49x** |
| fury warrior | 70 | +1.111% | **0.76x** |
| marksmanship hunter | 60 | +1.111% | **0.51x** |
| marksmanship hunter | 70 | +1.111% | **1.03x** |
| caster proxy (cast speed) | 60 | +1.111% | **0.43x** |
| caster proxy (cast speed) | 70 | +1.111% | **0.97x** |

Berserking is throughput-linear and gear-invariant, so its
Blood Fury ratio RISES with gear exactly like Out of the
Shadows does. Context for the Strong Voodoo decision: a troll
already carries one of the game's two ceiling racials; Strong
Voodoo would stack a passive on top of it. The table above and
the one before it are the two numbers to weigh together.

## The remaining new racials

| race | racial | level | value | x Blood Fury (basis) | valid classes note |
|---|---|---|---|---|---|
| Dwarf | Hearty Appetite, AP food +50% | 60 | +0.747% while fed | 0.33x (fury L60) | any dwarf melee; L60 food value half-assumed |
| Dwarf | Hearty Appetite, AP food +50% | 70 | +0.830% while fed | 0.57x (fury L70) | any dwarf melee; L60 food value half-assumed |
| Dwarf | Hearty Appetite, SP food +50% | 70 | +0.74 (0.59 - 0.88)% while fed | 0.64x (caster proxy) | dwarf's only cloth caster is PRIEST |
| Blood Elf | Bloodthistle, Outland tier +20 SP | 70 | +1.28 (1.02 - 1.53)% while active | 1.12x (caster proxy) | BE casters: paladin, priest, mage, warlock (warlock VALID for BE) |
| Blood Elf | Bloodthistle, Classic tier +10 SP | 70 | +0.64 (0.51 - 0.77)% while active | 0.56x (caster proxy) | BE casters: paladin, priest, mage, warlock (warlock VALID for BE) |
| Gnome | Expansive Mind +1% haste | any | +0.90 (0.80 - 1.00)% | 0.62x (fury L70) | gnome: warrior, rogue, mage, warlock, DK |
| Gnome | Engineering bombs +20% | any | burst only; ~0 sustained without bombs | - | usage-dependent |
| Tauren | Aftershock | any | +0.33 (0.15 - 0.50)% of GROUP damage in stomp range | 0.22x (vs one fury L70 Blood Fury - but it pays the whole group) | tauren: warrior, hunter, shaman, druid, DK |
| Draenei | Light Within | any | +0.27% ceiling (8s per 5min below 35% health) | 0.18x (fury L70) | any draenei |
| Human | Jack of All Trades combat trickle | any | small (Master of Anatomy crit rating; value pending Spell.dbc read) | well under 0.2x | economy racial first |
| Blood Elf | Arcane Torrent | any | resource value - deferred to the mana phase | - | rogue full-energy noted as the big one |
| Troll | Regeneration | any | survivability, not DPS | - | - |

## Appendix - where each crit number comes from

| profile | class base | agility -> crit | + gear equip crit | = derived | + talent pkg (recalled) | = pricing crit |
|---|---|---|---|---|---|---|
| combat rogue L60 | -0.29 | agi 338 + rating 84 -> +18.00 pp | +0.0 | 17.70% | +5.0 | **22.7%** |
| combat rogue L70 | -0.29 | agi 363 + rating 106 -> +13.88 pp | +0.0 | 13.58% | +5.0 | **18.6%** |
| fury warrior L60 | 3.19 | agi 109 + rating 182 -> +18.48 pp | +0.0 | 21.67% | +8.0 | **29.7%** |
| fury warrior L70 | 3.19 | agi 160 + rating 238 -> +16.14 pp | +0.0 | 19.33% | +8.0 | **27.3%** |
| marksmanship hunter L60 | -1.53 | agi 271 + rating 112 -> +16.16 pp | +0.0 | 14.63% | +5.0 | **19.6%** |
| marksmanship hunter L70 | -1.53 | agi 370 + rating 88 -> +13.24 pp | +0.0 | 11.70% | +5.0 | **16.7%** |

Derived crit = gtChanceToMeleeCritBase + agility x gtChanceToMeleeCrit
+ crit rating / gtCombatRatings + item equip-spell crit, all from
our own DBC/item_template data (pinned by tests). NOT included:
buffs (Leader of the Pack, Mongoose...), weapon-skill vs defense
depression, proc trinkets. Talent packages are the one recalled
input - a Talent.dbc read replaces them when rotations arrive
(Phase 3).

## Reading guidance

Berserking context: trolls already own a ~0.7-0.8x-of-Blood-Fury
racial at pre-raid 70 that scales up with gear; any Strong
Voodoo grant stacks on top of that.

Against the original Blood Fury on the SAME profile: Out of the
Shadows is the only new racial that approaches the ceiling for a
single character, and its ratio rises with gear because Blood
Fury's flat AP dilutes as damage grows - against 024's
raid-geared Blood Fury figure it crosses 1x. Everything else
prices well under half a Blood Fury for any single recipient;
Warband Fury's group sum and Gorged's corpse-and-a-break spike
are the two that can exceed that in the right moment, which is
the stated intent (moments over stats). Two inputs are worth
firming before the group locks numbers: the crit-proc share and
the DoT shares behind Strong Voodoo - both are wowsims
reference-harvest candidates before any dummy session is spent.
