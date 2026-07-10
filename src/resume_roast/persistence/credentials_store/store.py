"""CredentialsStore: file lifecycle for the credentials domain."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from resume_roast.persistence.credentials_store.models import Credentials
from resume_roast.persistence.credentials_store.parser import parse_credentials
from resume_roast.persistence.errors import InvalidSchemaError
from resume_roast.persistence.json_file import read_json_object, write_json_object


class CredentialsStore:
    FILENAME = "credentials.json"

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    @property
    def path(self) -> Path:
        return self._base_dir / self.FILENAME

    def load(self) -> Credentials | None:
        if not self.path.exists():
            return None
        data = read_json_object(self.path)
        try:
            return parse_credentials(data)
        except InvalidSchemaError as exc:
            raise InvalidSchemaError(f"{self.path}: {exc}") from exc

    def save(self, credentials: Credentials) -> None:
        existing = read_json_object(self.path) if self.path.exists() else {}
        updates = {key: value for key, value in asdict(credentials).items() if value is not None}
        write_json_object(self.path, {**existing, **updates}, secure=True)
