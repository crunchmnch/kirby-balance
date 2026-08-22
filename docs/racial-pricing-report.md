# Racial Pricing Report - Phase 1c (S243)

**Every number here is derived from our own data or swept - no
measurement was taken.** Profiles are UNBUFFED and UNTALENTED for
stats (no gems/enchants/set bonuses/raid buffs), so absolute
percentages run a little hot versus a raid-buffed character; the
Blood Fury RATIOS are computed on the same basis top and bottom
and are the numbers to trust. Method: design 025; mechanics:
guide-combat-math.md; routes: docs/racial-pricing-worksheet.md.

Export: generated 2026-08-22T17:48:04Z, payload 7bcd81b960c440cf.

## The yardstick: Blood Fury on the anchor profiles

| profile | level | full-uptime gain | sustained (12.5% uptime) | percent-seconds/cycle |
|---|---|---|---|---|
| combat rogue | 60 | +19.38% | +2.422% | 291 |
| combat rogue | 70 | +11.59% | +1.449% | 174 |
| fury warrior | 60 | +18.45% | +2.306% | 277 |
| fury warrior | 70 | +11.70% | +1.462% | 175 |

Blood Fury moves with level and gear exactly as design 025
section 7 predicted - the unit is per-profile, and every ratio
below names the profile it is measured against.

## Night Elf - Out of the Shadows (the headline)

+15pp crit / +15 crit damage decaying over 10s per 120s
(Shadowmeld cooldown restarted on exit). White-share and
crit-proc-share are SWEPT; talent compounding applied per spec
(Impale 20, Lethality 30). Ratios vs the same profile's Blood
Fury sustained value.

| profile | level | base crit | percent-seconds (proc sweep) | sustained | x Blood Fury |
|---|---|---|---|---|---|
| combat rogue | 60 | 17.7% | 148 (122 - 171) | +1.230% | **0.51x** |
| combat rogue | 70 | 13.6% | 159 (122 - 193) | +1.329% | **0.92x** |
| fury warrior | 60 | 20.7% | 138 (117 - 157) | +1.149% | **0.50x** |
| fury warrior | 70 | 19.3% | 140 (117 - 161) | +1.167% | **0.80x** |
| caster (lock profile) | 60 | 7.3% | 51 | +0.428% | structural ~0.5x melee |
| caster (lock profile) | 70 | 12.0% | 52 | +0.435% | structural ~0.5x melee |

White-vs-ability composition moves the answer by under 2 points
across its whole range (verified: design 025 section 4.4 holds
on the real profiles). **The crit-proc share is the wide axis**
- the sweep spans are wide enough that a Deep Wounds/Ignite
share estimate per spec is the ONE measurement worth having
(the design 025 escape hatch), for: combat rogue L60 (+/-49 ps), combat rogue L70 (+/-71 ps), fury warrior L60 (+/-40 ps), fury warrior L70 (+/-45 ps).

## Orc - Warband Fury (gain) and Axe Spec (loss)

| item | level | per-recipient | notes |
|---|---|---|---|
| Warband Fury AP share | 60 | +0.576% sustained on fury warrior (69 ps) | 60 AP for 15s/120s |
| Warband Fury AP share | 60 | +0.606% sustained on combat rogue (73 ps) | 60 AP for 15s/120s |
| Warband Fury SP share | 60 | +0.64 (0.51 - 0.77)% sustained on caster | 31 SP; SP-fraction swept |
| Warband Fury AP share | 70 | +0.365% sustained on fury warrior (44 ps) | 70 AP for 15s/120s |
| Warband Fury AP share | 70 | +0.362% sustained on combat rogue (43 ps) | 70 AP for 15s/120s |
| Warband Fury SP share | 70 | +0.29 (0.23 - 0.34)% sustained on caster | 36 SP; SP-fraction swept |
| Axe Spec removal | any | -1.34% on axe users | conditional on weapon (the cage being removed) |

## Undead - Gorged

| model | level | profile | sustained | percent-seconds |
|---|---|---|---|---|
| pre-pull channel | 60 | fury warrior | +1.525% | 183 |
| in-combat channel | 60 | fury warrior | -6.046% (channel cost included) | - |
| pre-pull channel | 70 | fury warrior | +0.968% | 116 |
| in-combat channel | 70 | fury warrior | -6.882% (channel cost included) | - |

The in-combat model is net NEGATIVE for DPS - the 10s channel
costs more than the buff returns. Gorged is a between-pulls /
pre-pull racial, and honest pricing says so.

