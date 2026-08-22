import json
import os
import tempfile
import unittest

from kb import scenario, yardstick

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIO_PATH = os.path.join(
    ROOT, "scenarios", "l70-synthetic-warrior-bloodfury.json")


class ScenarioTests(unittest.TestCase):
    def test_example_scenario_loads_and_resolves(self):
        doc = scenario.load(SCENARIO_PATH)
        scenario.resolve_amounts(doc)
        eff = doc["auras"][0]["effects"][0]
        self.assertEqual(eff["amount"],
                         yardstick.blood_fury_attack_power(70))
        self.assertEqual(eff["resolved_from"], "yardstick:blood_fury_ap")

    def test_example_scenario_runs_and_cross_checks(self):
        doc = scenario.load(SCENARIO_PATH)
        # Shorten the fight for test speed; keep whole aura cycles so the
        # closed-form uptime fraction stays exact.
        doc["duration_ms"] = 40 * 120000
        report = scenario.run(doc)
        self.assertIn("comparison", report)
        cmp_ = report["comparison"]
        self.assertIn("closed_form_gain_pct_mean", cmp_)
        # The sim and the closed form must agree within noise at this
        # length (0.15 pp on a ~1 pp mean gain).
        self.assertLess(abs(cmp_["sim_vs_closed_form_pp"]), 0.15)
        # And the report must carry its inputs and its limitations.
        self.assertEqual(report["inputs"]["actor"]["level"], 70)
        self.assertTrue(report["model_limitations"])
        self.assertIn("provenance", report["inputs"]["actor"])

    def test_refuses_unknown_symbol(self):
        doc = scenario.load(SCENARIO_PATH)
        doc["auras"][0]["effects"][0]["amount"] = "yardstick:nope"
        with self.assertRaises(scenario.ScenarioError):
            scenario.resolve_amounts(doc)

    def test_refuses_missing_fields(self):
        doc = scenario.load(SCENARIO_PATH)
        del doc["seed"]
        fd, path = tempfile.mkstemp(suffix=".json", dir=os.path.join(
            ROOT, "scenarios"))
        with os.fdopen(fd, "w", encoding="ascii") as f:
            json.dump({k: v for k, v in doc.items()
                       if not k.startswith("_")}, f)
        self.addCleanup(os.unlink, path)
        with self.assertRaises(scenario.ScenarioError):
            scenario.load(path)

    def test_refuses_compare_without_unknown_aura(self):
        doc = scenario.load(SCENARIO_PATH)
        doc["compare_without"] = ["Not An Aura"]
        with self.assertRaises(scenario.ScenarioError):
            scenario.run(doc)
