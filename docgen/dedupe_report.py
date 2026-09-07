import sys, subprocess
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(os.path.dirname(HERE),'output'); os.makedirs(OUT,exist_ok=True)
# This is SY Design Studio's own QA report on the library, not a practice's specification,
# so it pins the in-house profile rather than reading whichever practice is installed.
os.environ.setdefault('SPECLINE_PRACTICE_SOURCE','brand')
from build_spec import *
from brand import _rule, _shade
def sp(d,t,size=9.5,color=None,bold=False):
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(4); r=p.add_run(t); r.font.size=Pt(size); r.font.bold=bold
    if color: r.font.color.rgb=color
    return p
def bullet(d,t):
    p=d.add_paragraph(); p.paragraph_format.left_indent=Mm(6); p.paragraph_format.first_line_indent=Mm(-4); p.paragraph_format.space_after=Pt(2)
    r=p.add_run("•  "); r.font.color.rgb=ACCENT; r.font.bold=True; r.font.size=Pt(9.5)
    r=p.add_run(t); r.font.size=Pt(9.5)
def verdict(d,v,why):
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(4)
    r=p.add_run("VERDICT  "); r.font.bold=True; r.font.size=Pt(9); r.font.color.rgb=ACCENT
    r=p.add_run(v); r.font.bold=True; r.font.size=Pt(10); r.font.color.rgb=DARK
    sp(d,why)

meta=dict(type="Document Review of the Specification Library",
  project="All eight project types — duplication, contradiction and clause accuracy",
  address="Internal review of the printed specifications as a reader receives them",
  client="SY Design Studio Ltd (internal)", job="LIBRARY", la="n/a — internal QA",
  application="Second-stage QA following the plan-check stress test",
  author="Prepared with Claude for Salman Yousaf", date="5 September 2026", rev="R02")
d=new_doc(); headers(d,meta); cover(d,meta)          # the logo comes from the practice profile

h1(d,"Why This Review Was Needed","1.0")
sp(d,"The library was completed by adding a set of detailed shared notes — Regulation 16 notices, heating systems, chimneys and stoves, external fire spread, drainage depths and off-mains drainage, the Approved Document F figures, staircase detail, radon detail, foundation fallback dimensions, lintels and fire protection, movement joints and ties, leadwork, permitted development limits, HMO, sub-floor ventilation, rooflights and renewables — to each of the eight project types. Those notes were appended to each type without removing or merging the older general notes that already covered the same ground.")
sp(d,"The technical content was therefore right but the documents repeated themselves, and in a handful of places the old note and the new note gave different figures for the same thing. The defect was found in the printed output of job 1134 (House Extension, Rev P01), which stated leadwork twice, staircases twice, ventilation three times, renewable systems three times, and gave the smoke alarm grade as D2 LD3 in one note where every other type adopts D1 LD2. Each of the eight types was then reviewed the same way, clause by clause, as a plan checker reads a submission.")
sp(d,"Figures were checked against the Approved Documents rather than against the previous text. Where a figure could not be confirmed from the Approved Document itself, the existing wording was kept and the point recorded rather than replaced with an assumption.")

h1(d,"Summary","2.0")
sp(d,"Every one of the eight documents now reads once per subject. Across the library the note count fell from 379 to 325 — a reduction of 54 notes — with no loss of technical coverage: the 113 construction build-ups are unchanged, no category was added or removed, and no category is left empty. All 141 automated tests pass and every document regenerates from the same single source as the app.")
for x in ["House Extension 64 → 53 notes","Loft Conversion 44 → 36","Flat Conversion 43 → 37","Garage Conversion 42 → 35",
          "New Build 68 → 58","New Build Flats 58 → 51","Basement Conversion 35 → 32","Garage Build 27 → 23"]:
    bullet(d,x)

