"""Aura container: effects a buff contributes while it is up.

Effect kinds implemented in v0 (each names the core mechanism it models):

    attack_power        flat AP while up (aura 99 family)
    melee_crit_pct      flat percent melee crit chance while up
    crit_damage_bonus_pct   aura 163, SPELL_AURA_MOD_CRIT_DAMAGE_BONUS -
                        the Path A / Path B asymmetry lives in damage.py,
                        which is handed the LIST of active amounts because
                        the two paths aggregate differently (see there)

Aggregation is faithful to the core, not to intuition: flat kinds sum;
aura 163 is aggregated by the damage path itself since the white path
multiplies (GetTotalAuraMultiplier...) while the ability/spell paths sum
(GetTotalAuraModifier...). With one aura up the two agree; with two they
do not, and the engine must not paper over that.
"""

KNOWN_KINDS = ("attack_power", "melee_crit_pct", "crit_damage_bonus_pct")


class AuraError(Exception):
    pass


class Aura(object):
    def __init__(self, name, effects):
        """effects: list of {"kind": str, "amount": number} dicts."""
        self.name = name
        self.effects = []
        for eff in effects:
            kind = eff.get("kind")
            if kind not in KNOWN_KINDS:
                raise AuraError(
                    "aura %r has unknown effect kind %r (known: %s)"
                    % (name, kind, ", ".join(KNOWN_KINDS)))
            amount = eff.get("amount")
            if not isinstance(amount, (int, float)):
                raise AuraError(
                    "aura %r effect %r has non-numeric amount %r"
                    % (name, kind, amount))
            self.effects.append((kind, float(amount)))


class AuraContainer(object):
    def __init__(self):
        self._active = []  # list of Aura, insertion-ordered

    def apply(self, aura):
        if any(a.name == aura.name for a in self._active):
            # v0 rule: reapplying an already-active aura refreshes nothing
            # and stacks nothing - refuse so a scenario bug is loud.
            raise AuraError(
                "aura %r applied while already active - v0 does not model "
                "stacking or refresh" % aura.name)
        self._active.append(aura)

    def remove(self, name):
        for i, a in enumerate(self._active):
            if a.name == name:
                del self._active[i]
                return
        raise AuraError("aura %r removed while not active" % name)

    def is_active(self, name):
        return any(a.name == name for a in self._active)

    def flat_total(self, kind):
        """Sum of all active amounts of a flat-summing kind."""
        return sum(amount for a in self._active
                   for (k, amount) in a.effects if k == kind)

    def amounts(self, kind):
        """All active amounts of a kind, for path-specific aggregation."""
        return [amount for a in self._active
                for (k, amount) in a.effects if k == kind]
