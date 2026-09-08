# Construction details — House Extension

Drawing specification for the eleven details in the library. Written from the Approved
Documents and from clauses already verified in `data/specdata_core.js`, so the drawings and the
specification agree. Every figure below appears in the specification already; where a detail and a
clause disagree, the clause is right and the drawing is wrong.

**Why these three.** A mid-wall section restates what the specification already says in words and
is never queried. Details earn their place at junctions, where insulation continuity, the damp
proof course, the cavity tray and the thermal bridge are resolved. These three cover the bottom of
the wall, the roof edge, and the join to the existing house — the three a building control officer
actually marks up on a single-storey rear extension.

**Conventions for all three**
- **1:10 at A3 landscape**, and the sheets measure it. The details are 1920 to 2100mm wide, which
  at 1:5 would need 384 to 420mm of paper — wider than A4 in either orientation, so the earlier
  1:5 label could not have been true on any sheet. A drawing that states a scale it does not
  hold is worse than one that states none, because someone will scale off it.
  **The paper was A4 until 8 September 2026 and did not fit**: printed at A4 landscape every
  sheet ran to two pages. At A3 landscape with a 72mm side panel each sheet is one page and the
  1:10 still holds, and A3 is the sheet size the drawing packs already use, and the size
  `dxf_details.py` has always built its paper space at.
- Status default **For Building Control Approval**, not For Construction.
- Hatch key on every sheet, showing the real hatch rather than a flat colour. Dimensions in
  millimetres. "Do not scale from this drawing."
- **Materials are drawn as they are cut, not as they are seen.** Brickwork in section shows bed
  joints at 75mm centres and no perpends; blockwork shows bed joints at 225mm. A staggered bond
  pattern is an elevation and has no place on a section. Coursing is set out from the damp proof
  course, as it is on site, so a bed joint lands exactly on the DPC.
- Show the build-up reference (EW1, GF1, RF1) against each element so the detail ties to the
  schedule and the drawings cross-refer.
- Anything to the structural engineer's design is drawn indicatively and labelled as such — the
  detail must not appear to specify a foundation size or a beam.
- Insulation continuity is the point of all three. Where insulation stops, say what continues it.

---

## D-201 — External wall to ground floor and damp proof course

**Substantiates:** the ground floor perimeter thermal bridge, and the continuity of the damp proof
course with the damp proof membrane.

**Section cuts** vertically through the cavity wall at ground level, from the foundation to about
600mm above finished floor level.

**From the bottom up**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Foundation | Indicative only — "to the structural engineer's design" | Depth 1000mm in shrinkable clay, 750mm elsewhere, shown as a broken dimension |
| Substructure walls | Dense concrete blockwork, minimum 7.0 N/mm², mortar designation suitable below DPC | Both leaves |
| Cavity fill | Lean mix concrete to **not less than 225mm below the DPC**, top finished with a fall to the outside | Weep holes above the fill |
| Hardcore | Compacted in layers **not exceeding 150mm**, minimum finished thickness **150mm** | |
| Blinding | **50mm** sand or other fine material | Protects the membrane |
| Slab | **Not less than 100mm** GEN1 or RC20 to BS EN 206 and BS 8500 | |
| DPM | Polyethylene **not less than 1200 gauge (300 micron)**, 1600 gauge where radon or gas protection is required | **Lapped and sealed to the DPC** — draw the lap, do not imply it |
| Floor insulation | Per GF1, over slab | |
| Edge insulation | **25mm** perimeter upstand, full depth of the screed | |
| Screed | **65mm** minimum over the insulation | |
| DPC | **Not less than 150mm above finished external ground level**, minimum **100mm** lap at joints | Both leaves |
| Wall above | Per EW1 | |

**The critical check — draw this or the detail is pointless.** The wall insulation and the floor
insulation must overlap at the perimeter. Show the cavity insulation carried down past the level of
the floor insulation, and the 25mm edge upstand carried up to the underside of the screed, so there
is no straight path from inside to outside through the slab edge. If the two do not overlap on the
drawing, the psi-value being claimed in SAP is not the detail being built.

