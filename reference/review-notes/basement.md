# Basement Conversion (`SPECS.basement`) — review and fix report

Data file: `/tmp/claude-0/-home-claude/5a43e098-d0a9-5b03-b512-8af8f345320b/scratchpad/specdata_basement.js`
Fix script: `/tmp/review/fix_basement_review.py` (run; JS re-evaluated with node afterwards)

## (i) Verdict

Would pass a building control plan check once the fixes below are applied. The technical core was already sound: BS 8102:2022 Grade 3 with two forms of protection, hit-and-miss underpinning sequence with bay limits and dry-pack, sump with duplicate pumps / battery back-up / high-level alarm, escape from a basement habitable room by egress window or protected stairway (matches AD B Vol 1 para 2.16), REI 30 floor over, Part K stair, correct AD L Table 4.2/4.3 U-values, Reg 16 notices and the 2026-edition transition flag. The defects were the same pattern as the House Extension: the shared detail notes had been appended without removing the older general notes (staircases x2, ventilation x2, heating x2, Regulation 16 x2), one outright wrong clause (the obsolete 75%-of-fittings lighting rule), a paragraph about doors and windows sitting inside the foul drainage note, the escape-window cill stated as a hard 800–1100 mm band, and FD20 doors where the firm's FD30S doorset standard applies.

## (ii) Findings and fixes

