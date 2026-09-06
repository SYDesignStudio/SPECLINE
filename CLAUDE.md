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
  configurator3.js      foundation configurator (UI) — checks, not a calculation
  configurator4.js      framed wall configurator (UI) — timber frame, dormer cheeks
  ucalc3.js             UC.frame: studded walls, combined method for stud bridging
  ucalc.js              UC: materials with verified conductivities + wall calculations
  ucalc2.js             floors (BS EN ISO 13370), heated basements, three roof types
  docx.js               DOCX: a dependency-free .docx writer (ZIP + OOXML), used by the app
  logos.js              SPECLINE_ICON (app chrome, favicons) and PRACTICE_SEED_LOGO (this installation)
  vendor/jspdf.local.js local jsPDF, used only by dist/preview.html for offline tests
docgen/               Word + PDF generation (python-docx, LibreOffice for the PDF step)
  spec_from_data.py     the generator: one .docx + .pdf per type, straight from dist/specdata.js
  brand.py, build_spec.py   cover page, headers, house typography
  plancheck_report.py, dedupe_report.py   the two QA reports already issued
tests/                seven Playwright suites, 185 assertions
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
- The cladding on a framed wall sits outside a ventilated cavity, so BS EN ISO 6946 §6.9.3
  requires it and the cavity to be disregarded with the external surface resistance taken as still
  air. The outer finish therefore changes the prose and the boundary check, not the U-value.
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
  list of users. Seeded from `PRACTICE_SEED` (this installation), kept in localStorage under
  `specline-practice` and in db doc `practice/profile`. The preview cover, the PDF cover, the
  running footer and the responsibility statement all read from `P`. `coverNotice()` builds the
  two-paragraph "ISSUED FOR BUILDING CONTROL APPROVAL" block in the practice's voice; the same
  `resp` paragraph shows on the Review and issue step before the PDF is produced. Seats are shown
  against the plan limit and not enforced.
- The chrome lockup is brackets as inline SVG and the wordmark as text (`.lockup`), per the
  identity sheet. Archivo 700 for the wordmark only; `--brand-ink` / `--bracket` carry its colours
  in both themes. `src/logos.js` holds the Specline icon data URIs and the practice seed logo.
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

- **Billing, and moving the tool behind the login.** Accounts, the admin dashboard and the
  regulations watch were built on 6 September 2026 (see "Accounts, administration and the
  regulations watch" above). What is still missing is a payment processor and per-practice
  separation of job data, because the specification tool itself is still the single Claude
  artifact rather than a hosted application. That is the next build.
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
then emails the studio. Read the list by downloading that CSV over SFTP or File Manager.
The notification sets no From header on purpose: an address that has no mailbox behind it is
commonly dropped by the receiving server, so the MTA's own sender is used, which SPF already
covers. Reply-To is the signup's address. **No mailbox is needed on specline.co.uk**, and the
signup is stored whether or not the mail is delivered.

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
- **Messages are not a mailbox.** The contact form stores to the database and emails the studio
  with the sender on Reply-To. There is still deliberately no mailbox on specline.co.uk, so mail
  sent directly to an address there is not collected. The dashboard says so on its face.

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
   the 185 assertions. Approved proposals export as an **assert-based Python script** — the same
   shape as the edit scripts already used in this repo — run in the working copy, then
   `build.py --test`, then commit. The generated script checks every replacement **before it
   writes anything**, so a proposal drafted against a clause that has since changed stops the
   whole run rather than half-applying it.

Measured on the current library: 1207 clauses parse, all attributed to a project type and a
clause title; six clauses name an edition, of which the four saying 2021 draft correctly and the
two already saying 2026 are skipped. Watch the year regex — it is `(?<![0-9])(?:19|20)\d{2}` and
not `\b…\b`, because the year in `ADL1_2026.pdf` follows an underscore, which is a word
character, so `\b` never matches and every new-edition file is missed.

Still not built: billing, and per-practice separation of job data — the specification tool is
still the single Claude artifact. Accounts are the seam for moving it behind a login, which is
the next build.

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
