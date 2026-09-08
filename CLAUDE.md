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
   `docgen/sy_logo.png` is a local asset. `src/logos.js` carries the Specline mark only — the
   practice logo is never compiled into the app; see "The practice on a generated document".
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
  configurator3.js      foundation configurator (UI) — checks, not a calculation
  configurator4.js      framed wall configurator (UI) — timber frame, dormer cheeks
  ucalc3.js             UC.frame: studded walls, combined method for stud bridging
  ucalc.js              UC: materials with verified conductivities + wall calculations
  ucalc2.js             floors (BS EN ISO 13370), heated basements, three roof types
  docx.js               DOCX: a dependency-free .docx writer (ZIP + OOXML), used by the app
  logos.js              SPECLINE_ICON (app chrome, favicons). No practice logo — build.py enforces it
  vendor/jspdf.local.js local jsPDF, used only by dist/preview.html for offline tests
docgen/               Word + PDF generation (python-docx, LibreOffice for the PDF step)
  spec_from_data.py     the generator: one .docx + .pdf per type, straight from dist/specdata.js
  practice.py           WHOSE document it is — one profile lookup, shared by every generator
  brand_inhouse.py      SY Design Studio's own profile; reached only by asking for it
  brand.py, build_spec.py   cover page, headers, house typography
  plancheck_report.py, dedupe_report.py   the two QA reports already issued
tests/                seven Playwright suites, 192 assertions
reference/            FACTS.md (verified figures) and the per-type review notes
dist/                 build output — git-ignored
output/               generated .docx/.pdf — git-ignored
```

## Commands

```bash
python build.py                 # merge + assemble + structural check   (seconds)
python build.py --test          # ... and run all 192 Playwright assertions   (~4 min)
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
`playwright install chromium`), Node (for the library check), and LibreOffice for the PDF step.
`_soffice()` in `docgen/spec_from_data.py` finds LibreOffice on PATH or in the usual install
locations, so it does not need to be on PATH; without it the Word files are still written and the
PDFs are skipped with a warning. The app itself has no build step and no npm dependencies.

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
  `BW` basement wall, `BF` basement floor, `FD` foundation. `FD` is first in `GORDER`, so
  foundations head the schedule. References are **per job, sequential in selection order**
  (EW1, EW2 …) — they are not fixed library codes, so never hard-code a reference in prose.
- A paragraph beginning `"NOTE — "` prints in grey as an instruction to the designer, not to the
  builder. Use it for genuine "check this on this job" prompts, never to defer a figure that is
  already known.
- Paragraphs are plain strings in a JS array. **No unescaped double quotes** — use single quotes or
  typographic quotes inside the text. Keep `²`, `³`, `—` as real characters; the PDF export maps
  what jsPDF's WinAnsi fonts cannot represent (`safe()` in `app_js.js`).

## House style for the written clauses

- A CAPS heading, then a target line (`To achieve a maximum U-value of 0.18 W/m²K (actual U-value
  achieved 0.17 W/m²K)`), then flowing descriptive prose that specifies the construction layer by
  layer. **Not** numbered legal clauses. A U-value limit is a **maximum** — the element may not be
  worse than the figure. The library said "minimum" on 21 target lines until 6 September 2026, which
  read as the opposite of what Part L requires; all 51 target lines now say maximum.
- **Temperatures use the degree symbol** (`60°C`, not "60 degrees Celsius"). `°` is in the WinAnsi
  set the PDF export uses, so it needs no mapping. Standardised across the library on
  6 September 2026.
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
| Wall ties | `450 mm vertical × 900 mm horizontal centres, staggered` — the PD 6697 maximum — and **225 mm vertical within 225 mm of unbonded jambs, reveals and movement joints**, which is closer than the 300 mm the standard allows and is stated as exceeding it. `reference/FACTS.md` records both figures so the two cannot be mistaken for a contradiction |
| Category headings | A **bullet** in the practice's accent, then the category in caps — in the app's preview, its PDF and its Word file, and in `docgen`'s documents. An asterisk reads as a footnote reference and there are no footnotes. Part B's headings are numbered instead, so they carry no bullet. In the app's PDF the bullet is **drawn** (`doc.circle`), because `safe()` maps the character to a hyphen: jsPDF's WinAnsi fonts cannot be relied on for it |
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
- **Stud bridging does the same thing to a framed wall.** `UC.frame()` in `src/ucalc3.js` runs
  timber frame panels and dormer cheeks through the combined method. On 6 September 2026 it found
  seven library figures stated **without the Annex F air-gap correction**, all of them 140mm K112
  between 38 × 140 studs at 400mm centres. **Corrected the same day.** What changed:

  | Build-up | Was | Now | Change made |
  |---|---|---|---|
  | Dormer Cheek, and the rendered and clad variants | 0.18 | 0.16 | 37.5mm K118 lining specified; as written it was 0.20 and failed |
  | Hip to Gable — Timber Frame Gable | 0.18 | 0.16 | 37.5mm K118 lining specified; as written it was 0.21 and failed |
  | Infill to Garage Door Opening — Timber Frame | 0.14 | 0.16 | figure only; the construction already met 0.18 |
  | Timber Frame External Wall (new build) | 0.14 | 0.16 | figure, and the service-void alternative removed — at 0.20 it failed |
  | Timber Frame External Wall (new build flats) | 0.14 | 0.16 | as above |

  The lesson is the same one the rafters taught: at air-gap level 0 every original figure was
  right, so this was an assumption rather than an arithmetic error. **Never state a framed-wall
  U-value without running it through `UC.frame()`.**
