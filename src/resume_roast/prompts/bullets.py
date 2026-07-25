"""Writing principles and the shared rating bands for resume bullet points."""

BULLET_PRINCIPLES = """\
## Bullet Writing Principles

- Every bullet must describe an accomplishment, not a routine task or job description — the resume is not the job description
- One sentence per bullet, short enough to read at a glance; judge length by word count, not by rendered lines
- Quantify with specific numbers, percentages, or metrics, placed early in the bullet
- Use digits, not spelled-out numbers (8, not eight)
- Start with a strong action verb: past tense for past roles, present tense for a role the candidate still holds
- Center the engineering skill, not the tool: what was designed, decided, and solved, with the software as supporting detail
- Avoid sub-bullets; they clutter more than they clarify
- Replace weak verbs: assisted, helped, participated, used, worked on
- Avoid superfluous verbs: crafted, innovated, leveraged, orchestrated, spearheaded
- Avoid filler adjectives and adverbs: excellent, innovative, expert, successfully, meticulously, strategically
- No trailing period on bullet points

"""

RATING_BANDS = """\
- 9-10: Accomplishment throughout, quantified with specific metrics; strong, varied action verbs; nothing vague
- 7-8: Mostly accomplishment-focused with some quantification; could be sharper in a place or two
- 5-6: Duties mixed with accomplishments; sparse metrics; some weak verbs or vague phrasing
- 3-4: Mostly task description; few or no metrics; weak verbs or walls of text
- 1-2: Vague throughout, no quantification
- 0: Nothing to judge — no substantive content to rate yet"""
"""The 0-10 bands behind every bullet rating the tool reports.

Bands only, no heading: refine rates one bullet and generate-block rates a
whole block, so each supplies its own heading and subject line above these.
"""
