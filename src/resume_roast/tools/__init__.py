"""Tool registry: each tool registers itself so the ReAct loop can dispatch by name."""

from .registrations import register_all
from .registry import ToolRegistry

REGISTRY = ToolRegistry()
register_all(REGISTRY)
