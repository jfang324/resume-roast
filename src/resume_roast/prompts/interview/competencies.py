"""Competency framework: the dimensions evaluated in every answer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Competency:
    id: str
    label: str
    description: str


COMPETENCIES: list[Competency] = [
    Competency(
        id="ownership",
        label="Ownership & Initiative",
        description=(
            "Drives outcomes beyond assigned tasks. Takes responsibility for "
            "results, anticipates problems, and acts without being asked."
        ),
    ),
    Competency(
        id="technical_competence",
        label="Technical Competence",
        description=(
            "Demonstrates depth of knowledge in their domain. Makes sound "
            "technical decisions, understands trade-offs, and stays current."
        ),
    ),
    Competency(
        id="problem_solving",
        label="Problem-Solving",
        description=(
            "Approaches problems with structure and creativity. Handles "
            "ambiguity, breaks down complex issues, and iterates toward solutions."
        ),
    ),
    Competency(
        id="collaboration",
        label="Collaboration & Communication",
        description=(
            "Works effectively across teams and stakeholders. Communicates "
            "clearly, handles disagreement constructively, and amplifies others."
        ),
    ),
]