- **The `u` field is what the build-up ACHIEVES; `tgt` is what it has to beat.** On 8 September
  2026 an audit through `UC.wall()`, `UC.roofRafter()`, `UC.roofCeiling()` and `UC.roofFlat()`
  found nine figures where the standard had been written into the achieved field, or an
  alternative arrangement's figure had, and one build-up that missed the target printed beside
  it. Everything else in the library reconciled exactly.

  | Build-up | Was | Now | What was wrong |
  |---|---|---|---|
  | Pitched Roof — Insulation Between and Over Rafters (new build) | 0.12 | 0.10 | 0.12 against a 0.11 target: **the specification failed on its own sheet.** The over-rafter board is now the 100mm the clause already priced at 0.10 |
  | Solid Wall — Internally Insulated (extension) | 0.30 | 0.26 | the retained-element standard, not the achievement |
  | Existing Gable or Flank Wall — Internally Insulated (loft) | 0.30 | 0.26 | as above, and its own prose already said 0.26 |
  | Pitched Roof — Insulation at Ceiling Level (extension) | 0.15 | 0.11 | the target. 400mm of 0.044 quilt is 0.11, as the two new-build clauses say of the same build-up |
  | Pitched Roof — Insulation at Ceiling Level, Residual Void (loft) | 0.15 | 0.11 | as above |
  | Existing Roof — Insulation at Ceiling Level (flat) | 0.16 | 0.11 | the renovation standard, not the achievement |
  | Existing Pitched Roof — Insulation at Ceiling Level (garage) | 0.16 | 0.15 | 300mm total is 0.15; the new-build clause says so of the same 300mm |
  | Pitched Roof — Insulation at Rafter Level (extension) | 0.15 | 0.14 | the 52.5mm alternative's figure, not the 62.5mm specified |
  | Pitched Roof — Insulation Between and Under Rafters (loft) | 0.15 | 0.14 | as above |
  | Partial Fill Cavity Wall (extension) | 0.18 | 0.16 | the target; the 0.15 block gives 0.16 |
  | Existing Uninsulated Cavity Wall — Blown Cavity (garage) | 0.25 | 0.28 | the better of two specified linings; state the worse |

  Two checks in `docgen/detail_review.py` now hold the line: a **FAIL** where the achieved value
  is worse than the target, and a **warn** where it is not among the figures the clause itself
  works out. Neither can catch a figure the clause never states, so **run a new or edited
  build-up through `UC` before writing its `u`** — and where two types carry the same
  construction, they must carry the same number.

  `UC` has no mode for insulation between AND over the rafters (the warm roof / sarking board
  build-up). It was checked by hand against `roofRafter`'s own conventions — Rse 0.10 for the
  ventilated batten space, 47/spacing bridging, the Annex F gap correction scaled by
  (R insulation / R total)². Worth adding as `roofOverRafter()`.
- The cladding on a framed wall sits outside a ventilated cavity, so BS EN ISO 6946 §6.9.3
  requires it and the cavity to be disregarded with the external surface resistance taken as still
  air. The outer finish therefore changes the prose and the boundary check, not the U-value.
- Conductivities were verified against manufacturer and BBA data on 5 September 2026 and are
  recorded in `reference/FACTS.md`. Celotex is now branded **SOPRATHERM** (Soprema); Xtratherm is
  now **Unilin**. Re-verify before changing any `k` value.

---

## The practice on a generated document — `docgen/practice.py`

**No generator owns a practice.** One lookup serves the Word specification, the PDF and the
detail sheets, so they cannot disagree about who drew the job. Order, first hit wins: a path the
caller passes, then `SPECLINE_PRACTICE`, then `specline-practice.json` in the directory **above
the repository**, then placeholders. `"brand"` as the path means `docgen/brand_inhouse.py`, which
holds SY Design Studio's own profile and is reached **only** by asking for it. A profile carries
`name`, `designer`, `addr`, `email`, `web`, and optionally `accent` and `logo` — the practice's
own branding on its own document. `docgen/practice.example.json` is the template.

`docgen/brand.py` used to *be* the profile. On 7 September 2026 it was split: the typography and
page set-up stayed (they are Specline's, and the same on every document), and the identity moved
out to the lookup. Three things went with it, each of which had been putting this practice on
every other practice's specification:

- **`ORANGE` was `F5900A`, SY Design Studio's brand colour**, on every heading, rule, NOTE flag
  and build-up reference in every document the tool produced. It is now `ACCENT`, read from the
  profile, defaulting to the same dark grey as the body text. `ORANGE` survives as an alias so
  nothing breaks silently; prefer `ACCENT`.
- **The cover printed the wordmark "SY DESIGN STUDIO"** whenever no logo file was found, and
  `spec_from_data.py` passed `sy_logo.png` explicitly so one was always found. The cover now
  falls back to the practice's *own* name set as a wordmark, and the generator passes no logo.
- **"Prepared By" read `Salman Yousaf, SY Design Studio Ltd`**, hard-coded in the meta dict.
  `cover()` already fell back to the profile, so the fix was deleting the key.

The filename lost its `SYDS_` prefix at the same time (`SPEC_<type>_<region>.docx`) — a
subscriber's file should not arrive prefixed with another practice's initials.

The two QA reports are the exception and pin the in-house profile deliberately
(`SPECLINE_PRACTICE_SOURCE=brand`, set before they import `build_spec`): they are SY Design
Studio's own reviews of the library, not a practice's specification.

**With no profile the documents print `[Practice name]`.** That is the safe failure, and the
reason nothing here defaults to a real firm: a blank cover gets corrected before issue, another
company's name might not. Check a change to any generator by running it against a made-up profile
and grepping the output for "SY Design", "Salman" and "Specline" — all three must be absent.

### The same rule inside the app — `src/app_js.js`, `src/logos.js`, `site/app.php`

The app had the identical fault one layer along, and worse, because the built app is *deployed*:
`site/app/spec.html` is committed and served to every signed-in practice. Fixed 7 September 2026.

- **`PRACTICE_SEED` carried SY Design Studio Ltd** — name, designer, address — and
  `PRACTICE_SEED_LOGO` in `src/logos.js` carried the logo itself as a data URI. Any subscriber who
  had not yet filled in the Practice page issued a specification under the vendor's name with the
  vendor's logo on the cover, and `savePractice()` then wrote that logo into *their* stored
  profile. It is now `PRACTICE_BLANK` — empty — and `logos.js` holds the Specline mark only.
- **The document accent was `#E8850C` / `B5640A`**, the vendor's brand orange, on the cover rule,
  the SPECIFICATION heading, every section rule, every build-up reference and every NOTE bar.
  It is now `accHex()`, read from the practice's own `accent` (a colour field on the Practice
  page), defaulting to the same neutral `3E4244` as `docgen/practice.py`. `accInk()` darkens it
  for text and `accSoft()` tints it for the notice panel; `applyAccent()` pushes all three onto
  `#paper`, whose `.paper` rule holds only the neutral defaults.
- **No logo is not an error state.** The cover sets the practice's own name as a wordmark instead
  — in the preview (`.pmark`), the PDF and the .docx. Before this, the fallback was the vendor's
  compiled-in mark, so the failure was silent and looked deliberate.
- **`site/app.php` is the only source of a practice on the hosted side.** It builds the profile
  from the `practices` row with the stored profile over it, and injects it as `window.SPECLINE`
  `.practice`; the app makes that `PRACTICE_BASE`, the thing a saved profile is merged onto. A
  saved profile wins where it has a value; with nothing saved the account's own details stand
  alone. There is no third fallback, by design.
- **`build.py` fails the build** if "SY Design Studio", "Salman", "sydesignstudio" or
  "Durham Avenue" appears in `logos.js`, `app_js.js`, `app_head.html` or `app_body.html` — comments
  included, because comments ship inside the built HTML. Write "the vendor's own practice" instead.
