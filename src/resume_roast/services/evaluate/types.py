"""Types owned by the evaluate service."""

from dataclasses import dataclass

from resume_roast.integrations.types import Usage
from resume_roast.prompts.evaluate.output.schema import RoastReport


@dataclass(frozen=True)
class EvaluateResult:
    """What `run()` returns: the parsed report plus accounting."""

    report: RoastReport
    usage: Usage | None
    latency_seconds: float
