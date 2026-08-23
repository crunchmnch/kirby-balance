"""Race/class validity - read from CharBaseInfo.dbc via the stamped
export, never from memory.

Added S243 after Strong Voodoo was priced on a troll warlock, a combo
that does not exist in 3.3.5 (user caught it; CharBaseInfo.dbc
confirmed). Every racial pricing row must pass validate() before a
number is printed for a (race, class) pair.
"""

from kb import export as export_mod

RACE_NAMES = {1: "Human", 2: "Orc", 3: "Dwarf", 4: "NightElf",
              5: "Undead", 6: "Tauren", 7: "Gnome", 8: "Troll",
              10: "BloodElf", 11: "Draenei"}
CLASS_NAMES = {1: "warrior", 2: "paladin", 3: "hunter", 4: "rogue",
               5: "priest", 6: "deathknight", 7: "shaman", 8: "mage",
               9: "warlock", 11: "druid"}


class RaceClassError(Exception):
    pass


class RaceClass(object):
    def __init__(self, pairs):
        self._pairs = set((int(r), int(c)) for r, c in pairs)
        if not self._pairs:
            raise RaceClassError("empty race/class table")

    @classmethod
    def from_export(cls, path):
        doc = export_mod.load(path)
        pairs = doc["payload"].get("char_base_info")
        if not pairs:
            raise RaceClassError(
                "export %s carries no char_base_info - regenerate it with "
                "tools/refresh_export.py" % path)
        return cls(pairs)

    def is_valid(self, race_id, class_id):
        return (race_id, class_id) in self._pairs

    def validate(self, race_id, class_id):
        """Fail closed on an impossible combo."""
        if not self.is_valid(race_id, class_id):
            raise RaceClassError(
                "%s cannot be a %s in 3.3.5 (CharBaseInfo.dbc)"
                % (RACE_NAMES.get(race_id, race_id),
                   CLASS_NAMES.get(class_id, class_id)))

    def classes_for(self, race_id):
        return sorted(c for (r, c) in self._pairs if r == race_id)
