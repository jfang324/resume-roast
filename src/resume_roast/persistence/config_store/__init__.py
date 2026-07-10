"""Config domain: dataclasses, parser, and store."""

from resume_roast.persistence.config_store.models import Config
from resume_roast.persistence.config_store.store import ConfigStore

__all__ = ["Config", "ConfigStore"]
