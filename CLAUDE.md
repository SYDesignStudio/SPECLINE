# SY Spec Builder

In-house Building Regulations specification tool for **SY Design Studio Ltd** (Salman Yousaf,
Director; 49 Durham Avenue, Hounslow TW5 0HG). It produces branded, submission-ready
specifications for building control across eight residential project types in **England**.

Used in house first; the intent is to open it to other practices later as a paid product.

---

## Non-negotiables

Read these before changing anything. They are the rules the project is built on, not preferences.

1. **Never invent a figure.** Every dimension, U-value, fire period, dB rating, litres/second or
   percentage must come from the Approved Documents, a British Standard, the legislation, or a
   manufacturer's published data. If you cannot confirm it, leave the existing wording alone and
   say so in your reply. Writing a plausible number into a building control document is the worst
   thing you can do in this repo. `reference/FACTS.md` holds the figures already verified — check
   there first.
2. **Clean room on third-party content.** BuildingRegs4Plans (and any competitor) may be used only
   as a checklist of *topics* — never copy, paraphrase closely, or export their clause text. All
   wording in `data/` is written from the Approved Documents in our own words. If a clause someone
   pastes in looks like it came from a commercial library, flag it rather than committing it.
3. **The brand stays here.** Do not upload the logo, practice details, or any generated document to
   a third-party website, and do not generate deliverables through another site's export engine.
   `src/logos.js` and `docgen/sy_logo.png` are local assets.
4. **`data/` is the single source of truth.** The app, the Word files and the PDFs are all generated
   from it. Never edit a generated file in `dist/` or `output/` — the next build overwrites it.
5. **Challenge the brief.** Salman wants mistakes pointed out, better solutions suggested, and
   Building Regulations or planning risks flagged. Technical accuracy beats agreement.

---

## Layout

```
build.py              one entry point: merge -> assemble -> structural check [-> test] [-> docs]
data/                 THE LIBRARY. Six JS files, one SPECS.<type> object each.
  specdata_core.js      extension, loft, flat   (declares `const SPECS = {...}`)
  specdata_garage.js    garage conversion       (assigns `SPECS.garage = {...}`)
  specdata_newbuild.js  new build house
  specdata_nbflats.js   new build flats
  specdata_basement.js  basement conversion
  specdata_garagebld.js new detached/attached garage
src/
  app_head.html         <style> and the page head fragment (design tokens live here)
  app_body.html         the page skeleton: header + five routes (desk, workspace, spec, working, standards)
  app_js.js             the app: routing, jobs desk, workspace, job store, preview, jsPDF export
  configurator.js       cavity wall U-value configurator (UI)
  configurator2.js      floor / basement / roof configurators (UI)
  ucalc.js              UC: materials with verified conductivities + wall calculations
  ucalc2.js             floors (BS EN ISO 13370), heated basements, three roof types
  logos.js              LOGO, LOGO_DARK, LOGO_PDF as data URIs
  vendor/jspdf.local.js local jsPDF, used only by dist/preview.html for offline tests
docgen/               Word + PDF generation (python-docx, LibreOffice for the PDF step)
  spec_from_data.py     the generator: one .docx + .pdf per type, straight from dist/specdata.js
  brand.py, build_spec.py   cover page, headers, house typography
  plancheck_report.py, dedupe_report.py   the two QA reports already issued
tests/                six Playwright suites, 141 assertions
reference/            FACTS.md (verified figures) and the per-type review notes
dist/                 build output — git-ignored
output/               generated .docx/.pdf — git-ignored
```

## Commands

```bash
python build.py                 # merge + assemble + structural check   (seconds)
python build.py --test          # ... and run all 141 Playwright assertions   (~4 min)
python build.py --docs          # ... and regenerate all 16 Word/PDF files
python build.py --docs loft     # regenerate one type only
python build.py --all           # everything
```

`dist/preview.html` opens straight from the filesystem — that is the fastest way to look at a
change. `dist/syds-spec-builder.html` is the file published as the Claude artifact.

**Always run `python build.py --test` before saying a change is done.** The structural check inside
`build.py` catches the errors that break the app silently: a note whose category is not in `cats`,
a category left with nothing in it.

Dependencies: Python with `python-docx` and `playwright` (`pip install -r requirements.txt`, then
`playwright install chromium`), Node (for the library check), and LibreOffice on PATH as `soffice`
for the PDF step. The app itself has no build step and no npm dependencies.