- **`tests/test7.py` sets its own practice** (`Marchmont Ridley Architects`, accent `#1F5C7A`) and
  asserts it reaches the cover, that the darkened accent reaches the XML, that no fixed brand
  colour does, and that none of the forbidden names — Specline included — appears anywhere in the
  document. Never assert a real firm's name in a test: it goes green on precisely this bug.

## Detail schedules — `docgen/detail_schedule.py`

`python docgen/detail_schedule.py` writes three files into `reference/details/` from `data/`:

- `build-up-schedule.md` — all 124 build-ups, layer by layer, each with the clause underneath
- `build-up-schedule.json` — the same, machine-readable, for generating DXF or PDF
- `detail-register.md` — the 18 junctions worth drawing, which types need each, and what is drawn

**The layers are extracted from the clause prose, not stored.** The library says "a 103mm facing
brick outer leaf, a 100mm cavity fully filled with 90mm Kooltherm K106", so the schedule reads the
thicknesses back out of the sentence. That is good enough to set a drawing out with and not good
enough to submit unchecked, which is why every build-up carries its clause and every layer carries
the phrase it was read from. Two limits worth knowing:

- **A clause states what it states.** The cavity wall never gives the dabs a thickness, so the
  extracted total is 315.5 against the verified 325.5. Where `buildup-layer-schedule.md` holds a
  hand-checked table (EW1, GF1, RF1) the JSON points at it with `verified_table` and **that table
  wins**.
- **A phrase with no identifiable material is not a layer.** Those are dropped and listed in
  `extraction_notes` rather than guessed into the drawing.
- **A number that gives a position is never a thickness, and no other word may rescue it.**
  `NEVER_A_LAYER` is an unconditional veto — spacings, levels, laps, upstands. Until
  7 September 2026 it was cancelled whenever `hatch_for()` matched anything later in the phrase,
  and `hatch_for()` answers "what would I draw this with", not "is this a material": its patterns
  match single common nouns. *"at 450mm vertical centres and at every stud horizontally"* matched
  **stud** and became 450mm of timber; *"an air-gap correction of 0.01"* matched **gap**;
  *"600mm below finished ground level"* matched **ground**. **45% of the drawn build-ups had an
  invented band** — EW5 timber frame was drawn 764.5mm against a real 314.5mm, with the phantom
  sitting inboard of the plasterboard. `QUALIFIER` is the separate, conditional list (*minimum*,
  *clear*) for words that may legitimately precede a material.
- **A member is drawn at its depth, which is the larger of the pair.** The library writes both
  orders — `47mm x 150mm rafters` and `140mm x 38mm studs` — so neither position can be trusted.
  Taking the first number gave a 38mm timber frame wall; taking the second, a 47mm rafter zone.
- **A member and what fills it are one band.** The rafter zone *is* the zone the insulation
  between the rafters occupies. Drawing both counted one 150mm zone as 300mm. A partial fill
  still leaves the band at the member's depth (`FILLS_THE_ZONE`).
- **`verify()` refuses to write a schedule containing any of the above, and exits non-zero.**
  Everything downstream draws from the JSON, so a bad layer there becomes a bad sheet and a bad
  DXF. The phrase each layer was read from had been recorded since the beginning *exactly* so it
  could be checked, and it never was — which is why a third of the set was wrong for weeks with
  nothing failing. It caught one more on its first run: a sentence of U-value working,
  *"a 150mm cavity with 150mm of the 0.032 slab calculates at 0.18"*, reaching the cavity-split
  branch looking exactly like a filled cavity.

- **The swallowed layers are rescued, not lost** (`_rescue`). The phrase window is greedy to 70
  characters because the cavity split (`100mm cavity fully filled with 90mm Kooltherm`) and the
  member rule (`47mm x 150mm rafters`) both have to see two thicknesses in one phrase. The cost
  was that a second layer named close behind the first vanished inside it — the 300mm quilt that
  is a cold-roof ceiling's entire insulation, 50mm sand blinding, 19mm plank flooring. Swallowed
  thicknesses now go back through the same vetoes (`_consider` is shared, so the two passes cannot
  drift apart), and **17 real layers came back**.
  The rescue pass is deliberately meaner than the top-level scan, because a salvage operation
  should not invent: it refuses anything from a sentence containing `calculat|W/m|achiev`, any
  figure equal to the one it sits inside (`115mm K106 in a 115mm cavity` is one band named twice),
  anything after an `or` (an alternative, not an extra band), a member named inside another phrase,
  and any label that is not a material once trimmed at the first connective.
- **An "A or B" pair keeps A.** `18mm or 22mm chipboard` is one layer offered in two thicknesses.
  Dropping the first instead left a stud partition with no studs.

### Reviewing the details — `docgen/detail_review.py`

`python docgen/detail_review.py [type]` reads every extracted build-up against its own clause and
reports; it never edits. `verify()` refuses what a regular expression can be certain of, and this
is for everything else — the defects that need the layers and the clause read side by side, which
is how both of the big ones were found. It exits non-zero on a FAIL.

Its first run, on 7 September 2026, found **20 layers drawn as the wrong material**: the hatch was
chosen from the whole matched phrase while the label was trimmed afterwards, so *"12.5mm
plasterboard on a metal furring system with 100mm mineral wool in the void"* was drawn as mineral
wool, a 50mm clear cavity as brickwork and 150mm of joists as insulation. **The hatch now follows
the trimmed label**, falling back to the fuller phrase only when the label names no material, so
the two always agree. Five more classes came out of the same pass:

- **An "or" before the figure marks a choice, not another band** — but only where the option
  before it was itself recorded, and within 120 characters. Without that guard, "an independent
  stud lining or 72.5mm insulated plasterboard" lost its only layer.
- **A sentence that works something out is specification up to the verb and arithmetic after it.**
  "72.5mm K118 board ... calculates at 0.28 and 62.5mm board on a cavity wall at 0.28" — the first
  figure is real, the second is the answer. Refusing the whole sentence emptied five retained-
  element build-ups; refusing only what follows `calculat|achiev` gets both right. **W/mK cannot
  be the test**: it appears in perfectly good layer phrases.
- **Three dimensions makes a component, not a section.** `500 x 500mm x 700mm minimum set into the
  slab` is a sump; a section through the floor does not cut it.
- **A cavity is read once.** The clause states it in the build-up paragraph and mentions it again
  paragraphs later ("ties of the length specified for a 150mm cavity in BS EN 845-1"), so the
  cavity figures are carried across paragraphs in `state` — `layers_from()` is called per
  paragraph, and a set that reset each time could not see the first mention. That wall was drawn
  515.5mm against a real 365.5.
- **Labels stop at `on` too**, so "100mm concrete on hardcore" is concrete rather than hardcore —
  `hatch_for` matches hardcore first.

After all of it: **0 FAIL, 0 warn, 341 layers, one build-up still flagged as implausibly thick**
for someone to read. Watch for `\b` arriving as a literal backspace byte — it happened again here,
in `BARE_CAVITY`, and the rule compiled and silently never fired. Use the editor, not a shell
heredoc, for anything containing a regex escape.

