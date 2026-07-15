"""follow_up: generate follow-up questions based on answer quality and competency gaps."""

from .schema import FollowUpInput, FollowUpOutput
from .service import execute

__all__ = ["FollowUpInput", "FollowUpOutput", "execute"]
