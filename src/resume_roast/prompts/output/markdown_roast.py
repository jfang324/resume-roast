"""Output format: a human-readable Markdown roast, printable straight to a terminal."""

MARKDOWN_ROAST_FORMAT = """\
## Output Format

Respond in readable Markdown with exactly these sections:

## Overall Assessment
Your headline verdict in two to four sentences, in your persona's voice,
with an overall score out of 10.

## Category Feedback
One subsection per category, each opening with a score out of 10 and
giving specific findings grounded in text quoted from the resume:
- Formatting: section structure, ordering, length, and conventions, judged
  from the Markdown and the document statistics
- Content: bullet quality — accomplishments, metrics, verbs, concision
- Skills: relevance and grouping of the skills section, and its consistency
  with the bullets
- Experience: trajectory, scope, ownership, and chronology across roles
- Education: degree presentation, dates, GPA, coursework choices

## Suggestions
The highest-impact improvements, most important first. Each suggestion must
quote the resume text it targets and show a concrete rewrite — no generic
advice. Rewrites use only facts already in the resume: never invent
metrics, technologies, or claims; where a number is missing, write a
placeholder like "[X]%" for the candidate to fill in."""
