import os
import unittest

from kb import raceclass

EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "export", "gametables.json")

TROLL, ORC, NIGHTELF, HUMAN, DWARF = 8, 2, 4, 1, 3
WARRIOR, HUNTER, PRIEST, WARLOCK, MAGE, DRUID = 1, 3, 5, 9, 8, 11


class RaceClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc = raceclass.RaceClass.from_export(EXPORT_PATH)

    def test_the_troll_warlock_bug_stays_dead(self):
        # The S243 pricing bug this module exists to prevent.
        self.assertFalse(self.rc.is_valid(TROLL, WARLOCK))
        with self.assertRaises(raceclass.RaceClassError):
            self.rc.validate(TROLL, WARLOCK)

    def test_known_valid_combos(self):
        self.assertTrue(self.rc.is_valid(TROLL, PRIEST))
        self.assertTrue(self.rc.is_valid(TROLL, MAGE))
        self.assertTrue(self.rc.is_valid(ORC, WARLOCK))
        self.assertTrue(self.rc.is_valid(NIGHTELF, DRUID))

    def test_known_invalid_combos(self):
        self.assertFalse(self.rc.is_valid(HUMAN, HUNTER))   # Cata, not 3.3.5
        self.assertFalse(self.rc.is_valid(DWARF, MAGE))     # Cata
        self.assertFalse(self.rc.is_valid(NIGHTELF, MAGE))  # Cata
        self.assertFalse(self.rc.is_valid(ORC, PRIEST))

    def test_classes_for_troll(self):
        # warrior, hunter, rogue, priest, dk, shaman, mage - no warlock,
        # no paladin, no druid
        self.assertEqual(self.rc.classes_for(TROLL), [1, 3, 4, 5, 6, 7, 8])
