"""Input validation and output normalization for verify."""

import json
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.tools.verify.schema import ClaimResult, VerifyInput, VerifyOutput


def parse_input(data: VerifyInput) -> VerifyInput:
    if not data.claims:
        raise ValueError("claims list cannot be empty")
    if not data.answer.strip():
        raise ValueError("answer cannot be empty")
    if not data.resume_markdown.strip():
        raise ValueError("resume_markdown cannot be empty")
    return data


def parse_output(text: str) -> VerifyOutput:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedResponseError(f"verify output is not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("verify output must be a JSON object")
    data = cast(dict[str, Any], data)
    raw_claims = data.get("claims")
    if not isinstance(raw_claims, list):
        raise MalformedResponseError("verify output must contain a 'claims' array")
    raw_list = cast(list[dict[str, Any]], raw_claims)
    results: list[ClaimResult] = []
    for i, item in enumerate(raw_list):
        text = item.get("text", "")
        if not isinstance(text, str) or not text.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            raise MalformedResponseError(f"claims[{i}].text must be a non-empty string")
        prob = item.get("probability", 0.5)
        if not isinstance(prob, (int, float)) or not 0.0 <= prob <= 1.0:
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
