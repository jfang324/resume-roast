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

- Every bullet must describe an accomplishment, not a routine task or job description — the resume is not the job description
- One sentence per bullet, at most two lines
- Quantify with specific numbers, percentages, or metrics, placed early in the bullet
- Use digits, not spelled-out numbers (8, not eight)
- Start with a strong past-tense action verb
- Center the engineering skill, not the tool: what was designed, decided, and solved, with the software as supporting detail
- Avoid sub-bullets; they clutter more than they clarify
- Replace weak verbs: aided, assisted, coded, collaborated, executed, helped, participated, programmed, used, utilized, worked on
- Avoid superfluous verbs: crafted, engineered, enhanced, innovated, leveraged, orchestrated, pioneered, spearheaded, transformed
- Avoid filler adjectives and adverbs: excellent, innovative, expert, successfully, meticulously, strategically
- No trailing period on bullet points

Example transformations:
Bad: "Responsible for managing the company blog and social media accounts."
Good: "Grew organic blog traffic from 12K to 85K monthly visitors in 10 months by implementing a pillar-cluster content strategy"

Bad: "Worked on a team to improve website performance using various tools."
Good: "Designed and implemented a Redis caching layer, reducing API response times from 450ms to 80ms and cutting server costs by 25%"

Bad: "Used Python to analyze data and create reports for the team."
Good: "Built an automated ETL pipeline in Python processing 2M records daily, eliminating manual reporting and saving 15 engineer-hours per week\""""

RESUME_STRUCTURE = """\
## Resume Structure

Sections and layout:
- Use bullet points, not paragraphs or dense prose; limit to 5-6 bullets per role
- Order entries and bullets from most relevant/impressive to least — content further down is less likely to be read
- Plain section names: Experience, Projects, Skills, Education — not "Professional Experience" or "Relevant Skills"
- No summary/objective section unless senior or a career changer; never a references section
- No personal pronouns (I, we, my, our, their)
- Typos and grammar errors signal carelessness — flag every one you find

Skills section:
- At most 3 lines, grouped into categories, comma-separated
- No proficiency labels ("expert in"), no soft skills, and nothing taken for granted: operating systems, IDEs, or repo hosts (Git is a skill; GitHub is not)
- Skills and bullets must agree: a listed skill that never appears in a bullet is unsupported, and a technology central to the bullets belongs in skills

Education:
- Graduation date only (no date ranges), reverse chronological, no high school
- GPA only if 3.75+, two decimals; drop it after the first full-time job
- Omit coursework unless truly specialized

Contact and conventions:
- Plain-text URLs (github.com/username), not masked links; GitHub/portfolio links only if they have real content
- No physical address
- Dates: "Present" not "Current"; en dashes for ranges; no seasons ("Winter 2022") or abbreviated years ('23); one consistent format throughout"""