**Two recoveries are probably duplicates, and both need an eye before issue**: `loft / Hip to
Gable — New Gable Wall` (402.5mm) and `newbuild / Suspended Timber Ground Floor — Insulation
Between Joists` (542mm). In each the clause restates the build-up in a later sentence, or offers
an alternative across a comma, and one sentence cannot see the other. **Reading two thicknesses
out of one sentence cannot always tell an extra layer from an alternative**, so `verify()` also
prints every build-up that has come out implausibly thick for its group rather than pretending
otherwise — 6 today. Those totals are the ones to check against the clause before issuing.

Watch the regexes in that file. On 7 September 2026 the `` word boundaries in `HATCH` arrived as
literal backspace bytes (0x08 — what `` means in a *non*-raw string), so four rules compiled fine
and silently never matched: sand blinding was hatched as the membrane it protects. Nothing failed,
the answer was just wrong. If a hatch looks wrong, check for control characters in the pattern
before anything else.

### Issue sheets — `docgen/sheet_buildups.py`

`python docgen/sheet_buildups.py [type] [group]` writes an A4 sheet per build-up to
`output/sheets/<type>/<REF>_<title>.pdf`, printed from HTML through Playwright. 109 sheets.
**This is the PDF to issue**; `dxf_buildups.py` is the CAD half and its check print is now
opt-in behind `--pdf`.

Each sheet carries the section with its annotations on the left, thermal performance and the
full specification on the right, the scale note, and a title block. Four things make it work:

- **Every annotation is quoted from the clause**, taken as the fragment starting at that
  layer's own thickness, so the drawing cannot drift from the specification. Matching whole
  sentences instead put the same opening sentence against every layer, because the opening
  sentence describes the whole build-up.
- **Walls are drawn upright and fill the column**; floors and roofs are wide and flat, so they
  get a section across the top with a **numbered key beneath**, which is how a flat build-up is
  normally read. Forcing a flat section into an upright column left it stranded in white space.
- **Wall ties are drawn only where the clause specifies them**, at the centres it gives, with
  the fall to the outer leaf it requires. A tie drawn level, or falling inwards, teaches the
  wrong thing.
- **The title block names the practice USING the tool, and the generator hard-codes none.**
  It reads a profile: `--practice <file.json>`, else `SPECLINE_PRACTICE`, else
  `specline-practice.json` in the directory **above the repository** (where it cannot be
  committed or shipped), else placeholders. `--practice brand` opts explicitly into
  `docgen/brand_inhouse.py` for SY Design Studio's own in-house documents. In the hosted app
  the same details come from the `practices` row for the signed-in account. The lookup itself
  is `docgen/practice.py` — see "The practice on a generated document" below.
  Baking SY Design Studio into the generator was exactly the bug the commercial rule exists to
  prevent — no technologist will issue a drawing to building control under another company's
  name. **With no profile the title block prints `[Practice name]`**, which is the safe
  failure: a blank gets corrected, someone else's name might not.
  Practice name, address and email fill the practice cell; the designer's initials and the
  current month fill *date / drawn*; the responsibility note names the designer. Project,
  client and job number are never filled from anywhere — they belong to a job, and these are
  library details, so a value there would be an invented job.
- **A partition is drawn in plan, with its studs** (`stud_zone`, `studs`). Studs march along the
  wall at their centres, so a vertical section cannot show them at all — the metal stud partition
  sheet was two lines of plasterboard and nothing else. Those sheets are captioned *typical plan
  section*, and the studs are drawn at the centres the clause gives: a C-stud as web-across-the-
  thickness with a flange at each end turned the same way, a timber stud as its full section.
- **Steel is not timber.** The `timber` hatch pattern matches "stud", so galvanised steel C-studs
  were drawn with a wood grain in four build-ups. `metal` now comes first in `HATCH`.
- **"Line both faces with 12.5mm plasterboard" is two boards** (`line_both_faces`). The extractor
  reads the figure once, so **every stud partition in the library was drawn with plasterboard on
  one side only**, which is not a partition. The phrase has to sit in the same sentence as the
  board, or "damp proof courses in both leaves" would mirror a lining that is only ever on one
  face; and a wall lined on both faces is exempted from the review's inside-out test, because it
  has no outer face.
- **A figure the window cut in half is not a layer.** Both thickness patterns carry `(?<![\d.])`.
  The 70-character window can end mid-figure — "…mineral wool infill and 12" left ".5mm
  plasterboard each side" behind it — and `finditer` then resumed on the fragment, putting a 5mm
  board that no clause mentions on two partitions. The rescue pass reads the whole figure back,
  because its run-on spans the cut.
- **A sentence offering another way to build it contributes no layers** (`ANOTHER_WAY`):
  *"Masonry partitions of 100mm blockwork may be used where…"*, *"184mm studs fully filled …
  achieve the same figure"*. Those were being drawn as extra bands of a wall built the first way.
- **A qualifier is refused only when what follows it is a condition, not a thing** (`NOT_A_THING`).
  "25mm minimum **where** the stud depth is shallower" reached a hatch through the word *stud*
  five words later — the mistake the unconditional veto exists to stop. But testing the trimmed
  label alone also refused "25mm minimum drained and ventilated cavity", a real cavity whose
  label the tail-trim had cut at *and*, and a build-up silently stopped drawing. **When a rule
  makes something disappear, find out which one before accepting the new count** — the sheet total
  dropping from 107 to 106 was the only visible sign.
- **A partial fill merges into the member zone it fills** — a 50mm quilt in a 70mm stud is 70mm of
  wall, not 120. Equal thickness cannot be the only test, but the words immediately around the
  fill must say it fills the members (`INFILLING`, using a short `_before` window), or a lining
  board inboard of the studs gets swallowed into the frame.
- **Mineral wool is not rigid board.** The `ins` rule matched the bare word *insulation*, so
  "mineral wool acoustic insulation" was hatched as a PIR board. `wool` now comes first. Gypsum
  board, fireline and wallboard are plasterboard, which they were not.
- **A phrase clipped by the 70-character window is allowed to finish.** The rescue pass searches
  the window plus a short run-on, accepting only matches that *start* inside the window. Rebuild
  that run-on from the original text and normalise once: gluing two separately-normalised pieces
  split a word ("10mm perime" + "ter gap") or welded two together ("plasterboardplank"), and the
  review caught both as lost provenance.
- **Only what sits after a working verb is working, and only when the verb is inside the same
  window.** Abandoning a whole rescue because the surrounding text mentioned achieving a target
  threw away real layers: "100mm quilt between the joists and 300mm laid cross-wise, **or
  equivalent to achieve the target U-value**" lost the 300mm — the entire top layer of a roof —
  because those three words happened to follow it. Two of these now: this and `NOT_A_THING`.
  A veto written to stop an invented band will, sooner or later, delete a real one; check what
  a new rule removes as carefully as what it catches.
