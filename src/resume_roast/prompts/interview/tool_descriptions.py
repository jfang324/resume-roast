"""The system-prompt block advertising the interview loop's tools.

Each tool's description lives with its prompt package; this module only
composes them, preserving the exact text the retired ToolRegistry generated.
"""

from resume_roast.prompts.interview.tools.evaluate.builder import EVALUATE_DESCRIPTION
from resume_roast.prompts.interview.tools.verify.builder import VERIFY_DESCRIPTION

TOOL_DESCRIPTIONS = "\n".join(
    [
        "## Available Tools",
        "",
        EVALUATE_DESCRIPTION,
        VERIFY_DESCRIPTION,
        "",
        'Call tools by outputting: {"tool": "<tool_name>", ...input fields}',
    ]
)
