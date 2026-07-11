"""Generic parser interface every domain parser implements."""

from typing import Any, Protocol


class Parser[T](Protocol):
    """Converts between an untyped JSON object and a domain dataclass."""

    def parse(self, data: dict[str, Any]) -> T:
        """Convert a loaded JSON object into the domain type."""
        ...

    def serialize(self, value: T) -> dict[str, Any]:
        """Convert the domain type into a JSON-serializable object."""
        ...