- **A stud depth the clause declines to fix is drawn undimensioned** (`stud_core`). "Proprietary
  galvanised steel C-studs at 600mm centres ... to the system manufacturer's specification" gives
  the centres and defers the depth, which is correct — the depth belongs to the system. So the
  zone is drawn at a nominal width that is **never printed**, hatched as whatever the clause says
  fills it, with the studs over it, and the overall dimension is replaced by *stud depth to the
  system specification*. Printing a total measured off a nominal band would invent the one number
  the clause deliberately leaves open.
- **A pitched roof is drawn on the slope** (`pitched_svg`), with the tiles, battens and underlay
  above the structure and a break line at the eaves end. Flat roofs and warm decks stay flat,
  because they are flat. The pitch is **indicative and never dimensioned** — the library does not
  state one, and a typical section is drawn at a plausible slope the way the reference details
  are; the pitch for a job comes off the drawings. `PITCH`, `TILE`, `BATTEN` and `GAUGE` are the
  drawing constants, not specification.
- **The covering is drawn only where the clause names one**, the same rule as the wall ties. Six
  of the twenty-five roof clauses describe the build-up from the rafters inwards and say nothing
  about tiles; those get no tiles, because a drawing may not state what the specification does
  not. The covering's key entry quotes the clause from where the covering is named, not the whole
  sentence, which otherwise repeated the first layer's note word for word.
- **Rotating a section requires knowing which face is outside**, which is what `face_order()` in
  `detail_schedule.py` settles. This is why the ordering fix had to come first: four roofs were
  being drawn with the ceiling as the outermost band, and flat bands hid it.
- **A member zone and its fill merge across paragraphs too** (`merge_member_fill`). A clause names
  the rafters in the paragraph about structure and the board filling them two sentences later, so
  the per-paragraph merge inside `layers_from()` never saw the pair — the dormer roof was drawn
  150mm too thick. Drawing it on the slope is what made that obvious.
- **A full run deletes the sheets of build-ups that no longer draw.** The generator only ever
  wrote, so a build-up that stopped drawing left its last sheet in the issue folder — and that
  sheet is wrong by definition. Two sat there for a day: the external wall insulation one still
  showing the phantom 150mm band read out of *"150mm above finished ground level"*, and the
  basement party wall showing one of two conditional options as though it were the specification.
  A **filtered** run never deletes: it knows nothing about the sheets it was not asked for.
- **Long clauses are set smaller, not cut off.** The size steps on a cost that counts
  paragraphs as well as characters, because paragraph spacing is what actually fills the
  column — the longest clause in the library is only 2149 characters, so a threshold set on
  characters alone never fired and the last line vanished behind the footer.

### DXF — `docgen/dxf_buildups.py`

`python docgen/dxf_buildups.py [type] [group]` draws every build-up as a layered section and
writes `output/dxf/<type>/<GROUP>_<title>.dxf` with a `.pdf` beside it to look at. 109 of the
124 build-ups draw; the rest are skipped and say why — foundations are not a layer stack, and
four clauses state no thicknesses. `output/` is git-ignored, so regenerate rather than commit.

- **Model space is 1:1 in millimetres.** Scale lives on the paper space viewport, set to 1:10,
  matching the drawn sheets. Never scale the geometry: the point of a DXF is that someone can
  dimension off it and get the real number.
- **One layer per material**, `S-MAT-<hatch>`, plus `S-CUT`, `S-DIM`, `S-TEXT`, `S-LEAD`,
  `S-BREAK`, `S-TITLE`. Lineweight is on the layer, so the whole drawing can be re-penned by
  editing layers.
- **Masonry is drawn with real bed joints** at real centres — brick 75, blockwork 225 — not a
  hatch pattern, and with no fill. A solid fill becomes a black bar the moment the set is
  printed in monochrome, which is how building control usually prints it.
- **Dimensions are geometry, not DIMENSION entities.** These regenerate from the library, so
  nobody edits them by hand, and an associative dimension renders as bare extension lines in
  every viewer that does not implement dimension blocks in full — including the check print.
- **All text goes through `ascii_()`.** The library is written with `²`, `—` and `·`, and CAD's
  standard SHX fonts have none of them; unconverted they land on the drawing as empty boxes.

It draws build-ups, not junctions. A junction is a decision about how insulation, the damp
proof course and the fire separation resolve where two build-ups meet — see
`reference/details/detail-register.md` for which are worth drawing and which are drawn.

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
- **Word export.** `src/docx.js` writes a `.docx` directly: a ZIP of OOXML parts, stored rather
  than deflated, with no npm package and no CDN script, so it works offline in the tests.
  `buildDocx()` in `app_js.js` mirrors `buildPdf()` section for section, including the practice
  logo as an embedded image, the cover table, the schedule, Part A, Part B and the U-value
  working. `makeDoc(fmt)` is the single download path for both formats. Word keeps the `²` and `—`
  characters that the PDF has to map through `safe()`, so the Word file is the better one to edit.
  `tests/test7.py` opens the result with python-docx, the same library the practice generator uses,
  so a file Word would reject fails the build.
- **Foundations** (`src/configurator3.js`, group `FD`): 11 library build-ups (trench fill and strip in
  the five types with a foundations category, plus a raft for a single-storey extension), and a
  configurator for a bespoke one. It does **not** calculate — a foundation width comes from Approved
  Document A Table 10 or the engineer, and **those values are deliberately not held here**. It
  checks a proposed foundation against Section 2E (projection vs thickness, the 150 mm floor,
  trench fill width, step overlap, depth by subsoil) and shows the working. Raft and piled produce
  an engineer's-design entry with no dimensional check. Every generated entry carries a NOTE to
  confirm the width against Table 10, and a failing check becomes a NOTE on the entry rather than
  being silently dropped. The schedule's Standard column carries the summary ("600 × 225, 1000
  deep") in place of a U-value. Figures are in `reference/FACTS.md`.
- **Practice profile** (`P` in `app_js.js`, route `practice`): name, named designer, address,
  email, phone, logo as a data URI with its pixel size, plan (`solo` | `practice` | `payg`) and a
  list of users, and the practice's own accent colour. **Nothing is seeded from a compiled-in
  practice**: `PRACTICE_BLANK` is empty, `PRACTICE_BASE` is the signed-in account's practice
  injected by `app.php`, and a saved profile is merged over that — kept in localStorage under
  `specline-practice` and in db doc `practice/profile`. The preview cover, the PDF cover, the
  running footer and the responsibility statement all read from `P`, through `pName()` so an
  unfilled cover reads `[Practice name]`. `coverNotice()` builds the
  two-paragraph "ISSUED FOR BUILDING CONTROL APPROVAL" block in the practice's voice; the same
  `resp` paragraph shows on the Review and issue step before the PDF is produced. Seats are shown
  against the plan limit and not enforced.
