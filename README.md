[![PyPI Version](https://img.shields.io/pypi/v/resume-roast)](https://pypi.org/project/resume-roast/)
![Python Versions](https://img.shields.io/pypi/pyversions/resume-roast)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/resume-roast?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/resume-roast)
[![License](https://img.shields.io/github/license/jfang324/resume-roast)](https://github.com/jfang324/resume-roast/blob/main/LICENSE)
[![CI](https://github.com/jfang324/resume-roast/actions/workflows/ci.yaml/badge.svg)](https://github.com/jfang324/resume-roast/actions/workflows/ci.yaml)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

# Resume Roast

A terminal-based LLM-powered resume coaching tool. Get brutal, structured feedback on your resume, refine individual bullet points through back-and-forth chat, or generate new resume blocks from scratch.

## Features

- **`evaluate`** — Submit a PDF resume and receive a structured roast: per-category scores, highlighted strengths and weaknesses, and concrete rewrite suggestions with before/after examples
- **`interview`** — Agentic behavioral interview that asks resume-tailored questions, fact-checks answers against your resume, and scores them across ownership, technical competence, problem-solving, and collaboration
- **`refine`** — Interactive chat that coaches a single resume bullet, rating it on every turn and suggesting improvements
- **`generate-block`** — Chat-based interviewer that gathers details about a role or project, then generates a formatted resume block rated against our bullet-writing principles
- Multiple LLM models to choose from, with per-session token usage and cost reporting
- Configurable persona (recruiter, hiring manager, senior engineer) and level (intern through senior) for evaluations

## Getting Started

### Prerequisites

- Python 3.12 or higher
- An NVIDIA NIM API key (get one at [build.nvidia.com](https://build.nvidia.com/))

### Installation

```sh
pip install resume-roast
```

For development:

```sh
git clone https://github.com/jfang324/resume-roast.git
cd resume-roast
poetry install
```

### First-Time Setup

Set your NVIDIA API key:

```sh
resume-roast config credentials
```

You can also configure the model, persona, and seniority level:

```sh
resume-roast config settings
```

Configuration is stored in `~/.resume-roast/`.

## Usage

### Evaluate a Resume

```sh
resume-roast evaluate path/to/resume.pdf
```

Extracts your resume, sends it to the LLM for structured analysis, and prints a diff-highlighted report with scores and rewrite suggestions.

### Refine a Bullet

```sh
resume-roast refine "Managed a team of 5 engineers"
```

Opens an interactive chat. The LLM coaches you, rating the bullet on every reply and suggesting improvements. Available commands:

| Command              | Action                                              |
| -------------------- | --------------------------------------------------- |
| `/replace <text>`    | Replace the bullet with a new version (re-rates it) |
| `/generate <notes>`  | Generate a candidate rewrite (notes optional)       |
| `/help`              | Show available commands                             |
| `/exit`              | End the session                                     |
| *(plain text)*       | Conversational coaching turn                        |

### Generate a Block

```sh
resume-roast generate-block
```

Opens an interactive chat. The LLM interviews you about a role or project, asking questions to gather specifics. Type `/generate` when you're ready to produce a formatted resume block (header + 3-6 bullet points). The model only generates if it can produce an 8-10/10 quality block — otherwise it asks more questions. Available commands:

| Command              | Action                                  |
| -------------------- | --------------------------------------- |
| `/generate <notes>`  | Generate a resume block (notes optional) |
| `/help`              | Show available commands                 |
| `/exit`              | End the session                         |
| *(plain text)*       | Answer questions, add details           |

### Interview

```sh
resume-roast interview path/to/resume.pdf
```

Starts an agentic behavioral interview. The LLM generates questions tailored to your resume, asks them one at a time, fact-checks your answers against the resume, and probes deeper with follow-ups when needed. After all questions, produces a competency report with per-category scores, strengths, and growth areas. Available commands:

| Command        | Action                       |
| -------------- | ---------------------------- |
| `/exit`        | End the interview early      |

## Development

See [docs/development.md](docs/development.md) for setup and development commands.

## Tools & Technologies

### Core

- Python 3.12+
- Typer (CLI framework)
- Rich (terminal output, spinners, diff rendering)
- pymupdf4llm (PDF to Markdown extraction)
- mammoth (DOCX to Markdown extraction)
- defusedxml (safe XML parsing for DOCX metadata parts)
- openai SDK (NVIDIA NIM API client)

### Code Quality

- Ruff (linting + formatting)
- Pyright (strict type checking)
- Bandit (security linting)
- pre-commit hooks

### Testing

- pytest
- coverage (branch coverage, 85% minimum)
- pytest-asyncio

### Build & Package

- Poetry

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
