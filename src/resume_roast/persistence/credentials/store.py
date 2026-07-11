"""Credential persistence: `~/.resume-roast/credentials.json`."""

from pathlib import Path

from resume_roast.persistence.base_parser import Parser
from resume_roast.persistence.base_store import Store
from resume_roast.persistence.credentials.parser import CredentialsParser
from resume_roast.persistence.credentials.types import Credentials


class CredentialsStore(Store[Credentials]):
    """Loads and saves `Credentials`."""

    FILENAME = "credentials.json"

    def __init__(self, base_dir: Path, parser: Parser[Credentials] | None = None) -> None:
        super().__init__(base_dir, self.FILENAME, parser or CredentialsParser())

    def default(self) -> Credentials:
        """No credentials.json yet — nothing is configured."""
        return Credentials()