- The chrome lockup is brackets as inline SVG and the wordmark as text (`.lockup`), per the
  identity sheet. Archivo 700 for the wordmark only; `--brand-ink` / `--bracket` carry its colours
  in both themes. `src/logos.js` holds the Specline icon data URIs and nothing else.
- **Two configurators can share a category.** External Walls carries the cavity wall and the
  framed wall. Their selects are namespaced — `data-cf="cavity"` against `data-cf="fr_*"` — and
  each binder scopes itself to the card holding its own Add button. Do not reintroduce a bare
  `document.querySelector(".cfgcard")`; test4 scopes its chip assertions with
  `.cfgcard:has(#addWall)`.
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

- Parametric timber frame walls, dormer cheeks and internal linings — these are still fixed
  build-ups while cavity walls, floors, basements and roofs are configurable.
- Wales as a second region (different Part L/F targets and a separate notional dwelling).
- Rebuild the A102 General Notes drawing sheet, which still cites withdrawn standards
  (BS 5950, BS 5628, BS 6206, BS 5588-9) and carries another practice's name.
- Embed a font in the PDF export if the documents are to go to unknown recipients. The `²`/`³`
  characters *are* in the file; some viewers substitute a font that lacks the glyph because the
  standard PDF fonts are referenced rather than embedded. Costs roughly 300 KB per file.

- **Billing.** Accounts, the admin dashboard, the regulations watch and the tool behind the
  login were all built on 6 September 2026 (see "Accounts, administration and the regulations
  watch" above). Jobs are now stored per practice on the server. What is left before a
  subscription can be sold is a payment processor and a solicitor's look at the terms.
- Reissue the SSL certificate for `specline.co.uk` to cover `www` as well. The handshake fails on
  `www` today, so the redirect in `.htaccess` never gets a chance to run.
- Delete the leftover `site/` folder from `public_html`; it serves a duplicate of the home page.

**The two figures left unconfirmed are now confirmed, and both were wrong.** Checked on
6 September 2026 against the published Approved Documents, downloaded and read directly rather than
searched. Both corrected the same day:

- **Basement fire resistance.** The library said the floor over the basement goes to 60 minutes
  where the basement is more than 10 m deep or the house has more than one basement storey. Neither
  trigger exists. **Table B2** of AD B Volume 1 gives a dwellinghouse basement storey 30 minutes and
  marks depths over 10 m *not applicable*, because note 4 puts a house with a 10 m basement outside
  the scope of the dwellinghouse guidance altogether. More than one basement storey is covered by
  footnote `*`: the floor over the **topmost** basement takes the higher of the basement-storey
  period and the ground-or-upper-storey period. The clause now states all three of those.
- **Car park ventilation.** The library said openings of 2.5 per cent of the floor area, half at
  each of two opposite sides. **AD F Volume 2 paragraph 1.39** says a minimum aggregate equivalent
  area of **1/20** — 5 per cent, double what we specified — with 25 per cent of that aggregate on
  each of two opposing walls. Paragraph 1.38's carbon monoxide limits (30 ppm over 8 hours, 90 ppm
  over 15 minutes) are the primary route and were missing entirely. The mechanical figures were
  also misattributed: AD F's ten air changes are for exits and ramps where cars queue, not for smoke
  clearance. Smoke clearance, the 300 °C fan rating and the secondary supply are in **Section 11 of
  AD B Volume 2, which this library does not hold** — that part is now a NOTE to obtain before
  issue rather than a stated figure.

The lesson is worth keeping: "conservative as written" was assumed for both and was true for
neither. The basement clause over-specified, and the car park clause specified **half** the opening
area the Approved Document requires. An unconfirmed figure is not safe merely because it sounds
cautious — confirm it or flag it, and never split the difference.

## Brand — Specline

The product is sold as **Specline**, separately from SY Design Studio. Tokens live in
`src/tokens.css`; the identity sheet (mark, rationale, component specs) is the reference.

**The commercial rule:** Specline brands the *application*. The specification the app generates
carries the subscribing practice's own logo, name and address — never Specline's and never SY
Design Studio's. No technologist will issue a document to building control under another company's
brand. Treat any Specline mark appearing on a generated cover page, running header or footer as a
bug.

- **Colour.** Warm detail paper `#F4F3F0` against cool drafting ink `#10191F`, with deep petrol
  `#0E6E85` as the single accent (`#3FA6BE` on dark). Green/red/amber are semantic only — pass,
  fail and "confirm before issue" — and never do brand duty. **No SY Design Studio orange.**
- **Type.** IBM Plex Sans for everything read, IBM Plex Sans Condensed for uppercase micro-labels,
  IBM Plex Mono for anything measurable — references, U-values, thicknesses. Always
  `font-variant-numeric: tabular-nums` where figures align in a column.
- **Measure.** 4px base. Radii 2/4/6/10 — tight, because a precision instrument should not look
  soft. Divide with 1px hairlines before reaching for a card, and a card before a shadow;
  `--shadow-2` is for menus and modals only.
- **Themes.** Define the full light palette on bare `:root`, redefine tokens under
  `@media (prefers-color-scheme:dark)` guarded as `:root:not([data-theme="light"])`, and again under
  `:root[data-theme="dark"]`. Never style a component inside a theme block. The A4 preview stays
  true white in both themes — it is paper, not chrome.
- **Status.** Never colour alone. The figure goes in the label: "Meets 0.18", not a green tick.

## Deployment — specline.co.uk

The marketing site is `site/`. **Upload the CONTENTS of `site/` to `public_html`, never the
repository.** The document root must hold `index.html` and `.htaccess` and nothing else from this
repo.

The repository must never sit in a public web root. It carries the clause library (`data/`), this
brief with the pricing and the founding-member strategy, `reference/FACTS.md`, and
`docs/TERMS-DRAFT.md`, whose own first line says it must not be published. On 6 September 2026 the
whole repo was uploaded to `public_html` by mistake: the home page answered at `/site/index.html`,
the domain root returned 403 to every visitor, and all of the above were readable over HTTPS.
`.git` was blocked by the host, so the history was not exposed.

**Hostinger deploys this repository into `public_html` on every push to `main`, so the repository
root IS the web root.** Nothing is ever uploaded by hand — a manual upload is wiped by the next
deployment, which is exactly what happened on 6 September 2026. The root `.htaccess` is what makes
a code repository safe to serve: it rewrites everything into `site/`, so `/` is the home page and
`/CLAUDE.md`, `/data/…`, `/reference/FACTS.md` and `/docs/TERMS-DRAFT.md` all 404. **If that file
is removed or the deployment target changes, the whole repository goes public again.**

