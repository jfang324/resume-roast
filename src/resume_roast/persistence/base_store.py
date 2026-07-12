"""Generic JSON-backed store: shared file I/O for every persistence domain."""

import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, cast

from resume_roast.persistence.base_parser import Parser
from resume_roast.persistence.errors import InvalidJsonError, InvalidSchemaError, PersistenceError

_OWNER_ONLY_FILE_MODE = 0o600
_OWNER_ONLY_DIR_MODE = 0o700


class Store[T](ABC):
    """Base class for JSON-backed stores.

    Subclasses supply a filename, an injected `Parser[T]`, and a `default()`
    value returned by `load()` when the backing file doesn't exist yet. All
    file mechanics (reading, JSON decoding, atomic writes, permissions) live
    here exactly once; subclasses never touch `json` or the filesystem.

    Every store file is written owner-only (0600, best-effort on Windows).
    """

    def __init__(self, base_dir: Path, filename: str, parser: Parser[T]) -> None:
        self._base_dir = base_dir
        self._filename = filename
        self._parser = parser

    @property
    def path(self) -> Path:
        """The full path to this store's backing file."""
        return self._base_dir / self._filename

    @abstractmethod
    def default(self) -> T:
        """Value `load()` returns when the backing file doesn't exist yet."""

    def load(self) -> T:
        """Load and parse the backing file, or return `default()`."""
        if not self.path.exists():
            return self.default()
        data = self._read_json()
        try:
            return self._parser.parse(data)
        except InvalidSchemaError as exc:
            # Parsers operate on dicts and don't know the file; add it here.
            raise InvalidSchemaError(f"{self.path}: {exc}") from exc

    def load_or_create(self) -> T:
        """Like `load()`, but first materialize `default()` on disk when the
        backing file doesn't exist yet.
        """
        if self.path.exists():
            return self.load()
        value = self.default()
        self.save(value)
        return value

    def save(self, value: T) -> None:
        """Serialize and atomically write `value` to the backing file."""
        self._write_json(self._parser.serialize(value))

    def _read_json(self) -> dict[str, Any]:
        """Read `path` and decode it as a JSON object."""
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PersistenceError(f"Could not read {self.path}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise InvalidJsonError(f"{self.path} is not valid JSON") from exc

        if not isinstance(data, dict):
            raise InvalidSchemaError(f"{self.path} must contain a JSON object")

        return cast(dict[str, Any], data)

    def _write_json(self, data: dict[str, Any]) -> None:
        """Write `data` to `path`, creating `base_dir` if needed."""
        try:
            self._base_dir.mkdir(mode=_OWNER_ONLY_DIR_MODE, parents=True, exist_ok=True)
            self._swap_into_place(data)
        except OSError as exc:
            raise PersistenceError(f"Could not write {self.path}") from exc

    def _swap_into_place(self, data: dict[str, Any]) -> None:
        """Write `data` to a sibling temp file, then atomically rename it onto `path`."""
        fd, tmp_name = tempfile.mkstemp(
            dir=self._base_dir, prefix=f".{self._filename}.", suffix=".tmp"
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            # mkstemp already creates the file 0600; the explicit chmod makes
            # owner-only a contract of every store, not an mkstemp side effect.
            tmp_path.chmod(_OWNER_ONLY_FILE_MODE)
            os.replace(tmp_path, self.path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
