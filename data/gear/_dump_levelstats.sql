-- kirby-balance Phase 1b: class base stats at the two gates.
-- READ-ONLY SELECT against dev_world. Output is tab-separated.
-- v3: + class 3 (hunter).
SELECT Class, Level, Strength, Agility, Stamina, Intellect, Spirit
FROM player_class_stats
WHERE Level IN (60, 70) AND Class IN (1, 3, 4, 9)
ORDER BY Class, Level;
