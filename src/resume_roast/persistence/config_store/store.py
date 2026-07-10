"""ConfigStore: file lifecycle for the config domain."""

from __future__ import annotations

from pathlib import Path

from resume_roast.persistence.config_store.models import Config
from resume_roast.persistence.config_store.parser import parse_config
from resume_roast.persistence.json_file import read_json_object, write_json_object


class ConfigStore:
    FILENAME = "config.json"

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    @property
    def path(self) -> Path:
        return self._base_dir / self.FILENAME

    def load(self) -> Config:
        if not self.path.exists():
            return Config()
        return parse_config(read_json_object(self.path))

    def save(self, config: Config) -> None:  # noqa: ARG002
        write_json_object(self.path, {})
