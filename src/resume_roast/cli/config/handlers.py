"""`config` subcommand group: bare handler functions, wired by the registry."""

from resume_roast.cli.config.logic import apply_entries, apply_selections
from resume_roast.cli.config.utils import (
    confirm_saved,
    confirm_settings,
    prompt_for_entries,
    prompt_for_selections,
)
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore


def credentials() -> None:
    """Prompt for every registered provider's API key and save them.

    A blank entry keeps the existing value for that provider.
    """
    store = CredentialsStore(storage_dir())
    existing = store.load()
    updated = apply_entries(existing, prompt_for_entries(existing))
    store.save(updated)
    confirm_saved(updated, store.path)


def settings() -> None:
    """Choose each setting from its allowed values and save them.

    A blank entry keeps the current value.
    """
    store = SettingsStore(storage_dir())
    existing = store.load()
    updated = apply_selections(existing, prompt_for_selections(existing))
    store.save(updated)
    confirm_settings(updated, store.path)
