"""Scoring calibration: what is being judged, and the 1-10 bands to judge it on."""

EVALUATION_PRIORITIES = """\
## What You Are Evaluating

A resume has one job: convey competence for the target level. Every category
is a lens on that question, and the overall score answers it directly — it is
never an average of category scores.

Categories are not equally weighted: content and experience carry most of
the verdict, skills and education support it, and formatting matters only
where it obstructs the reader. You see formatting secondhand — the Markdown
extraction and document statistics are lossy proxies for the real layout —
so hold those conclusions loosely and give the benefit of the doubt to
anything extraction could have mangled. Strong substance in a plain wrapper
beats polish around weak substance."""

SCORE_BANDS = """\
## Score Bands

Score each category and the overall assessment on a 1-10 scale:
- 9-10: Exceptional — accomplishment-driven and quantified throughout, flawless structure
- 7-8: Strong — mostly achievement-focused, some quantification, well organized
- 5-6: Adequate — duties mixed with accomplishments, occasional metrics, some vague language
- 3-4: Below Average — mostly task descriptions, few metrics, weak verbs or walls of text
- 1-2: Poor — vague throughout, no quantification, missing sections

The guidance below is calibration, not a checklist: score each issue by what
it actually costs the reader, not by counting rule matches. Numeric
thresholds (GPA cutoffs, word counts, bullet limits) are rules of thumb —
near-misses are judgment calls worth a mention, never violations to
penalize."""
