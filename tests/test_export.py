import json
import os
import tempfile
import unittest

from kb import export

EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "export", "gametables.json")


class ExportContractTests(unittest.TestCase):
    def tempfile_with(self, doc):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="ascii") as f:
            json.dump(doc, f)
        self.addCleanup(os.unlink, path)
        return path

    def test_committed_export_verifies(self):
        doc = export.load(EXPORT_PATH)
        self.assertIn("payload", doc)

    def test_refuses_missing_stamp(self):
        doc = export.load(EXPORT_PATH)
        path = self.tempfile_with({"payload": doc["payload"]})
        with self.assertRaises(export.ExportError):
            export.load(path)

    def test_refuses_tampered_payload(self):
        doc = json.loads(json.dumps(export.load(EXPORT_PATH)))
        doc["payload"]["melee_crit_base"][0] += 0.001
        path = self.tempfile_with(doc)
        with self.assertRaises(export.ExportError):
            export.load(path)

    def test_refuses_unknown_schema(self):
        doc = json.loads(json.dumps(export.load(EXPORT_PATH)))
        doc["stamp"]["schema"] = 999
        path = self.tempfile_with(doc)
        with self.assertRaises(export.ExportError):
            export.load(path)

    def test_payload_hash_is_generation_time_independent(self):
        doc = export.load(EXPORT_PATH)
        redone = export.make_export(
            doc["payload"], "2030-01-01T00:00:00Z", "elsewhere",
            "somewhere", {})
        self.assertEqual(redone["stamp"]["payload_sha256"],
                         doc["stamp"]["payload_sha256"])
