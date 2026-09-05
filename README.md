# SY Spec Builder

Building Regulations specifications for building control, generated from one library.
Eight residential project types, England.

| | |
|---|---|
| Library | `data/` — 113 construction build-ups, 325 general notes |
| App | a single self-contained HTML page, published as a Claude artifact |
| Documents | branded Word + PDF, one per project type, from the same library |

## Quick start

```bash
pip install -r requirements.txt
playwright install chromium

python build.py            # merge the library and assemble the app
python build.py --all      # ... plus the 141 tests and all 16 documents
```

Then open `dist/preview.html` in a browser.

You also need **Node** (the build uses it to evaluate the library) and **LibreOffice** on PATH as
`soffice` (used to convert the generated .docx to .pdf). Neither the app nor the tests need a network
connection.

## What is where

`CLAUDE.md` is the full brief — data model, house style, practice standards, backlog and the rules
that must not be broken. Read that before making changes.

- `data/` the library. The single source of truth; everything else is generated from it.
- `src/` the app. No build step, no npm dependencies.
- `docgen/` Word and PDF generation.
- `tests/` six Playwright suites.
- `reference/FACTS.md` every figure verified against the Approved Documents, with the date.
- `dist/`, `output/` build output — not committed.

## Conventions

Build-up references are per job, sequential in selection order: EW1, EW2, GF1, RF1. They are not
fixed library codes. Part A of a specification is the numbered build-ups; Part B is the general
notes by topic.

Nothing in this repo is copied from a commercial specification library. All wording is written from
the Approved Documents. See the non-negotiables in `CLAUDE.md`.

© SY Design Studio Ltd. Private repository — not for distribution.
