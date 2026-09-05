# Garage Conversion (`SPECS.garage`) — review and fix report

Reviewer role: senior Architectural Technologist / plan-checker. Data file reviewed and fixed:
`/tmp/claude-0/-home-claude/5a43e098-d0a9-5b03-b512-8af8f345320b/scratchpad/specdata_garage.js`
Fix script: `/tmp/review/fix_garage_review.py` (run once; pre-fix copy kept at `/tmp/review/specdata_garage.before.js`).

## (i) Verdict

**Approvable.** The build-ups are technically sound (every retained element meets Table 4.3, every new element meets Table 4.2, the retained-garage separation is REI 30 with a 100 mm step or fall, the shared garage wall is treated as an REI 60 compartment wall) and the escape, alarm, ventilation and drainage provisions are complete. Before the fix a plan-checker would have raised three queries — the FD20 door grade (pre-2019 Approved Document B), the boundary wall "fire resistance from the inside" contradicting the "from both sides" statement two notes later, and Regulation 23 being cited for the change to energy status (that is Regulation 22) — and would have commented on the document reading twice on notices, drainage, ventilation and heating. All of these are now resolved.

## (ii) Findings and fixes

**Duplicates merged (7 notes removed)**

1. *Statutory Notices and Party Wall* + *Regulation 16 Notices — Commencement and Completion* → one note **Statutory Notices (Regulation 16), Inspections and Party Wall** (General Notes). Kept the detailed Reg 16 paragraph and its NOTE; replaced the generic inspection-stage list ("oversite, foundations…") with the garage-specific one from the older note (excavation under the garage door, DPC and floor membrane, fire separation to a retained garage before closing up, insulation before boarding); competent-person certificates now stated once; party wall paragraph retained.
2. *Lintels, Beams and Fire Protection* + *New Openings into the Dwelling* → **Lintels, Beams, New Openings and Fire Protection** (Structure). The 30-minute steel protection was stated in both; the cavity tray/stop ends/weep holes over the infill lintel was in the new-openings note and build-up EW1 — now once in the note.
3. *Foundation Under the Garage Door Opening* + *Foundations — Fallback Dimensions and Rules* → **Foundation Under the Garage Door Opening and Fallback Foundation Rules** (Foundations & Infill). The NHBC Chapter 4.2 / trees sentence appeared in both; now once, with the raft/piled fallback and the "excavations inspected before concreting" sentence.
4. *Smoke Detection* + *Smoke Alarms in Rented Dwellings* → **Smoke, Heat and Carbon Monoxide Alarms** (Means of Escape & Fire Regs). Rented-dwelling paragraph kept as paragraph 2. CO alarm to BS EN 50291 for combustion appliances stated here; the boiler-in-garage case (1–3 m from the appliance) stays in the heating note.
5. *Ventilation of the New Room* + *Ventilation — Approved Document F Figures, Systems and Commissioning* → **Ventilation — Approved Document F** (Ventilation). Purge 1/20 (>30°) / 1/10 (15–30°), 8000 mm² background, extract 30/60/30/15/6 l/s, 15-minute overrun, 10 mm undercut were each stated twice; now once, led by the garage-specific paragraph. Dropped "or the dwelling is single-aspect" (a flats trigger, meaningless for a house). Kept "check openable areas against the window schedule" as a genuine designer prompt.
6. *Drainage* + *Drainage — Depths, Chambers, Branch Pipes, Building Over Sewers and Pumped Drainage* → **Drainage — Connections, Depths, Chambers, Branch Pipes, Building Over Sewers and Pumped Drainage** (Drainage). Cover depths 600/900, pea gravel, 450 mm chambers, rodding eyes, BS EN 12056-2, AAV, 50 mm sleeving and testing were all in both. Garage-specific items folded in: PVC-U to BS EN 1401/clay at 1:40, connection to the existing SVP within 6 m or a new stack 900 mm above openings within 3 m, saddle/new-chamber connection to the existing foul drain, sleeving and fire stopping through the infill wall, existing drains under the garage to be located and protected, testing "in the presence of building control". The drain-crossing-a-foundation rule (also in the foundation note) now appears in the drainage note once.
7. *Heating and Hot Water* + *Heating Systems — Boilers, Heat Pumps, Underfloor Heating and Hot Water* → **Heating and Hot Water — Extending the Existing System, Boilers, Heat Pumps, Underfloor Heating and Part G** (Services). Garage-specific lead paragraph (extend existing system, TRVs, boiler-in-garage flue terminal check, CO alarm 1–3 m, Gas Safe/OFTEC/HETAS notification and certificates) followed by the three detail paragraphs; CO alarm clause removed from the detail paragraph so it is stated once.

**Contradictions resolved**

