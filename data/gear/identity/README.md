# Gear identity lists

Item IDENTITY only - which items a band is expected to wear. Stats are
NEVER taken from these files or their sources; they come from
`dev_world.item_template` via `_dump_items.sql` (ADR 012: our items will
diverge from stock, and the whole point is pricing against OURS).

Provenance per file; confidence per row where the fetch was shaky. A row
whose id fails the name/slot assertion against the dump gets corrected,
never silently trusted. Known accepted gaps, consistent across all lists
so they largely cancel in racial comparisons: no gems, no socket
bonuses, no enchants, no set bonuses (v1 profile limitation - recorded
in every profile's provenance).

Sources (fetched S243):
- L70: wowhead TBC Classic pre-raid BiS guides (user-named source).
- L60: wowhead WoW Classic pre-raid BiS guides (user allowed "any other
  resource that defines typical pre-raid gear"; wowisclassic is
  JS-rendered and not fetchable - ADR 012 already records that).
- fury-60: fetch had slot confusions; rows marked `confidence: recalled`
  were corrected from well-known classic canon and MUST pass the dump
  assertion before being quoted.
- warlock-60: three rows are random-suffix world items ("of Shadow
  Wrath"); the base item carries no stats in item_template, so those
  rows carry an `assumed_bonus` note instead.
