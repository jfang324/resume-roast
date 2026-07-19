"""Builds the verify tool's prompt text and its model-facing result rendering."""

from resume_roast.prompts.interview.tools.verify.schema import VerifyOutput

SYSTEM = """\
You are a fact-checking assistant. Given a candidate's answer to an interview
question and their resume, evaluate each factual claim in the answer.

For each claim:
- Search the resume for supporting evidence.
- If the resume supports the claim, assign a high probability (0.8-1.0).
- If the resume contradicts the claim, assign a low probability (0.0-0.2)
  and note the contradiction.
- If the resume neither supports nor contradicts (information not present in
  the resume), assign a moderate probability (0.3-0.7) — the lack of evidence
  does not mean the claim is false.
- If the claim is a vague or soft statement that cannot be verified (e.g.
  "I think", "in my opinion"), flag it as unverifiable.

Return ONLY a JSON object with a "claims" array. Each claim object MUST have
a non-empty "text" field. Example:
{"claims": [{"text": "...", "probability": 0.9, "evidence": "...", "contradiction": false}]}"""

VERIFY_DESCRIPTION = """\
## Tool: verify

Extract key factual claims from the candidate's last answer and verify each one against their resume. Call this after the user answers.

Input JSON schema:
{
  "type": "object",
  "properties": {
    "claims": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Factual claims to verify against the resume"
    }
  },
  "required": [
    "claims"
  ]
}"""
"""How the interviewer's system prompt advertises this tool."""


def build_user_message(claims: list[str], answer: str, resume_markdown: str) -> str:
    """Lay out the resume, the answer, and the numbered claims to check."""
    numbered = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(claims))

    return f"""\
<resume>
{resume_markdown}
</resume>

Candidate answer: {answer}

Claims to verify:
{numbered}"""


def render_verify_results(output: VerifyOutput) -> str:
    """Render the verification outcome as the observation text the model reads."""
    lines = ["Verify results:"]
    for c in output.claims:
        prob = f"{c.probability:.1%}"
        flags: list[str] = []

        if c.contradiction:
            flags.append("CONTRADICTION")

        if c.evidence:
            flags.append("evidence found")
        else:
            flags.append("no resume evidence")

        flag_str = f" ({', '.join(flags)})" if flags else ""
        lines.append(f'  - "{c.text}" probability={prob}{flag_str}')

    return "\n".join(lines)