## The remaining racials, priced

| race | component | level | value | route |
|---|---|---|---|---|
| Dwarf | Hearty Appetite, AP food +50% | 60 | +0.762% sustained while fed | closed form (L60 food values half-assumed - read L60 Well Fed rows before quoting) |
| Dwarf | Hearty Appetite, AP food +50% | 70 | +0.830% sustained while fed | closed form (L60 food values half-assumed - read L60 Well Fed rows before quoting) |
| Dwarf | Hearty Appetite, SP food +50% | 70 | +0.74 (0.59 - 0.88)% while fed | closed form x SP fraction |
| Blood Elf | Bloodthistle (Outland tier, +20 SP) | 70 | +1.28 (1.02 - 1.53)% while active | consumable, not passive |
| Blood Elf | Bloodthistle (Classic tier, +10 SP) | 70 | +0.64 (0.51 - 0.77)% while active | consumable |
| Troll | Strong Voodoo, affliction lock | any | +1.50 (1.20 - 1.80)% sustained | +2% x DoT share (swept) - LARGER than it reads |
| Troll | Strong Voodoo, melee specs | any | ~0% | no DoT share to speak of |
| Troll | Regeneration | any | not DPS - survivability/downtime | not priced here |
| Gnome | Expansive Mind +1% haste | any | +0.90 (0.80 - 1.00)% | closed form |
| Gnome | Engineering bombs +20% | any | situational burst; ~0 sustained outside bomb usage | swept 0-2 bombs/min elsewhere |
| Gnome | Escape Artist -10% debuff duration | any | utility, not DPS | not priced |
| Tauren | Aftershock (group) | any | +0.33 (0.15 - 0.50)% of GROUP damage | 10% x 5% uptime x stomp-window share (swept) |
| Draenei | Light Within | any | +0.27% ceiling (once per 5min, below 35% health) | bounded ceiling |
| Draenei | Heroic Presence REMOVAL | any | about -1.09% per party member under the miss cap | the largest removal in the pass |
| Human | Jack of All Trades trickle | any | small; Master of Anatomy rank value pending a Spell.dbc read | bounded |
| Human | Sword/Mace Spec removal | any | -0.80% on sword/mace melee | conditional (the cage) |
| Dwarf | Mace Spec removal | any | -1.34% on mace melee | conditional |
| Dwarf/Troll | Gun/Bow Spec removal | any | about -0.7% ranged (1pp crit) | hunters only |
| Blood Elf | Arcane Torrent buffs | any | resource value - DEFERRED to the mana phase; rogue burst bounded elsewhere | deferred |

## Reading guidance - what the numbers actually say

**1. The yardstick moved more than the racial.** 024 priced
everything against a RAID-GEARED Blood Fury (~117 ps at 70).
On the real PRE-RAID profiles Blood Fury is worth far more
(~175 ps at 70, ~277 at 60), because a flat AP grant is
relatively bigger on a smaller damage pool. Out of the Shadows
is nearly gear- and level-invariant by construction. So at
pre-raid gear it sits BELOW Blood Fury (about 0.5x at 60,
0.8-0.9x at 70) - and its ratio RISES as gear grows. Against
024's own raid-geared Blood Fury figure (117 ps) the same
percent-seconds read ~1.2x for fury and ~1.35x for a Lethality
rogue: the S235 concern is CONFIRMED for raid gear, and the
design question is now precise - do you want a racial that
strengthens relative to the yardstick as gear improves?

**2. The sleeper is Strong Voodoo.** +2 percent on DoTs is a
passive worth ~1.5 percent sustained on an affliction lock -
about equal to Blood Fury's entire sustained value on a
pre-raid melee, always on, no button. Nothing else in the pass
gives a single spec that much passively.

**3. Gorged is two racials.** Pre-pull it is strong (183 ps at
60 - more than Out of the Shadows); mid-combat it is a trap
(net negative once the 10s channel is costed). Worth saying in
its tooltip-adjacent lore or accepting knowingly.

**4. The removals are not symmetric.** Heroic Presence is the
single largest number in either direction (about -1.1 percent
per party member); the weapon specs are conditional losses the
cage-removal rationale already accepts.

**5. What would change these numbers:** the crit-proc share
(Deep Wounds/Ignite) is the one swept input wide enough to
move a decision - the design 025 escape hatch (one target-dummy
session) applies to it and to nothing else here. This report
prices; whether a gap is acceptable stays the group's call.
