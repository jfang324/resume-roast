"""Session constants for the `refine` subcommand."""

TEMPERATURE: float = 0.5

HELP: str = (
    "Available commands:\n"
    "  /replace <text>    Replace the bullet with a new version\n"
    "  /generate <notes>  Generate a candidate rewrite\n"
    "  /exit              End the session\n"
    "  /help              Show this message"
)