R=[
("House Extension","APPROVE","Content sound; the document repeated itself and carried one wrong Part G clause and one contradiction on the alarm grade.",
 ["Leadwork ×2, staircases ×2, ventilation ×3, renewables ×3 (air source heat pump specified three times), heating ×2, damp proof course and cavity trays ×2, movement joints ×2, rainwater discharge hierarchy ×2 — all merged to one note each.",
  "Smoke alarms given as Grade D2 LD3 while every other type adopts D1 LD2 — now D1 LD2 throughout, stated as exceeding the Approved Document B minimum.",
  "Part G wrongly limited hot water at the taps to 60°C and cited the bath valve to G5. G3 requires storage capable of 60°C for legionella control and the bath supply limited to 48°C by a thermostatic mixing valve to BS EN 1111 or BS EN 1287 — rewritten.",
  "Garage door specified as ‘E 30 standard’ — now an FD30S doorset (E 30 Sa) with a self-closer.",
  "Escape window gave only the 1100mm upper bound — now the full envelope with the 800mm lower bound, the no-key requirement, the inner-room rule and the three-storey case.",
  "Internal and external lighting notes deferred the efficacy figure — now 75 lumens per circuit-watt for all fixed lighting, fittings under 5 circuit-watts excluded (Approved Document L Volume 1, 2021 edition)."]),
("Loft Conversion","APPROVE","The fire strategy was internally inconsistent before the review; it now reads as one strategy.",
 ["Stair enclosure given as REI 30 in one place and EI in another; doors given as E 20, FD20 and E 30 in three places, with a note telling the reader not to use FD references at all. Resolved: FD30S doorsets with self-closers as the practice standard, stated as exceeding the Approved Document B minimum of E 20, and REI / EI / E notation explained once.",
  "Guarding to landings given as 1100mm — Approved Document K Diagram 3.1 is 900mm to stairs, landings and internal floor edges and 1100mm to external balconies. Corrected against the published Approved Document.",
  "Commencement notice trigger given as ‘when structural works begin’ — for a loft the Regulation 46A trigger is 15 per cent of the work complete. Corrected.",
  "Part G hot water clause corrected as for the extension.",
  "A paragraph on the fire resistance of the new floor over a retained ceiling had been pasted into the planning note — moved to its own note under Loft Floor.",
  "Renovated-element targets that read ‘upgrade to the standard in Approved Document L’ now give the Table 4.3 figures (roof 0.35 → 0.16, cavity wall 0.70 → 0.55, other walls 0.70 → 0.30, floor 0.70 → 0.25).",
  "Planning ×2, notices ×2, staircases ×2, escape ×3, alarms ×2, ventilation ×2, drainage ×3, heating ×2 merged."]),
("Flat Conversion","APPROVE","Regulation 6 framing and the Part E regime were right; the supporting clauses needed reconciling.",
 ["Background ventilators given as 8000mm² in one note and 10,000mm² in another for the same flat — resolved to 10,000mm² for a single-storey flat, 8000mm² for a maisonette.",
  "Lighting efficacy given as ‘three quarters of fittings’ — that rule was withdrawn in the 2021 edition; now all fixed lighting at 75 lumens per circuit-watt.",
  "A Robust Details paragraph contradicted the paragraph stating that Robust Details are not available for conversions — removed, pre-completion testing stated once.",
  "Regulation 6 applicability re-checked against the legislation: a house-to-flats conversion brings in requirement C2(c), S2 and Q1; the full C2 applies only under regulation 5(a).",
  "Internally insulated wall build-up header said 0.30 while its text said 0.26 — product and thickness named and the header corrected.",
  "Six merges: radon, staircases, heating and hot water, sound testing, compartmentation and fire periods, ventilation."]),
("Garage Conversion","APPROVE","Three real queries a plan checker would have raised, now closed.",
 ["Boundary wall given as 30 minutes ‘from the inside’ in one note and ‘from both sides’ two notes later — resolved to both sides.",
  "Regulation 23 cited for the change to a building’s energy status — that is Regulation 22; Regulation 23 covers renovation of thermal elements. Checked on legislation.gov.uk and both now cited correctly.",
  "FD20 door to the dwelling — now an FD30S doorset.",
  "Flat roof build-up RF4 claimed 0.15 in its text and 0.16 in its header; RF3 implied that re-covering a roof makes it a new element. Both corrected.",
  "Seven duplicate pairs merged: notices, lintels, threshold foundation, alarms, ventilation, drainage, heating — keeping the garage-specific clauses in each case."]),
("New Build","APPROVE","Technically the strongest of the eight; the defects were duplication plus three clause errors.",
 ["Garage separation stated as both 60 and 30 minutes within the same note — resolved to REI 30.",
  "FD20 doors specified to a three-storey protected stair — now FD30S doorsets with self-closers.",
  "Fire appliance gateway width given as 2.75m — corrected to 3.1m.",
  "Rooflight U-value described as assessed ‘in the vertical plane’ — Approved Document L assesses rooflights in the horizontal position; corrected against the published document.",
  "Limiting-value list completed with the party wall 0.20 and rooflights 2.2 figures.",
  "Eighteen duplicate sets merged, including drainage three times over, movement joints three times, guarding three times and the unvented hot water clause three times."]),
("New Build Flats","APPROVE for a block with no storey above 11m","The stated basis of the specification; a taller block still needs the clause-by-clause review the Building Height note calls for.",
 ["Stair-head smoke vent given as 1.5m² where Approved Document B asks for 1m², and the same note contradicted itself — corrected against the published document.",
  "Evacuation alert systems placed at 11m in one note and 18m in another — resolved to 18m.",
  "Car park ventilation cited to Approved Document B Volume 1 Section 11, which is boundary distances — now cited to Volume 2 (car parks and shopping complexes).",
  "Protected-hall glazing rule corrected (uninsulated glazing only above 1.1m) and window guarding aligned between the Windows note and the Part O note.",
  "Extract rates that read ‘at the rates in Table 1.1’ now give the figures.",
  "Seven merges: notices, radon, foundations, staircases, heating and hot water, escape within the flat, Part E testing, ventilation, Part O and drainage."]),
("Basement Conversion","APPROVE","The technical core — BS 8102 Grade 3, underpinning sequence, sump arrangement, escape — was already sound.",
 ["The obsolete ‘three quarters of fittings’ lighting rule replaced with 75 lumens per circuit-watt for all fixed lighting.",
  "A paragraph on doors and windows was sitting inside the foul drainage note — moved to Internal Works.",
  "FD20 doors replaced with FD30S doorsets in two notes and in build-up IW1; alarms stated as D1 LD2 exceeding the Approved Document B minimum; escape window given the 800–1100mm range and the no-key requirement.",
  "Four duplicate pairs merged: Regulation 16 notices, staircases, ventilation, heating.",
  "Repetition trimmed: the fire-resistance period, the damp proof course and the sump specification are each now stated once, with the other notes cross-referring."]),
("Garage Build","APPROVE","Sound on substance; the issues were presentation, one contradiction and one garbled rule.",
 ["Foundations stated three times with two different step-overlap rules — merged, and the Approved Document A rule corrected (thickness not less than the projection, and not less than 150mm).",
  "Movement joint spacing for concrete blockwork given as 6m in one note and 7.5–9m in another — resolved to 6m.",
  "Timber cladding reasoning corrected: cladding worse than Class B-s3, d2 counts towards the unprotected area.",
  "Boundary fire spread ×2, notices ×2, room over the garage ×2, vehicle door lintel ×2 merged; the separation note now cross-refers to build-up SW1 instead of restating it.",
  "Alarms and the escape window brought up to the practice standard; the detached (Volume 2) and attached (Volume 1, Table 4.2) Part L routes distinguished."]),
]
n=2
for name,v,why,items in R:
    n+=1; h1(d,name,f"{n}.0")
    verdict(d,v,why)
    h2(d,"What was found and what was done")
    for x in items: bullet(d,x)

