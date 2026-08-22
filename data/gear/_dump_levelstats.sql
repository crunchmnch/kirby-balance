-- kirby-balance Phase 1b: class base stats at the two gates.
-- READ-ONLY SELECT against dev_world. Output is tab-separated.
-- Corrected S243: this core uses player_class_stats + player_race_stats
-- (final stat = class base + race modifier), not player_levelstats.
SELECT Class, Level, Strength, Agility, Stamina, Intellect, Spirit
FROM player_class_stats
WHERE Level IN (60, 70) AND Class IN (1, 4, 9)
ORDER BY Class, Level;