1. **Regulation 16 duplicated** — "Statutory Notices and Houses in Multiple Occupation" (two-day / five-day notices, basement inspection stages, HMO) and the appended "Regulation 16 Notices — Commencement and Completion" (same notices in full, generic inspection stages). Merged into one General Notes note, "Regulation 16 Notices, Inspections and Completion Documents": the full Reg 16 text once, the basement-specific inspection stages (underpinning bays before concreting, waterproofing before covering, reinforcement before pours, pumping on test) in place of the generic list, and the basement handover documents (waterproofing design statement and guarantees, pump commissioning record, maintenance schedule) folded in. Inspection stages now worded as "as the building control body's inspection schedule sets out" rather than as statutory stage notices. The HMO sentences moved to the fire note (item 8).
2. **Staircases duplicated** — "Stair to the Basement" and the appended "Staircases — Detail" restated the same Part K figures. Merged into "Stair to the Basement": basement-specific content kept (loft headroom relaxation does not apply; steep retained cellar stair must be brought up to standard; enclosure where a protected stair is needed), detail folded in once (handrails both sides at 1 m width, 600 mm between handrails, tapered treads, landings, BS 585, 0.36 kN/m guarding load).
3. **Ventilation duplicated** — "Ventilation of Basement Rooms" and "Ventilation — Approved Document F Figures, Systems and Commissioning" both gave the 8000 mm², 1/20 purge, extract rates and 10 mm undercut. Merged into "Ventilation of Basement Rooms — Approved Document F": basement logic (window to a lightwell → System 1; no window / small lightwell / AP <5 → System 3 or MVHR for the whole basement; no open-flued appliances) kept, with the AD F figures stated once each (1/10 for 15–30°, 4000 mm² wet rooms, ≥1700 mm, System 3 4000 mm² ventilators, continuous 13/8/6, 0.3 l/s/m², intermittent 15/6/30 and 30/60 kitchen, cooker hood 650–750 mm, duct rules, commissioning results to building control within 5 days). The "check openable areas against the window schedule" designer prompt kept.
4. **Heating duplicated** — basement "Heating and Hot Water" (TRVs, no boiler/cylinder below the sump alarm level, gas in ventilated ducts) and the appended shared "Heating Systems — Boilers, Heat Pumps, Underfloor Heating and Hot Water". Merged into one Services note with the basement paragraph first. The shared text was correct on Part G (bath supply ≤48°C by TMV to BS EN 1111/1287); added the G3 cylinder "stored at not less than 60°C" clause from FACTS, the Gas Safe/OFTEC/HETAS sentence, pipework outside the heated envelope to Table 4.4, and tied the UFH paragraph to the Basement Floors build-ups (pipes clipped to the floor insulation) instead of the intermediate-floor R 0.75 figure which does not apply to a ground-bearing basement slab.
5. **Misplaced paragraph** — the third paragraph of "Foul Drainage from Below Sewer Level" was about internal doors, lightwell window U-values and safety glazing. Removed from the drainage note and made a new note "Internal Doors, Lightwell Windows and Safety Glazing" under Internal Works (a category that previously had a build-up but no note). Safety-glazing critical locations attributed to Approved Document K / BS EN 12600.
6. **Wrong lighting clause** — "Not less than 75 per cent of new light fittings to be low energy with an efficacy of 75 lumens per circuit watt" → AD L Vol 1 2021: all new fixed internal and external lighting ≥75 lumens per circuit-watt, fittings under 5 circuit-watts excluded; external (lightwell/stair) lighting off in daylight and when not needed by photocell + presence detector/time switch; fire-rated recessed fittings in the REI 30 ceiling cross-referenced.
7. **Alarm grade statement** — "Smoke Detection and Fire Resistance" specified Grade D1 LD2 (correct) but did not say it exceeds the AD B minimum. Now: "Grade D1 Category LD2 … which exceeds the Grade D2 Category LD3 minimum in Approved Document B Volume 1 and is SY Design Studio Ltd's standard".
8. **HMO / rented alarms** — HMO content that was in the statutory-notices note (own escape window or door for a basement HMO bedroom, D1 LD2 or LD1, confirm occupation before fixing the fire strategy) folded into the rented-dwellings alarm note, retitled "Smoke Alarms in Rented Dwellings, HMOs and Large Dwellings", with the previously repeated LACORS/HMO sentence stated once.
9. **Escape window cill** — "bottom of the openable area between 800mm and 1100mm" → "not more than 1100mm above the floor (and not less than 800mm unless guarding to Approved Document K is provided), openable without a key from inside" (FACTS / AD B).
10. **Fire doors** — FD20 in the Means of Escape note, the misplaced doors paragraph and build-up IW1 → "FD30S fire doorsets (E 30 Sa, intumescent strips and cold smoke seals) with self-closer", stated as the firm's standard adopted in place of the FD20 minimum that the document already cited for a dwellinghouse protected stairway.
11. **Fire resistance period stated twice** — the "30 minutes (60 where the basement is more than 10m deep or the house has more than one basement storey)" rule appeared in both "Lintels, Beams and Fire Protection" and "Smoke Detection and Fire Resistance". The beams note now says "the same period of fire resistance as the floor over the basement (30 minutes, as the Means of Escape & Fire Regs note)". See (iii) on the 60-minute wording itself.
12. **Linings / cavities wording** — B-s3,d2 was limited to "the stair enclosure where it is a protected stairway"; AD B Vol 1 Table 4.1 requires B-s3,d2 in circulation spaces generally, so now "in the circulation space at the foot of the stair and in the stair enclosure". The reference to "Section 9" for cavity barriers replaced by "the concealed-spaces provisions of Approved Document B Volume 1" because section numbering differs between the collated editions (the 2025-collated PDF places cavities in Section 5).
13. **DPC stated three times** (Above-Ground Portions note, Additional Notes for Walls, build-up EW1). The walls note now cross-refers to the Above-Ground Portions and Junctions note for the 150 mm DPC and adds the PD 6697 tie rule (2.5/m²; 300 mm vertical centres within 225 mm of jambs and movement joints) that was missing.
14. **Sump specification repeated** in build-up BF1 and "Pumps, Sumps and Maintenance". The note now refers to BF1 for the chamber/pumps/battery/alarm specification and keeps only the operational items (alternation, discharge route, commissioning, maintenance).
15. **Ceiling height** — "should have a clear ceiling height of not less than 2.3m and the stair headroom of 2m" read as if both were regulatory. Now states that the Regulations set no minimum room height, 2.3 m is for amenity, and the 2 m stair headroom is the Part K requirement.
16. **BS 8102 NOTE** said Type C is "the second line in every build-up", but build-up BW2 (retained masonry wall) uses Type C as the primary protection. Reworded to "as the second line of protection to a new wall and as the primary protection to a retained masonry wall".