---

## Data model

Every type is:

```js
SPECS.<type> = {
  name: "House Extension", region: "England",
  cats: ["Planning & Permitted Development", "General Notes", ...],   // print + UI order
  buildups: [{ g:"EW", c:"External Walls", t:"Full Fill Cavity Wall",
               u:"0.17 W/m²K", tgt:"0.18 W/m²K", p:["paragraph", ...] }],
  notes:    [{ c:"Ventilation", t:"Ventilation — Approved Document F", p:["paragraph", ...] }]
}
```

- **`c` is the category** and must appear in that type's `cats`. This is a field on every record —
  there are no lookup tables. The build check enforces it.
- **`g` is the reference group** for build-ups: `EW` external wall, `IW` internal wall, `GF` ground
  floor, `IF` intermediate floor, `RF` roof, `SW` separating wall, `SF` separating floor,
  `BW` basement wall, `BF` basement floor. References are **per job, sequential in selection order**
  (EW1, EW2 …) — they are not fixed library codes, so never hard-code a reference in prose.
- A paragraph beginning `"NOTE — "` prints in grey as an instruction to the designer, not to the
  builder. Use it for genuine "check this on this job" prompts, never to defer a figure that is
  already known.
- Paragraphs are plain strings in a JS array. **No unescaped double quotes** — use single quotes or
  typographic quotes inside the text. Keep `²`, `³`, `—` as real characters; the PDF export maps
  what jsPDF's WinAnsi fonts cannot represent (`safe()` in `app_js.js`).

## House style for the written clauses

- A CAPS heading, then a target line (`To achieve minimum U-value of 0.18 W/m²K (actual U-value
  achieved 0.17 W/m²K)`), then flowing descriptive prose that specifies the construction layer by
  layer. **Not** numbered legal clauses.
- Named products with alternatives (`Celcon Solar, Thermalite Turbo or equivalent`), standards cited
  inline, practical installation notes at the end.
- British English. Professional, confident, concise — never robotic.
- Part A is the numbered construction build-ups; Part B is the unkeyed general notes by topic.
- **One subject, one note.** The library was de-duplicated in September 2026 after shared notes were
  appended without removing the older general notes covering the same ground: the documents repeated
  themselves and contradicted themselves. If you add a note, first search the type for an existing
  note on that subject and extend it. Cross-refer by note title rather than restating a rule.

## Practice standards (state these consistently)

| Item | The standard used here |
|---|---|
| Fire doors | `FD30S doorset (E 30 Sa, intumescent strips and cold smoke seals) with self-closer` — stated as exceeding the Approved Document B minimum where that minimum is E 20 |
| Alarms | `BS 5839-6 Grade D1 Category LD2` — stated as exceeding the AD B minimum of D2 LD3 |
| Escape window | ≥0.33 m², ≥450 × 450 mm clear, bottom of the openable area ≤1100 mm and ≥800 mm unless guarded, openable without a key |
| Hot water | Cylinder capable of storage at ≥60 °C; bath supply ≤48 °C by a TMV to BS EN 1111 or BS EN 1287 (Approved Document G3). Never "taps limited to 60 °C" |
| Fixed lighting | 75 lumens per circuit-watt, all fixed internal and external fittings, those under 5 circuit-watts excluded. The "three quarters of fittings" rule was withdrawn in AD L 2021 |
| Building control | Lower case in prose; "the Building Control Officer" for the person |

## U-value calculations

`ucalc.js` / `ucalc2.js` calculate to **BS EN ISO 6946** (combined method, with the Annex F
corrections for air gaps and wall ties) and **BS EN ISO 13370** (ground floors and heated
basements). The working is carried into the exported PDF as its own section, which is what makes
the numbers defensible to a plan checker.

Two things this repo has been caught out by before, both now covered by tests:

- **Rafter bridging roughly halves the effective resistance** of high-performance board between
  rafters. A build-up that looks right can be a long way off — 100 mm K107 between 47 × 150 rafters
  plus 37.5 mm K118 achieves 0.20, not the 0.15 once claimed. Never state a rafter-level U-value
  without running it through the calculator.
- Conductivities were verified against manufacturer and BBA data on 5 September 2026 and are
  recorded in `reference/FACTS.md`. Celotex is now branded **SOPRATHERM** (Soprema); Xtratherm is
  now **Unilin**. Re-verify before changing any `k` value.

