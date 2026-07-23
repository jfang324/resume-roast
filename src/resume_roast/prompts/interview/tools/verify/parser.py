"""Output parsing for the verify tool."""

from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.tools.verify.schema import ClaimResult, VerifyOutput
from resume_roast.prompts.response_parser import parse_first_json_object


def parse_output(text: str) -> VerifyOutput:
    """Parse the model's claims array, validating every field.

    Raises:
        MalformedResponseError: on invalid JSON or a claim that breaks the schema.
    """
    data = parse_first_json_object(text, "verify output")
    raw_claims = data.get("claims")
    if not isinstance(raw_claims, list):
        raise MalformedResponseError("verify output must contain a 'claims' array")

    raw_list = cast(list[object], raw_claims)
    results: list[ClaimResult] = []
    for i, entry in enumerate(raw_list):
        if not isinstance(entry, dict):
            raise MalformedResponseError(f"claims[{i}] must be a JSON object")

        item = cast(dict[str, Any], entry)
        text = item.get("text", "")
        if not isinstance(text, str) or not text.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            raise MalformedResponseError(f"claims[{i}].text must be a non-empty string")

        prob = item.get("probability", 0.5)
        if isinstance(prob, bool) or not isinstance(prob, (int, float)) or not 0.0 <= prob <= 1.0:
            raise MalformedResponseError(f"claims[{i}].probability must be a number 0.0-1.0")

        evidence = item.get("evidence")
        if evidence is not None and not isinstance(evidence, str):
            raise MalformedResponseError(f"claims[{i}].evidence must be a string or null")

        contradiction = bool(item.get("contradiction", False))
        results.append(
            ClaimResult(
                text=text,
                probability=float(prob),
                evidence=evidence,
                contradiction=contradiction,
            )
        )

    return VerifyOutput(claims=results)