**Also show:** finished floor level and finished external ground level with the 150mm difference
dimensioned; weep holes at not more than 900mm centres above the cavity fill; and a note that where
the site is in a radon affected area the membrane is replaced by a radon-resistant grade to BR 211
with 300mm sealed laps.

---

## D-202 — Warm deck flat roof at the eaves

**Substantiates:** the wall head thermal bridge and the cavity barrier at the top of the cavity.

**Section cuts** vertically through the roof edge, the fascia and gutter, and the head of the
cavity wall, from about 300mm into the roof to about 600mm down the wall.

**From the deck up (RF1)**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Joists and firrings | Firrings cut to give a design fall of **not flatter than 1:80** | Direction of fall |
| Deck | 18mm exterior grade plywood or OSB3, screwed | |
| Vapour control layer | Continuous on the **warm side**, laps **150mm** taped and sealed | Sealed at the perimeter |
| Insulation | Per RF1 — TR27 laid **break-bonded in two layers, fully adhered** | State the thickness and that mechanical fixing changes the U-value |
| Waterproofing | Single ply or built-up felt to the manufacturer's system | Dressed over the edge |
| Edge trim | Proprietary drip with a minimum **25mm** projection over the gutter | |
| Gutter | Sized per AD H3 — 112mm half round / 68mm downpipe for roof areas up to 40m² | |

**At the wall head**

- Cavity barrier at the top of the cavity — mineral wool or a proprietary closer, per AD B Vol 1.
- **Insulation continuity:** the roof insulation must meet the cavity insulation. Draw the cavity
  insulation carried up to the underside of the deck, or the roof insulation returned down over the
  wall head. Show which.
- Wall plate strapped down; lateral restraint straps at not more than 2m centres where the roof
  provides restraint.
- Ceiling and internal finish, with the air barrier sealed at the wall/ceiling junction.

**The critical check.** The cavity barrier and the insulation are two different things doing two
different jobs at the same place, and they are routinely conflated. Draw both, label both.

---

## D-203 — Flat roof abutment to the existing dwelling

**Substantiates:** weather-tightness and insulation continuity at the junction with the existing
house. This is the most-queried detail on a rear extension and the one most often built wrong.

**Section cuts** vertically through the abutment where the new flat roof meets the existing
external wall.

**Must show**

| Component | Dimension / spec |
|---|---|
| Upstand | Waterproofing carried **not less than 150mm** above the finished roof surface, on an insulated upstand |
| Cavity tray | Over the abutment, stepped where the existing wall is cavity construction, with **stop ends** and **not fewer than two weep holes per opening, at not more than 900mm centres** |
| Cover flashing | Lead **Code 4**, tucked **25mm** into the masonry joint and wedged, lapped over the upstand, piece lengths limited to **1.5m**, patination oil on completion |
| Vertical DPC | At the abutment where the new cavity meets the existing wall |
| Insulation | Roof insulation carried up the upstand and meeting the existing wall insulation line; vapour control layer carried up with it |
| Fire stopping | At the junction, and cavity barriers where the new cavity meets the existing |
| Existing finish | Where the existing external wall becomes internal, render and any impermeable finish removed as required; existing cavity closed and sealed at the junction |

**The critical check — three separate things, three separate lines on the drawing.** The cavity
tray keeps water out of the cavity, the cover flashing keeps water off the upstand, and the
insulation keeps the heat in. They are three different components at the same junction and a
drawing that shows two of them will be built with two of them. Show the stop end explicitly; a
cavity tray without stop ends discharges into the cavity and is the single most common defect at
this junction.

**Also show:** movement joint with proprietary wall tie connectors, or toothing and bonding into
the existing as directed by the structural engineer.

---

---

## D-204 — Window head, insulated lintel and cavity tray

**Substantiates:** the head thermal bridge, and the two things a plan checker looks for over any
opening — a cavity tray that catches what the cavity sheds, and insulation carried through so the
closer, not the lintel, is the thermal path.

