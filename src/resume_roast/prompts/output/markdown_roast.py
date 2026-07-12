"""Output format: a human-readable Markdown roast, printable straight to a terminal."""

MARKDOWN_ROAST_FORMAT = """\
## Output Format

Your entire response is readable Markdown printed straight to a terminal
for a human — never JSON, YAML, or a code fence. Every score in the
response is an integer out of 10; a 100-point scale is never used. The
response has exactly the seven sections below, in this order, with the
exact heading lines shown — each category's score lives in its heading,
never in the body text. The text under each heading describes what that
section must contain: write it out as full prose grounded in quoted resume
text — a heading with a bare score and no findings is an incomplete
response, and so is a response that stops before `## Suggestions`.

## Overall Assessment
Your headline verdict in two to four sentences, in your persona's voice,
closing with the line `Overall: <n>/10`.

## Formatting — <n>/10
Section structure, ordering, length, and conventions.

## Content — <n>/10
Bullet quality — accomplishments, metrics, verbs, concision.

## Skills — <n>/10
Relevance and grouping of the skills section, and its consistency with the
bullets.

## Experience — <n>/10
Trajectory, scope, ownership, and chronology across roles.

## Education — <n>/10
Degree presentation, dates, GPA, coursework choices.

## Suggestions
The highest-impact improvements, most important first. Each suggestion must
quote the resume text it targets and show a concrete rewrite — no generic
advice. Rewrites use only facts already in the resume: never invent
metrics, technologies, or claims; where a number is missing, write a
placeholder like "[X]%" for the candidate to fill in. This section always
ends the response."""

MARKDOWN_ROAST_REMINDER = """\
Evaluate the resume above. Follow the Output Format skeleton exactly: the
first line of your response is `## Overall Assessment`; then one `## <name>
— <n>/10` section per category (Formatting, Content, Skills, Experience,
Education) with the score in the heading and your findings, grounded in
quoted resume text, as the body; then `## Suggestions` to end the response.
Every score is an integer out of 10 — never out of 100."""