---

## Publishing

The app is published as a Claude artifact at
`https://claude.ai/code/artifact/ab022f14-8507-4311-9d5a-b987dfd10a9a`
(capabilities: `db`, `downloads`). Publish `dist/syds-spec-builder.html` to **that URL** so the link
and saved jobs survive; publishing without the URL creates a separate artifact.

The generated documents are filed on Salman's PC under `D:\BUILDING REGULATIONS\`:
`0N - <TYPE>\03 Submission Pack\*.pdf` and `\04 Editable (Word)\*.docx`, with QA reports in
`09 - REFERENCE`.

---

## The app (rebuilt 5 September 2026)

Five routes behind the top tabs: **Jobs** (the desk: a live headline, the saved jobs, the eight
project types), **Workspace** (rail of job record → categories → review and issue, stage, live
preview), **Specification** (the preview full width with a contents nav), **U-value working**
(every calculated build-up on the job with its layer bar and working) and **Practice standards**.

- A job is `{id, type, data, sel, notes, custom, cfg*, history, created, updated}`. It autosaves
  to `localStorage` on every change and, in the artifact, to `db` collection `jobs/<id>` (debounced).
  Without `db` the app says "Kept in this browser" and still works.
- **Issue** downloads the PDF, appends `{rev, at, n, m}` to `history` and moves `data.rev` on
  (P01 → P02). Job numbers are typed, never generated.
- The **layer bar** (`layerBar()` in `app_js.js`) draws a build-up's layers to scale from the
  calculator's `layers` array. It is the app's signature: on the desk, in every configurator, on
  each calculated build-up card, on the working page. Colours come from `swatchFor()` by material.
- Design: warm paper ground, Newsreader for headings, Geist for text, Geist Mono for figures.
  Graphite for actions; the studio orange only for the built thing (references, targets, the bar).
  The logo from `src/logos.js` sits on a white plate in dark mode (`--logo-plate`).
  `LOGO_DARK` is a screenshot strip with UI baked in — do not use it.
- Test selectors that must survive a restyle: `.tile[data-k]`, `button.step` (`.st`, `.sc`),
  `#stepJob`, `.crumb`, `#fields input[data-k]`, `#typename`, `#stage .card` (`.tag`, `.more`,
  `.rm`), `#paper .sched`, `#btnPdf`, `#btnPrev`, `#btnType`, `.viewer`, `.cfgcard`, `.uval`,
  `#addWall/#addFloor/#addRoof`, `select[data-cf]`, `table.wk`, `.cfgwarn`.
- The wizard-style answer steps in the Claude Design artboard (fire safety, sound, ventilation as
  single choices) were deliberately **not** built: the library has no rule mapping answers to
  notes, and a radio choice would have let a job issue without an alarm note. Notes stay
  on/off per category.

## Backlog

Roughly in order:

- Word export from the app. Word files are still generated on the practice PC by
  `python build.py --docs`; the app offers PDF only and says so.
- Parametric timber frame walls, dormer cheeks and internal linings — these are still fixed
  build-ups while cavity walls, floors, basements and roofs are configurable.
- Wales as a second region (different Part L/F targets and a separate notional dwelling).
- Rebuild the A102 General Notes drawing sheet, which still cites withdrawn standards
  (BS 5950, BS 5628, BS 6206, BS 5588-9) and carries another practice's name.
- Embed a font in the PDF export if the documents are to go to unknown recipients. The `²`/`³`
  characters *are* in the file; some viewers substitute a font that lacks the glyph because the
  standard PDF fonts are referenced rather than embedded. Costs roughly 300 KB per file.

**Two figures deliberately left unconfirmed** (recorded in `reference/review-notes/`): the 60-minute
fire resistance for a basement more than 10 m deep or with more than one basement storey, and the
car park ventilation percentages in New Build Flats. Both are conservative as written. Confirm
against the Approved Document before the first job of either kind rather than changing them on an
assumption.

## Regulatory horizon

Approved Documents L1 and F1 **2026 editions** were published on 24 March 2026 and come into force
on **24 March 2027**, with transitional relief for new dwellings commenced before 24 March 2028.
Every specification carries the flag. The library will need a full pass against the new editions
during 2027 — that is a rewrite of the Part L and Part F content, not a patch.