**Section cuts** vertically through the head of a window in the cavity wall, from four courses
above the lintel down to the top of the glazing.

**From the top down**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Masonry over | EW1 unchanged: 103 brick, 10 residual, 90 K106, 100 block | Bearing on the lintel |
| Cavity tray | 150 upstand against the inner leaf, stop ends both jambs | Laid before the masonry over |
| Weep holes | open perpends in the first course above the tray, two per opening minimum, at not more than 900 centres | Draw one open perpend |
| Lintel | proprietary insulated cavity lintel to BS EN 845-2, thermal break across the cavity | **Indicative — no size.** Manufacturer's tables for span and load; 150 minimum end bearing on whole units |
| Cavity closer | proprietary insulated, full length of the head | Insulation cut tight to it |
| Frame | laps the closer by 30 to 50 | Sealed both faces |
| Glazing | whole-window U-value not exceeding 1.4 W/m²K, or WER Band B | |

## D-205 — Window jamb, cavity closer and vertical damp proof course

**Substantiates:** the reveal thermal bridge and the moisture path. Where the cavity is closed the
two leaves are bridged, so both the insulation and the damp proof course have to turn the corner.

**Section cuts** horizontally through the jamb — a plan, not a vertical section. External at the
top of the sheet, room below, opening to the right.

**Across the wall**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Outer leaf | 103, returned into the reveal | |
| Insulation | 90 K106 carried right up to the closer | No gap behind the closer |
| Cavity closer | proprietary insulated, full height of the jamb | |
| Vertical DPC | at the reveal, where the cavity is closed | |
| Wall ties | 225 vertical centres within 225 of the unbonded jamb, falling to the outer leaf | Draw the fall |
| Frame | laps the closer by 30 to 50, or 50 for a door | |
| Lining | plasterboard returned into the reveal to the frame | |

## D-206 — Window cill, sub-cill, damp proof course and closer

**Substantiates:** the cill thermal bridge, and water thrown clear of the wall below. The cill is
also where guarding and safety glazing bite, because it fixes how far the opening sits above the
floor.

**Section cuts** vertically through the cill, from the bottom of the glazing to five courses below.

**From the top down**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Frame cill | set on the sub-cill and sealed | |
| Sub-cill | laid to fall, projecting past the face of the brickwork, throated | **Indicative profile** — it is a product |
| DPC | under the cill, lapped down over the outer leaf, stop ends at each jamb | |
| Cavity closer | proprietary insulated, full length of the cill | Insulation cut tight to it |
| Masonry below | EW1 unchanged | |
| Internal cill board | returned to the frame | |

**Two rules this sheet carries in its notes, not its dimensions.** Guarding or an opening
restrictor to Approved Document K where the cill is below 800 above finished floor level and the
drop outside exceeds 600. And, where the window is an escape window, an openable area of not less
than 0.33 m² and not less than 450 by 450, with the bottom of the openable area not more than 1100
above the floor and not less than 800 unless guarded.

---

## D-207 — Eaves at a pitched roof

**Substantiates:** the wall head thermal bridge where the roof is insulated at rafter level, and
the separation of the two components that meet there — the cavity barrier, which is fire stopping,
and the insulation, which is not.

**Section cuts** vertically **between rafters**, so the board filling the rafter depth is seen,
from about 550mm out past the fascia to about 500mm down the wall. Drawn at 35°; the pitch is as
the elevations.

**From the plate up**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Cavity insulation | EW1 unchanged, carried up to the underside of the wall plate | No gap at the head |
| Cavity barrier | mineral wool or a proprietary closer at the very head of the cavity | **Fire, not thermal** — label it as such |
| Wall plate | bedded on the inner leaf, strapped down against uplift | Restraint straps 30 x 5 galvanised, 1m long, at not more than 2m centres |
| Wedge over the plate | flexible insulation filling between the plate and the rafters, tucked into the head of the cavity | This is the piece that is left out on site |
| Rafter zone | **150** Kooltherm K107 fully filling 47 x 150 minimum rafters to the engineer's design | RF2 |
| Underlay | breathable to BS 5534, counter-battens up the slope, battens over | |
| Lining | **62.5** K118 insulated plasterboard beneath the rafters, joints taped | |
| Vapour control | continuous on the warm side, laps, junctions and penetrations sealed | |

