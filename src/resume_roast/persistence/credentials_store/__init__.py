"""Credentials domain: dataclasses, parser, and store."""

from resume_roast.persistence.credentials_store.models import (
    CREDENTIAL_SPECS,
    Credentials,
    CredentialSpec,
    mask_secret,
)
from resume_roast.persistence.credentials_store.store import CredentialsStore

__all__ = [
    "CREDENTIAL_SPECS",
    "CredentialSpec",
    "Credentials",
    "CredentialsStore",
    "mask_secret",
]
