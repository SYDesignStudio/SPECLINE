# Specline

[![Licence: proprietary](https://img.shields.io/badge/licence-proprietary-0E6E85)](LICENSE)

Building Regulations specifications for building control, generated from one library.
Eight residential project types, England.

Specline is the application. The specification it produces carries the practice's own logo,
name and address — never Specline's. Built and used in house at SY Design Studio Ltd.

| | |
|---|---|
| Library | `data/` — 124 construction build-ups, 325 general notes |
| App | a single self-contained HTML page, published as a Claude artifact |
| Documents | branded Word + PDF from the app, and one master pair per project type from the library |

## Quick start

```bash
pip install -r requirements.txt
playwright install chromium

python build.py            # merge the library and assemble the app
python build.py --all      # ... plus the 167 tests and all 16 documents
```

Then open `dist/preview.html` in a browser.

You also need **Node** (the build uses it to evaluate the library) and **LibreOffice** (used to
convert the generated .docx to .pdf; it is found on PATH or in the usual install locations, and
without it the Word files are still written). Neither the app nor the tests need a network
connection.

## What is where

`CLAUDE.md` is the full brief — data model, house style, practice standards, backlog and the rules
that must not be broken. Read that before making changes.

- `data/` the library. The single source of truth; everything else is generated from it.
- `src/` the app. No build step, no npm dependencies.
- `docgen/` Word and PDF generation.
- `tests/` seven Playwright suites, 167 assertions.
- `reference/FACTS.md` every figure verified against the Approved Documents, with the date.
- `dist/`, `output/` build output — not committed.

## Conventions

Build-up references are per job, sequential in selection order: EW1, EW2, GF1, RF1. They are not
fixed library codes. Part A of a specification is the numbered build-ups; Part B is the general
notes by topic.

Nothing in this repo is copied from a commercial specification library. All wording is written from
the Approved Documents. See the non-negotiables in `CLAUDE.md`.

## Licence

Copyright © 2026 SY Design Studio Ltd. All rights reserved.

**Source-available, not open source.** The source is published so it can be read. No permission is
granted to use, copy, modify or distribute any part of it, and that applies to the specification
text in `data/` as much as to the code — reproducing those clauses in another specification,
drawing or product is not permitted. See [LICENSE](LICENSE) for the full terms.

Specline is intended to be licensed commercially to other practices. Enquiries:
info@specline.co.uk

The specification text is written for a competent designer who stays responsible for its
suitability on the job. Check every figure against the Approved Document in force at the date of
submission.
