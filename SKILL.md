---
name: university-student-writing
description: Create, adapt, or review standards-based Chinese and English LaTeX documents for university students, including coursework, research, campus administration, social practice, student organizations, campus news, applications, and career materials. Use when document genre, institutional conventions, evidence, citations, or typesetting correctness matter; defer to a supplied school or instructor template.
---

# University Student Writing

Create a complete, editable LaTeX project whose structure and presentation fit the requested university-student genre.

## Route the request

1. Identify the audience, language, genre, receiving organization, submission format, and whether a school or instructor template exists.
2. Read [references/routing.md](references/routing.md), then load only the guide for the selected domain:
   - academic work: [references/academic/guide.md](references/academic/guide.md)
   - campus-life documents: [references/campus-life/guide.md](references/campus-life/guide.md)
   - social practice and internships: [references/social-practice/guide.md](references/social-practice/guide.md)
   - student organizations: [references/student-organization/guide.md](references/student-organization/guide.md)
   - campus news: [references/campus-news/guide.md](references/campus-news/guide.md)
   - career and applications: [references/career/guide.md](references/career/guide.md)
3. For standards, conflicts, or claims that a format is mandatory, read [references/source-policy.md](references/source-policy.md) and consult [sources.md](sources.md).

## Preserve authority and facts

Apply requirements in this order:

1. the user's explicit instructions and supplied template;
2. the current template of the school, instructor, competition, or recipient;
3. an applicable current national, international, or publisher standard;
4. a convention supported by multiple universities;
5. an optional readability recommendation.

Name the authority level used. Do not turn a single-school example into a universal rule. Do not invent experiences, survey data, quotations, awards, approvals, signatures, official positions, or news facts. Use visible `[[待填写：…]]` fields when facts are missing.

## Generate the project

Read [references/latex-workflow.md](references/latex-workflow.md). Prefer the deterministic generator:

```powershell
python scripts/create_document.py --genre <genre-id> --output <new-directory>
```

Use `--list` to discover genre IDs. A supplied official template takes precedence; preserve it and adapt content inside a copy instead of replacing its class, style files, fonts, or layout.

Deliver the source project and a compiled PDF when a TeX engine is available. Use XeLaTeX by default for the built-in templates. Do not claim successful compilation without running it.

## Validate

Run:

```powershell
python scripts/validate_document.py <project-directory>
```

Resolve errors before delivery. Review warnings in context rather than suppressing them globally. Visually inspect representative rendered pages whenever layout matters.

## Boundary

The built-in templates are reliable baselines, not substitutes for mandatory Word forms, online forms, official seals, or institution-specific approval workflows. For publisher submission, use that publisher's current official template rather than recreating it.
