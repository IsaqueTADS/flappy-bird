"""Persistent player data, separate from source code and the frozen bundle."""
import json
import os
from pathlib import Path
import tempfile


def user_data_dir():
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    return base / "FlappyBird"


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


class PlayerData:
    def __init__(self, directory=None, legacy=None):
        self.directory = Path(directory) if directory is not None else user_data_dir()
        self.record_path = self.directory / "record.json"
        self.settings_path = self.directory / "settings.json"
        record = read_json(self.record_path)
        old = read_json(Path(legacy)) if legacy else {}
        self.best = max(self.valid_score(record.get("best")), self.valid_score(old.get("best")))
        settings = read_json(self.settings_path)
        self.music = settings.get("music", True) is not False
        self.effects = settings.get("effects", True) is not False
        self.error = False
        if legacy and self.best > self.valid_score(record.get("best")):
            self.save_record(self.best)

    @staticmethod
    def valid_score(value):
        return max(0, value) if type(value) is int else 0

    def write(self, path, value):
        temporary = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.directory, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(value, stream)
            os.replace(temporary, path)
            return True
        except OSError:
            self.error = True
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def save_record(self, best):
        self.best = max(self.best, self.valid_score(best))
        return self.write(self.record_path, {"best": self.best})

    def save_settings(self, music, effects):
        self.music, self.effects = bool(music), bool(effects)
        return self.write(self.settings_path, {"music": self.music, "effects": self.effects})