Build-ups: read all ten. U-values, targets and cross-references (BW1/BW2/BF1) are internally consistent; no material or thickness changed. The only build-up text change is FD20 → FD30S doorset in IW1 (item 10).

## (iii) Noticed but deliberately left

- **"60 minutes where the basement is more than 10m deep or the house has more than one basement storey"** (fire note). I believe AD B Vol 1 Table B4 gives 30 minutes for a dwellinghouse basement storey including the floor over and marks deeper than 10 m as not relevant, with no "more than one basement storey" trigger, but I could not read Table B4 on the official text (see (v)), so the wording was left; it is conservative rather than unsafe. Now stated only once.
- The FD20 minimum for a dwellinghouse protected-stairway door (AD B Vol 1 Table C1) is the document's existing claim and is retained only as the figure the FD30S standard exceeds; not independently verified for the same reason.
- "Sleeping accommodation is not to be provided in a basement in Flood Zone 3" and the London basement-policy sentences are planning matters, correctly placed under Planning; left.
- 100 mm drain gradient "not less than 1:40" is conservative against AD H (1:80 permitted with a WC); left.
- Sockets at 450–1200 mm is a new-dwelling AD M provision applied here as good practice; left.
- The AD L/F 2026-edition transition NOTE, the radon postcode prompt and the window-schedule prompt are genuine designer prompts; kept.
- "Open-flued combustion appliances are not to be installed in a basement" is a firm design rule rather than an AD J requirement; left as written.
- Regulation 5/6 flat-conversion cross-reference in Applicability is correct and left.

## (iv) Notes count

35 → 32 (four notes dropped by merging, one new Internal Works note created from the misplaced paragraph). Build-ups 10 → 10. All 21 categories retain at least one note or build-up; no category renamed; every note `c` is in `cats`; "BS 8102" present; JS evaluates (`new Function('const SPECS={};'+src+';return SPECS;')`); no paragraph contains a double quote.

## (v) Sources fetched

- https://www.gov.uk/government/publications/fire-safety-approved-document-b — to locate the current AD B Vol 1 PDF.
- https://assets.publishing.service.gov.uk/media/67d2bb074702aacd2251cb94/Approved_Document_B_volume_1_Dwellings_2019_edition_incorporating_2020_2022_and_2025_amendments_collated_with_2026_and_2029_amendments.pdf — the fetch returned only the first 38 pages (Sections 1–3); confirmed para 2.16 (basement habitable room: emergency escape window/external door, or protected stairway to a final exit) and that cavities are in Section 5 of this edition. Appendices B and C (Tables B4 and C1) were not reachable; a direct download was refused by the egress proxy (403).

## (vi) Resolved 6 September 2026 — the fire resistance figure, confirmed and corrected

Approved Document B Volume 1 was downloaded in full and **Table B2** read directly (it is B2 in this
edition, not B4 as (iii) guessed). The suspicion in (iii) was right, and the wording was not merely
conservative — it stated two rules that do not exist.

| Claim in the library | What Table B2 says |
|---|---|
| 60 minutes where the basement is more than 10 m deep | **Not applicable.** Note 4: a dwellinghouse with a 10 m deep basement is outside the scope of the dwellinghouse guidance, so the guidance for buildings other than dwellings applies instead. There is no 60-minute figure to give. |
| 60 minutes where the house has more than one basement storey | No such trigger. Footnote `*` instead: the floor over the **topmost** basement takes the **higher** of the basement-storey period and the ground-or-upper-storey period. |
| 30 minutes (REI 30) otherwise | Correct — 30 min for a dwellinghouse basement storey where the lowest basement is up to 10 m deep. |

The clause in "Smoke Detection and Fire Resistance" now states the 30-minute base, the footnote `*`
rule for more than one basement storey, and the out-of-scope position for a basement over 10 m deep.
Figures recorded in `reference/FACTS.md` under AD B Volume 1.
