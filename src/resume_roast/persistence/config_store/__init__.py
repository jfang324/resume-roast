"""Config domain: dataclasses, parser, and store."""

from resume_roast.persistence.config_store.models import SETTING_SPECS, Config, SettingSpec
from resume_roast.persistence.config_store.store import ConfigStore

__all__ = ["SETTING_SPECS", "Config", "ConfigStore", "SettingSpec"]