**The critical check — draw the two insulation lines meeting.** The cavity insulation stops at the
top of the cavity and the roof insulation starts at the plate arris. If the drawing only brings
them close, the wall plate is a straight cold path from the cavity into the roof, and the
psi-value assumed in SAP is not the detail being built. The cavity barrier does not close that
path and must not be drawn as though it does.

**Also show:** that with a breathable underlay there is no roof void to ventilate, and that where a
non-breathable underlay is used a clear **50mm** gap is kept above the insulation, ventilated
equivalent to a continuous **25mm** at the eaves and **5mm** at the ridge. Where the roof is
insulated at ceiling level instead, the eaves piece is flexible insulation of R-value not less than
**1.2 m²K/W** filling between the wall plate and the eaves ventilator, and the void is ventilated
equivalent to a continuous **10mm** gap at the eaves on two opposite sides plus **5mm** at the ridge.

---

## D-208 — Verge and gable ladder

**Substantiates:** insulation continuity at the gable and the closing of the cavity at the verge.
The weathering is ordinary; the junction that gets queried is where the cavity insulation stops and
the roof insulation starts.

**Section cuts** square to the verge — perpendicular to the line of greatest slope — so the roof
build-up reads as a flat sandwich, the rafters and counter-battens are cut, and the battens and the
ladder noggins are seen along their length.

**Across the junction**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Covering | on battens seen along their length, counter-battens cut at rafter centres | |
| Undercloak | fibre cement or a proprietary dry verge unit, bedded in mortar on the outer leaf | Indicative — it is a product |
| Gable ladder | built off the last rafter but one, noggins between the verge rafter and the last rafter | Restraint straps 30 x 5 at not more than 2m centres |
| Barge board and soffit | to the verge rafter, soffit ventilated | |
| Rafter zone | **150** K107 filling the rafter depth, inboard of the last rafter | RF3 |
| Lining | **62.5** K118 beneath, vapour control layer carried to the wall lining | |
| Cavity barrier | closing the head of the cavity | **Fire, not thermal** |
| Continuity piece | flexible insulation over the inner leaf, tight to the last rafter | |

**The critical check.** The cavity insulation stops at the top of the cavity; the roof insulation
starts inboard of the last rafter. Without a piece bridging the two, the inner leaf is a cold path
the full length of the gable — and a gable is long. Draw both the barrier and the insulation, label
both, and keep them separate.

---

## D-212 — Intermediate floor into the external wall

**Substantiates:** the air barrier through the floor zone, and the continuity of the cavity
insulation past it. The joist bearing is the engineer's; this is the sheet building control marks
up.

**Section cuts** vertically **between joists**, so the quilt is seen, with the joist and the hanger
shown beyond.

**Across the junction**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Deck | **18 or 22** moisture resistant tongued and grooved flooring grade board, glued and screwed | |
| Joists | to the engineer's design and span; drawn 47 x 220 C24 at 400 centres | IF1 — **indicative, no size implied** |
| Quilt | **100** mineral wool of not less than 10 kg/m³ between the joists | Requirement E2 |
| Ceiling | **12.5** plasterboard | |
| Bearing | joists carried on hangers fixed to the inner leaf, **not built in** | |
| Air barrier | parge coat or wet plaster, continuous up the inner face of the inner leaf | Draw it as one unbroken line |
| Restraint | straps 30 x 5 galvanised, 1m long, at not more than 2m centres, over three joists with solid noggins | |
| Cavity insulation | EW1 carried past the floor zone without a break | |

