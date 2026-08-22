-- kirby-balance Phase 1b: per-race stat modifiers.
-- READ-ONLY SELECT against dev_world. Output is tab-separated.
SELECT Race, Strength, Agility, Stamina, Intellect, Spirit
FROM player_race_stats
ORDER BY Race;
