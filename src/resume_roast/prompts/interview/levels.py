"""Role-level answer expectations, keyed by the ``level`` setting's allowed values.

Distinct from the evaluate feature's level blocks, which calibrate a resume.
These calibrate what an *answer* can plausibly demonstrate: the competency
descriptions are written for an established IC, so scoring an intern against
them unqualified marks absent seniority as absent competence.
"""

LEVEL_CONTEXT: dict[str, str] = {
    "intern": (
        "Internship candidate (current student or recent graduate)\n\n"
        "What each competency looks like here:\n"
        "  - Ownership: noticing something is wrong and raising it, finishing what "
        "they started, asking for help at the right moment — not driving initiatives\n"
        "  - Technical competence: fundamentals explained clearly, real understanding "
        "of code they wrote themselves\n"
        "  - Problem-solving: a structured approach to a scoped problem; coursework "
        "and personal projects are valid evidence\n"
        "  - Collaboration: explaining their own contribution on a team project and "
        "responding to feedback\n\n"
        "Professional-scale experience is not expected. Its absence is not a gap."
    ),
    "junior": (
        "Junior engineer (0-2 years professional experience)\n\n"
        "What each competency looks like here:\n"
        "  - Ownership: carrying a task past its literal scope, flagging a risk, "
        "following through to production\n"
        "  - Technical competence: working effectively in a codebase they did not "
        "write; testing, debugging, code review\n"
        "  - Problem-solving: debugging unfamiliar code or an unclear bug report\n"
        "  - Collaboration: working with reviewers and asking questions that unblock "
        "them\n\n"
        "Production contribution is expected; architectural influence is not."
    ),
    "mid": (
        "Mid-level engineer (3-5 years experience)\n\n"
        "What each competency looks like here:\n"
        "  - Ownership: owning a feature area end to end and anticipating problems "
        "before they land\n"
        "  - Technical competence: depth in a domain and reasoning about trade-offs, "
        "not just tool familiarity\n"
        "  - Problem-solving: breaking down ambiguous problems and iterating\n"
        "  - Collaboration: working across functions and handling disagreement "
        "productively\n\n"
        "Independent delivery is expected; org-level influence is not."
    ),
    "senior": (
        "Senior engineer (6+ years experience)\n\n"
        "What each competency looks like here:\n"
        "  - Ownership: driving outcomes across teams and setting technical direction\n"
        "  - Technical competence: architecture, migrations, and trade-offs at system "
        "scale\n"
        "  - Problem-solving: ambiguity at the system or organizational level\n"
        "  - Collaboration: mentoring, influence without authority, and navigating "
        "conflict\n\n"
        "The competency descriptions apply in full at this level."
    ),
}


def render_level(level: str) -> str:
    """Render the role-level expectations section for `level`.

    Facts about the level only: the interviewer reads this to pitch its
    questions, and the evaluator reads it alongside its own scoring bar.
    """
    return f"## Candidate Level\n\n{LEVEL_CONTEXT[level]}"