8. Boundary wall fire resistance: *Fire Resistance and Separation* said "30 minutes fire resistance **from the inside**" while *External Fire Spread* said "**from both sides**" for a wall within 1 m of the relevant boundary. AD B Volume 1 requires both sides within 1 m; the duplicate paragraph was removed from *Fire Resistance and Separation* and replaced with a one-sentence cross-reference to the External Fire Spread note.
9. Build-up RF4 (pitched roof, ceiling-level insulation): header `u:"0.16"` and target 0.16 but the text said "calculates at 0.15". Text now reads 0.16 "with no margin; do not reduce the quilt thickness". Materials/thicknesses unchanged.
10. Build-up RF3 target read "0.16 for a renovated roof (0.15 where the roof covering is renewed)". Re-covering an existing roof is a Regulation 23 renovation (Table 4.3, 0.16) — as RF1/RF2 and the U-value note correctly say — not a new element. Bracket now reads "(0.15 W/m²K where the roof is rebuilt as a new element)".

**Wrong or weak clauses fixed**

11. *How the Regulations Apply* attributed the "change in energy status" to Regulation 23. Verified on legislation.gov.uk: Regulation 22 is *Requirements relating to a change to energy status*; Regulation 23 is *Requirements for the renovation or replacement of thermal elements*. Rewritten: Reg 22 for the garage becoming heated, Reg 23 for each element renovated/replaced in the process (re-covering the roof, relaying the slab); Table 4.3 for retained and Table 4.2 for new elements. "Regulation 23" phrase preserved (test requirement) and remains correct in build-up RF2's NOTE.
12. "FD20 door" to a protected stairway in a three-storey house (stated in both *Internal Finishes* and *New Windows and External Doors*): FD20 was withdrawn in the 2019 Approved Document B; FACTS confirms FD30 with FD30S adopted. Removed from *Internal Finishes*; *New Windows and External Doors* now specifies "an FD30S doorset (E 30 Sa, with intumescent strips and cold smoke seals) fitted with a self-closer" for both the retained-garage door and any door onto the protected stair of a house with a floor more than 4.5 m above ground. Build-up IW1 door wording aligned to the same house standard.
13. Alarm grade: *Smoke Detection* said "Grade D1 Category LD2 as a minimum" without context. Now states the house standard and that it exceeds the AD B Volume 1 minimum of Grade D2 Category LD3; alarm standards (BS EN 14604, BS 5446-2), supply circuit and commissioning certificate added.
14. Background ventilation "8000 mm²" (windows note and ventilation note) did not cover the single-storey case; AD F Table 1.7 gives 10,000 mm² for single-storey dwellings. Both places now read "8000 mm² (10,000 mm² where the dwelling is single-storey)". Bathroom 4000 mm² added to the wet-room paragraph.
15. Movement joints: "where the panel exceeds 6m" for infill brickwork → clay brick 12 m / concrete block 6 m (FACTS / PD 6697).
16. Part G in the heating note: added the G3 requirement that stored hot water is held at not less than 60 °C (the 48 °C bath TMV clause was already correct and is retained); unvented installer wording tightened to "registered with a competent person scheme for unvented hot water".
17. Part Q sentence in *Security* ("Part Q does not apply to work to an existing dwelling other than a new dwelling") rewritten: Q1 applies only to new dwellings, including those created by a material change of use, not to a room added to an existing dwelling.
18. Pipework insulation in the heating note now "primary and accessible pipework, and all pipework outside the heated envelope, to Table 4.4 of AD L Volume 1 and the DBSCG" (previously "Table 4.4" with no document named).

## (iii) Noticed but deliberately left

- Foundation depths "1000 mm in clay / 750 mm elsewhere" (fallback note) and the 750 mm trigger in the garage-door paragraph: AD A gives 0.75 m as the clay minimum; 1000 mm is the commonly adopted depth and is conservative. Not in FACTS; left as written.
- "A kitchen is not to be the access room to an inner room" (*Means of Escape*): not in FACTS and I could not confirm the exact AD B wording; conservative, left.
- Fallback note still says "Approved Document A Section 2E … Table 10" — plausible references, not verified, left.
- *Off-Mains Foul Drainage* note: rarely relevant to a garage conversion but it is a single, correct note (figures match AD H and FACTS), so retained.
- *Partitions and the Existing Ceiling* upgrading the ceiling to 30 minutes "where the room above is a bedroom": a good-practice statement rather than a strict AD B requirement; left.
- *Existing Construction to be Verified* overlaps slightly with the last paragraph of *Compliance and Scope*; the two serve different purposes (scope disclaimer vs contractor instruction) and were left.
- Build-up materials, thicknesses and calculated U-values were not altered (calculator-checked); only the two textual inconsistencies in items 9 and 10.
- The AD L/F 2026-edition transition NOTE in *Thermal Elements and U-values* is kept as a genuine designer flag.
- Party Wall Act paragraph appears in build-up EW9 (shared wall) as well as the notices note; the build-up version is a design NOTE and was left.

## (iv) Counts

Notes: **42 → 35**. Build-ups: 18 → 18 (three text edits: IW1 door wording, RF3 target bracket, RF4 U-value statement). All 18 categories still have at least one note or build-up; every note's category is in `cats`; no paragraph contains a double quote; `node` eval passes.

## (v) Sources fetched

- https://www.legislation.gov.uk/uksi/2010/2214/regulation/22 — Regulation 22 "Requirements relating to a change to energy status".
- https://www.legislation.gov.uk/uksi/2010/2214/regulation/23 — Regulation 23 "Requirements for the renovation or replacement of thermal elements".
- All other figures checked against `/tmp/review/FACTS.md` only.
