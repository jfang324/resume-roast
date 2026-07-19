"""Output types for the verify tool."""

from dataclasses import dataclass, field
from typing import cast


@dataclass(frozen=True)
class ClaimResult:
    text: str
    probability: float
    evidence: str | None = None
    contradiction: bool = False


@dataclass(frozen=True)
class VerifyOutput:
    claims: list[ClaimResult] = field(default_factory=lambda: cast(list[ClaimResult], []))
