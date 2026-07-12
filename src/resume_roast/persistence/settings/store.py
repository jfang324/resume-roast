"""Settings persistence: `~/.resume-roast/settings.json`."""

from pathlib import Path

from resume_roast.persistence.base_store import Store
from resume_roast.persistence.json_parser import JsonParser
from resume_roast.persistence.settings.parser import SettingsParser
from resume_roast.persistence.settings.types import Settings


class SettingsStore(Store[Settings]):
    """Loads and saves `Settings`."""

    FILENAME = "settings.json"

    def __init__(self, base_dir: Path, parser: JsonParser[Settings] | None = None) -> None:
        super().__init__(base_dir, self.FILENAME, parser or SettingsParser())

    def default(self) -> Settings:
        """No settings.json yet — every setting takes its default."""
        return Settings()
