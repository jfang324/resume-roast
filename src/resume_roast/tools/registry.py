"""Tool, ToolResult, and ToolRegistry for the interview ReAct loop."""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    success: bool
    data: str = ""
    result_type: str = ""
    metadata: dict[str, Any] = field(default_factory=lambda: cast(dict[str, Any], {}))


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., ToolResult]
    parameters: dict[str, Any] | None = None
    required: list[str] = field(default_factory=lambda: cast(list[str], []))

    def system_prompt_entry(self) -> str:
        parts = [f"## Tool: {self.name}", "", self.description]
        if self.parameters:
            parts.append(f"\nInput JSON schema:\n{json.dumps(self.parameters, indent=2)}")
        return "\n".join(parts)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def execute(self, name: str, action: dict[str, Any], **context: Any) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(self._tools)
            return ToolResult(
                success=False,
                data=f"Unknown tool '{name}'. Available: {available}.",
            )
        for param in tool.required:
            if param not in action:
                return ToolResult(
                    success=False,
                    data=f"Tool '{name}' missing required parameter: {param}.",
                )
        try:
            return tool.fn(action=action, **context)
        except Exception:
            logger.exception("Tool '%s' raised", name)
            return ToolResult(
                success=False,
                data=f"Tool '{name}' encountered an internal error.",
            )

    def system_prompt_block(self) -> str:
        parts = ["## Available Tools", ""]
        parts.extend(self._tools[name].system_prompt_entry() for name in sorted(self._tools))
        parts.append("")
        parts.append('Call tools by outputting: {"tool": "<tool_name>", ...input fields}')
        return "\n".join(parts)

    @property
    def names(self) -> list[str]:
        return list(self._tools)