The site is four files: `index.html`, `terms.html`, `privacy.html` and `waitlist.php`, plus
`.htaccess`. The waiting list posts to `waitlist.php`, which validates, rate-limits by IP, and
appends to `../../specline-waitlist.csv` — the domain directory **above `public_html`**, which is
never web-served and which a deployment never touches, so the list survives every push —
then emails Specline. Read the list by downloading that CSV over SFTP or File Manager.
Reply-To is the signup's address. The signup is stored whether or not the mail is delivered.

Terms and privacy are published and **drafted in-house, not reviewed by a solicitor**. Both say so
on the page. `docs/TERMS-DRAFT.md` is the brief they were written from, kept for the solicitor.

`site/.htaccess` is defence in depth, not the fix: it disables directory listing, refuses dotfiles
and source extensions, 404s the repo directories, folds `www` into the apex and forces HTTPS.

## Accounts, administration and the regulations watch

Built 6 September 2026 as PHP under `site/`, because the artifact cannot do it: the Claude
artifact's `user` capability is not available on this account, so per-viewer identity is
impossible inside it. Authentication therefore lives on specline.co.uk, and the artifact stays
the tool.

```
site/app/bootstrap.php   config, database + schema, session, CSRF, throttle, mail, layout, guards
site/app/regwatch.php    the 19 Approved Documents, gov.uk fetch/parse, citation mapping
site/account/            signup, login, logout, verify, forgot, reset, index (the account page)
site/admin/              index, signups, waitlist, messages, regs, settings, setup
site/contact.php         message capture   ·   site/cron.php   the scheduled check
site/static/ui.css       one stylesheet, the same tokens as the home page
```

**All data lives above `public_html`** — `specline.sqlite`, the setup key, the optional
`specline-config.php`, and the waiting list CSV that was already there. Hostinger redeploys the
repository into the web root on every push, so anything kept inside it is destroyed. `DATA_DIR`
resolves to the directory above the repository and can be overridden with `SPECLINE_DATA_DIR`
for local testing. SQLite by default; put a `mysql` key in the config file to use MySQL instead.

- **No default administrator.** `admin/setup.php` writes a random key to a file above the web
  root; whoever can read that file over SFTP can claim the owner role once, and the page then
  closes itself. There is no hard-coded password anywhere.
- **Security.** `password_hash`/`password_verify`, per-session CSRF tokens checked with
  `hash_equals`, sliding-window throttles on login (8 per address and 20 per IP per 15 minutes),
  signup, contact and password reset, session id regenerated on login, cookies `HttpOnly` +
  `SameSite=Lax` + `Secure` over HTTPS, tokens stored only as SHA-256 hashes, and a CSP.
  Sign-in, sign-up and reset all answer identically whether or not an address exists, so none of
  them can be used to test whether someone has an account. `site/app/` is denied by `.htaccess`
  **and** by a guard inside the files, so a server that ignores `.htaccess` still cannot fetch
  the configuration.
- **`DirectoryIndex` must list `index.php`.** Both `.htaccess` files set it explicitly, and
  `/account/` and `/admin/` are 403 without it.
- **Messages are not an inbox.** The contact form stores to the database and emails
  info@specline.co.uk with the sender on Reply-To. Mail sent *directly* to the mailbox is read in
  the mailbox, not here; this page only holds what came through the form. The dashboard says so.

**The regulations watch does not edit the library, and must not be made to.** It fetches each
Approved Document's gov.uk publication page once a day, fingerprints the set of attachment
addresses plus the page's latest update date, and raises a reviewable event when that moves. It
then lists the clauses in each project type that name the document, so the review has a
checklist and the decision has an audit trail. It stops there **because of non-negotiable 1**:
gov.uk can tell you a PDF was replaced, it cannot tell you that a limiting value moved from 0.18
to 0.16, and a program that inferred the new wording would be inventing figures for documents
that go to building control. The machine notices; a person writes the clause in `data/`.

Two honest limits, both stated on the page: the citation count is a **floor**, because a clause
can be governed by a document without naming it; and car park smoke clearance, fan ratings and
anything else in a volume the library does not hold stays a NOTE to obtain, never a stated
figure. The check also runs opportunistically when the dashboard is opened and a day has passed,
so it works before any cron job exists; Settings generates a token-protected URL and a CLI
command for a real scheduled task.

### Proposed edits (`site/app/proposals.php`, `admin/proposals.php`)

Drafts the library changes that follow from a document moving, for a person to accept or refuse.
Three rules define it, and all three are load-bearing.

1. **It drafts only what it can ground in something it has actually read.** Today that is the
   edition a clause names: gov.uk's attachment titles carry the year, so if a clause says
   "Approved Document L Volume 1, 2021 edition" and the page now attaches `ADL1_2026.pdf`, the
   replacement is four digits and the evidence is the attachment title, quoted on the proposal.
   Where the library itself records a commencement date, that sentence is quoted too — the
   drafted AD L edits carry "Approved Documents L1 and F1, 2026 editions, come into force on
   24 March 2027" and say not to approve until then. **Published is not in force.**
2. **It never drafts a figure.** A U-value, fire period, ventilation rate or percentage can only
   be changed by reading the amendment, and it cannot read the amendment. That is not laziness:
   the Approved Documents are PDFs whose text sits behind subsetted font encodings, and this was
   tested — PHP inflates the content streams fine (350 of 359 on AD O) and gets custom font codes
   out, not words, so decoding needs a real font-CMap parser. Inferring a figure from a filename
   or a change note would breach non-negotiable 1. Clauses stating figures are listed for reading
   instead, with their figures extracted so the reviewer knows what to check, and no wording
   proposed.
3. **Approving does not write to `data/`.** The server holds a deployed copy that the next push
   overwrites, so an edit made there would vanish without reaching git, the structural check or
   the 192 assertions. Approved proposals export as an **assert-based Python script** — the same
   shape as the edit scripts already used in this repo — run in the working copy, then
   `build.py --test`, then commit. The generated script checks every replacement **before it
   writes anything**, so a proposal drafted against a clause that has since changed stops the
   whole run rather than half-applying it.

Measured on the current library: 1207 clauses parse, all attributed to a project type and a
clause title; six clauses name an edition, of which the four saying 2021 draft correctly and the
two already saying 2026 are skipped. Watch the year regex — it is `(?<![0-9])(?:19|20)\d{2}` and
not `\b…\b`, because the year in `ADL1_2026.pdf` follows an underscore, which is a word
character, so `\b` never matches and every new-edition file is missed.

### The specification tool behind the login

Built 6 September 2026. `/app.php` is the gate and the only way to the tool: it checks the
session, then reads `site/app/spec.html`, so an unauthenticated request never receives a byte of
the app. That file is denied to the web by `site/app/.htaccess`.

