import json
from pathlib import Path
import tempfile
import unittest

from storage import PlayerData


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_record_survives_restart_and_does_not_decrease(self):
        data = PlayerData(self.directory)
        self.assertTrue(data.save_record(24))
        self.assertTrue(data.save_record(3))
        self.assertEqual(PlayerData(self.directory).best, 24)

    def test_imports_existing_record_without_destroying_it(self):
        legacy = self.directory / "old.json"
        legacy.write_text('{"best": 35}', encoding="utf-8")
        data = PlayerData(self.directory / "new", legacy=legacy)
        self.assertEqual(data.best, 35)
        self.assertEqual(PlayerData(data.directory).best, 35)
        self.assertEqual(json.loads(legacy.read_text())["best"], 35)

    def test_preferences_survive_restart(self):
        PlayerData(self.directory).save_settings(False, True)
        data = PlayerData(self.directory)
        self.assertFalse(data.music)
        self.assertTrue(data.effects)

    def test_corrupt_or_invalid_records_are_ignored(self):
        for contents in ('{broken', '[]', '{"best": true}', '{"best": "42"}', '{"best": -10}'):
            (self.directory / "record.json").write_text(contents, encoding="utf-8")
            self.assertEqual(PlayerData(self.directory).best, 0)

    def test_write_failure_is_reported_without_crashing(self):
        blocked = self.directory / "file"
        blocked.write_text("not a directory", encoding="utf-8")
        data = PlayerData(blocked)
        self.assertFalse(data.save_record(12))
        self.assertTrue(data.error)