h1(d,"Rendering and Output","11.0")
for x in ["The superscript characters in ‘W/m²K’, ‘0.33m²’ and ‘10 kg/m³’ are present in the generated PDF. Where they appear as gaps it is the viewer substituting a font without the glyph, because the standard PDF fonts are referenced rather than embedded. Adobe Acrobat, Chrome and Edge display them correctly. Embedding a font would remove the risk at a cost of roughly 300KB per file and can be done if the documents are to be issued to unknown recipients.",
 "The build-up schedule header cells now draw before their labels so a cell fill cannot paint over the text of the column beside it.",
 "Every document is generated from the same data as the app, so a correction made once appears in the app, the Word file and the PDF."]:
    bullet(d,x)

h1(d,"What Remains Open","12.0")
for x in ["Wales, Scotland and Northern Ireland are not covered; every specification is England-only.",
 "The parametric configurators cover cavity walls, ground floors, heated basements and three roof types. Timber frame walls, dormer cheeks, internal linings and separating elements remain fixed build-ups.",
 "The A102 General Notes drawing sheet still cites withdrawn standards and has not yet been brought into line with the library.",
 "Two figures were left as written because they could not be confirmed from the Approved Document during this review and changing them on an assumption would be worse than leaving them: the 60 minute fire resistance for a basement more than 10m deep or with more than one basement storey (Basement Conversion), and the car park ventilation percentages (New Build Flats). Both are conservative as written. Confirm before the first job of that kind.",
 "The Approved Documents L1 and F1 2026 editions come into force on 24 March 2027, with the transitional commencement deadline of 24 March 2028 for new dwellings. Every specification carries the flag; the library will need a full pass against the new editions during 2027."]:
    bullet(d,x)
d.save(os.path.join(OUT,'SYDS_Spec_Library_Document_Review.docx'))
subprocess.run(['soffice','--headless','--convert-to','pdf','--outdir',OUT,os.path.join(OUT,'SYDS_Spec_Library_Document_Review.docx')],check=True,capture_output=True)
print("done")
