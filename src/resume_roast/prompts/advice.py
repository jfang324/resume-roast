"""Evaluation rubric blocks shared by prompt builders."""

SCORE_BANDS = """\
## Score Bands

Score each category and the overall assessment on a 1-10 scale using these bands:
- 9-10: Exceptional — every bullet is an accomplishment, strong action verbs, quantified results throughout, flawless structure
- 7-8: Strong — most bullets are achievement-focused, some quantification, clear action verbs, good organization
- 5-6: Adequate — mix of duties and accomplishments, occasional metrics, some weak verbs or vague language
- 3-4: Below Average — mostly task descriptions, few metrics, weak verbs, poor structure or walls of text
- 1-2: Poor — vague or no descriptions, no quantification, bad verbs, missing sections, objectively weak"""

BULLET_PRINCIPLES = """\
## Bullet Writing Principles

Writing principles for resume bullet points:

- Every bullet must describe an accomplishment, not a routine task or job description
- Quantify with specific numbers, percentages, or metrics
- Follow action to context to quantified result structure
- Start with a strong past-tense action verb
- Include relevant technical keywords and context
- No vague descriptions without measurable impact
- Replace weak verbs: aided, assisted, helped, participated, worked on, used, utilized
- Avoid superfluous verbs: leveraged, enhanced, innovated, spearheaded
- No trailing period on bullet points

Example transformations:
Bad: "Responsible for managing the company blog and social media accounts."
Good: "Grew organic blog traffic from 12K to 85K monthly visitors in 10 months by implementing a pillar-cluster content strategy."

Bad: "Worked on a team to improve website performance using various tools."
Good: "Designed and implemented a Redis caching layer, reducing API response times from 450ms to 80ms and cutting server costs by 25%."

Bad: "Used Python to analyze data and create reports for the team."
Good: "Built an automated ETL pipeline in Python processing 2M records daily, eliminating manual reporting and saving 15 engineer-hours per week.\""""

RESUME_STRUCTURE = """\
## Resume Structure

Structure rules for the overall resume:

- Use bullet points, not paragraphs or dense prose
- Limit to 5-6 bullets per role
- Bullets ordered from most relevant/impressive to least; the further down the
  resume content appears, the lower the chance it will be seen on a skim
- No personal pronouns (I, we, my, our, their)
- No soft skills or objective sections — demonstrate through bullet content instead
- Education should omit irrelevant coursework
- Skills section should omit soft skills, operating systems, and IDEs
- No objective/summary/references section unless senior engineer or career changer
- Consistent date formatting with no gaps or mixing of formats
- Information not relevant to the target role dilutes the resume and may be a
  candidate for removal depending on how full the resume is overall"""