**The critical check.** Joists built into the inner leaf punch a hole in the air barrier at every
joist and every strap. Hang them and the leaf stays continuous, which is the only version of this
junction that survives an air test. Then check the cavity insulation runs past the floor zone: it is
the easiest place on the elevation to leave a gap and the hardest to find afterwards.

---

## D-213 — Wall to foundation

**Substantiates:** the substructure — what happens between the foundation and the damp proof
course. D-201 takes the same wall and resolves the floor edge; this one resolves the foundation, the
cavity fill and the change from dense blockwork to the wall above.

**Section cuts** vertically through the wall and the trench, **with the depth broken**. The break is
drawn: the sheet is not to be scaled for depth.

**From the bottom up**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Trench fill | mass concrete not less than **750** thick, width the wall plus **300** and in no case less than **450**, cast against undisturbed ground in a trench dug to the full width | FD1. **Width is an input** — Table 10 of AD A or the engineer |
| Depth | not less than **1000** below finished ground level; **600** to internal loadbearing walls; below the invert of any adjacent drain without undermining it | Shown broken |
| Concrete | BS EN 206 and BS 8500; chemical class from the ground investigation report | Never from the soil description |
| Substructure | dense concrete blockwork both leaves | |
| Cavity fill | lean mix to not less than **225** below the DPC, top finished with a fall to the outside | |
| Weep holes | at not more than **900** centres, above both the fill and finished external ground | |
| DPC | not less than **150** above finished external ground, both leaves | |
| Floor | per GF1 — see D-201. Membrane lapped to the DPC | Indicated only, not dimensioned here |

**The critical check.** Where the wall is thin, wall plus 300 falls below the 450 minimum for trench
fill and the 450 governs. And where the ground falls the foundation is stepped: no step greater than
the thickness, the higher foundation overlapping the lower by the greatest of twice the step, the
thickness, or 300 — **not less than 1m for trench fill**.

**Also note:** where adverse ground, made ground, soft spots or major tree roots are found in the
excavation, work stops, building control is notified and the engineer advises before any concrete is
placed. The depth and size are approved on site by the building control officer.

---

## D-218 — Door threshold, level access

**Substantiates:** the threshold as two separate problems solved by different components — water,
and heat. A level threshold removes the 150mm step that normally keeps water out, so the fall on the
paving, the channel and the tray have to do that job instead.

**Section cuts** vertically through the door opening, from about 250mm above the threshold to about
650mm below finished floor level.

**Across the junction**

| Component | Dimension / spec | Annotate |
|---|---|---|
| Threshold and frame | proprietary low-profile section | **Indicative** — they are products |
| Level | paving **15** below finished floor level, laid to fall away | See the note below |
| Channel | channel drain across the full opening, removable grating, discharging to the surface water system | |
| Cavity tray | under the threshold with stop ends, weeping over the channel | Draw the stop end |
| Closer | insulated cavity closer, and **25** edge insulation | |
| Floor | GF1 — **65** screed on **80** K103 over a **100** slab, **50** blinding, **150** hardcore | |
| Membrane | over the slab, turned up at the opening and lapped to the tray | |

**The critical check.** Water and heat are solved by different components at this junction: the
channel and the tray keep water out, the closer and the edge insulation keep the heat in. A sheet
showing three of the four gets built with three. The floor insulation and the cavity insulation have
to meet under the threshold or the opening is the bridge.

**NOT VERIFIED — confirm before this sheet is issued.** The 15mm and the definition of an
*accessible threshold* are Approved Document M, and the Appendix A definition is **not** held in
`reference/FACTS.md`. The library confirms the M4(1) figures either side of it — a clear opening
width of not less than 775mm, and a level landing outside the principal entrance — but not the
upstand. Read Appendix A, add the figure to FACTS.md, and then take this note off the sheet.

## After these eleven

House Extension is now complete against the register except `D-217`, the dormer cheek, which the
relevance table reaches through EW + RF and which belongs with the loft details rather than here.

The next tranche is the shared ones: `D-209` separating wall to roof and `D-214` party wall at the
ground floor, both of which unlock New Build, New Build Flats and Flat Conversion at the same time.
