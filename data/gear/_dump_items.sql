-- kirby-balance Phase 1b: item stats for the gear identity lists.
-- READ-ONLY SELECT against dev_world. Output is tab-separated.
-- Regenerated S243 (v3): + marksmanship hunter lists, + Mark of Fordring.
SELECT entry, name, Quality, ItemLevel, InventoryType, class, subclass,
       stat_type1, stat_value1, stat_type2, stat_value2, stat_type3, stat_value3, stat_type4, stat_value4, stat_type5, stat_value5, stat_type6, stat_value6, stat_type7, stat_value7, stat_type8, stat_value8, stat_type9, stat_value9, stat_type10, stat_value10,
       dmg_min1, dmg_max1, dmg_type1, delay, armor,
       spellid_1, spelltrigger_1, spellid_2, spelltrigger_2,
       spellid_3, spelltrigger_3, spellid_4, spelltrigger_4,
       spellid_5, spelltrigger_5
FROM item_template
WHERE entry IN (2100, 11662, 11726, 11766, 11815, 12640, 12927, 12930, 12939, 12940, 13098, 13340, 13386, 13396, 13400, 13959, 13965, 14153, 15062, 15063, 15411, 17713, 18323, 18372, 18375, 18407, 18421, 18473, 18500, 18735, 19107, 19165, 21670, 21869, 21870, 21871, 21995, 22002, 22003, 22004, 22005, 22008, 22009, 22061, 22232, 22267, 22268, 22329, 22339, 22340, 22403, 22433, 23311, 23522, 23537, 24250, 24259, 24262, 25685, 25686, 27474, 27683, 27797, 27801, 27837, 27846, 27874, 27981, 27985, 28134, 28189, 28224, 28227, 28228, 28264, 28275, 28288, 28315, 28438, 29151, 29172, 29246, 29247, 29273, 29349, 29350, 29370, 29379, 29381, 29383, 29527, 30038, 30040, 30279, 30538, 30834, 30860, 31077, 31149, 31332, 31920, 31986, 32053, 32087, 32494, 33173)
ORDER BY entry;