- **`site/app/spec.html` is generated AND committed**, unlike everything in `dist/`. Hostinger
  deploys the repository, so only what is committed reaches the server. `build.py` writes it on
  every run, along with `site/static/jspdf.js` (copied from `src/vendor/`, so the app pulls
  nothing from a CDN). Never edit either by hand.
- **`src/serverstore.js`** provides the same tiny interface the artifact's `db` capability gave
  — `doc(path).get/set/delete` and `collection("jobs").limit(n).get()` — over `/api.php`. That is
  why **not one line of the app's own save, load or delete logic changed**. It activates only
  when `window.SPECLINE` is present, which `app.php` injects; opened any other way the app falls
  back to localStorage exactly as before, which is what keeps the Playwright suites working
  against `dist/preview.html`.
- **`/api.php` scopes every row by the practice on the session, never by an id from the client.**
  A job id does arrive from the browser, but only ever inside a `WHERE` that also pins
  `practice_id`. Verified by test: a second practice reading, listing, overwriting and deleting
  another's job gets null, an empty list, a refusal, and no effect. This is the per-practice
  separation the artifact could never have, because it had no idea who was looking at it.
- **Before launch there is one lock** (`site_lock`, in Settings): no new sign-ups, and nobody
  but the owner may sign in. One switch rather than two, so "the site is not open yet" cannot
  end up half true. The waiting list stays open, which is the point of being closed.
  `site/index.php` is PHP for this reason alone — its sign-up button follows the lock instead of
  needing an edit at launch.
  **Enforce it in `login_user()` and nowhere else.** Three paths create a session — signing in,
  verifying an address and completing a password reset — and when the check lived only in
  `login.php` a password reset signed a non-owner straight past it and into the tool. Found by
  testing the reset path on 6 September 2026 and fixed the same day: `login_user()` now returns
  false and creates nothing when it must refuse, so a caller cannot forget.
- **Access is shut by default** (`app_open` = `admin`; also `verified` or `closed`), set in
  Settings. Deploying the tool must not by itself hand it to everyone who has signed up. Closing
  it hides the tool and deletes nothing.
- Tables: `jobs` (the app's own snapshot in `payload`, with type, job number, title and revision
  beside it purely so this side can list and count) and `practice_profile`.
  `practices.contact_email` is the address printed on the specification and it belongs to the
  **practice**, not to whoever is signed in — it was taken from the user's login until
  6 September 2026, which meant a second person in the same practice changed the cover of every
  document. Blank falls back to the login.
  **`CREATE TABLE IF NOT EXISTS` does nothing to a table that already exists**, so a column added
  later needs the ALTER step at the end of `migrate()` and a bump of `SCHEMA_VERSION`, or it
  silently never appears on a database that is already built. Saving the profile
  also writes name, designer, address and phone back to `practices`, so the account page and the
  specification cover cannot drift apart.

Still not built: billing. A payment processor and a solicitor's look at
`docs/TERMS-DRAFT.md` are what stand between this and selling a subscription.

## Mail — info@specline.co.uk

A real mailbox exists on the domain since 6 September 2026, and everything the site sends now
comes **from** it, with `-f` setting the envelope sender as well as the header so bounces return
to it and SPF is checked against an address that exists. `mail_from()` in `bootstrap.php` and
`MAIL_FROM` in `waitlist.php` are the two places; the config file above `public_html` can
override the first with a `mail_from` key.

Before that date no From header was set anywhere, deliberately: there was no mailbox, and mail
claiming to come from an address that does not exist is commonly dropped. That is why account
**verification emails were unreliable**, which mattered because verification is what lets a new
practice in. If verification mail starts bouncing again, check SPF and DKIM for specline.co.uk
before changing anything in the code.

**The clause library must never name a company.** It named SY Design Studio Ltd in thirteen
places until 6 September 2026 — "adopted as SY Design Studio Ltd's standard", "read in
conjunction with the SY Design Studio Ltd drawing pack" — and that text prints on *every*
subscribing practice's specification, so another practice's document told building control to
refer to a company with no involvement in the job. It is now practice-neutral wording ("this
practice's standard", "the drawing pack issued with this specification", "the designer"), **not**
"Specline": Specline is the software, not the designer, and `tests/test7.py` asserts that the
word never appears on a generated document. The practice's own name is already on the cover, the
running footer and the responsibility statement, so naming it inside a clause was redundant too.

Two things that legitimately still say SY Design Studio Ltd, and must:
- **The legal entity** in the terms, the privacy notice and the site footer. It is the data
  controller and the contracting party, and a company must disclose its registered name on its
  website. "Specline" is a trading name, not a legal person.
- **The practice profile** — `specline-practice.json`, `docgen/brand_inhouse.py` and the practice
  row in the database. That is *the subscribing practice*, and it is what
  building control reads on the cover. Putting "Specline" there would be the bug the commercial
  rule exists to prevent. Note where those live: none of them is inside a generator.

## Commercial model

**Subscription only. Never a one-time licence.** The Approved Documents change: L1 and F1 2026
editions come into force on 24 March 2027, and there will be more. A perpetual licence would
commit us to maintaining a regulatory library forever for a single payment. Recurring revenue is
what matches a product whose value is being current.

| Tier | Price, ex VAT | What it covers |
|---|---|---|
| Solo | £39/month or £390/year | 1 user, all 8 project types, unlimited specifications |
| Practice | £89/month or £890/year | up to 5 users, shared job library, the practice's own added clauses |
| Per spec | £25 per issued spec | no subscription |

Annual is ten months' money. Founding-member pricing is locked for life for the first 30
subscribers.

Rules, because they constrain the build:

- **White-labelling is in every tier, including Per spec.** A specification a practice cannot put
  its own name on is not a product. Gate seats and custom clauses, never the practice's own
  identity on its own document.
- **Three per-spec purchases must cost more than one month of Solo** (3 × £25 = £75 > £39), so the
  cheap option pushes upward rather than replacing the subscription. Re-check this whenever a
  price moves.
- **Do not build payment processing yet.** Build the seams only: the practice profile, the plan
  field, the seat count shown against its limit. Billing comes after a solicitor has reviewed
  `docs/TERMS-DRAFT.md`.
- **The software drafts; building control approves.** Nothing in the app, the documents or the
  marketing may say or imply that Specline certifies, approves or guarantees compliance. The named
  designer remains responsible for the specification's suitability on the job.

## Regulatory horizon

Approved Documents L1 and F1 **2026 editions** were published on 24 March 2026 and come into force
on **24 March 2027**, with transitional relief for new dwellings commenced before 24 March 2028.
Every specification carries the flag. The library will need a full pass against the new editions
during 2027 — that is a rewrite of the Part L and Part F content, not a patch.
