"""Display constants for the `evaluate` subcommand."""

SPINNER_MESSAGES: list[str] = [
    "roasting your resume...",
    "summoning the resume wizard...",
    "counting the buzzwords...",
    "judging your font choices...",
    "consulting the hiring gods...",
    "searching for measurable impact...",
    "composing something devastating...",
]

DIFF_REMOVAL_PREFIX = "  - "
DIFF_ADDITION_PREFIX = "  + "
"""Line prefixes marking diff hunks; `show_report` colors lines that start with these."""

DIFF_STYLES: dict[str, str] = {
    DIFF_REMOVAL_PREFIX: "on #3a0000",
    DIFF_ADDITION_PREFIX: "on #003a00",
}
"""Full-width background colors for the removal/addition lines of a rewrite."""
