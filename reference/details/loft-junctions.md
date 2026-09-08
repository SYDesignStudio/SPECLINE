# Construction details — Loft Conversion

Drawing specification for the loft details in the library. Written from the Approved Documents and
from clauses already verified in `data/specdata_core.js`, so the drawings and the specification
agree. Every figure below appears in the specification already; where a detail and a clause
disagree, the clause is right and the drawing is wrong.

**Why these five.** A loft conversion is queried in different places to an extension. The wall,
floor and roof are mostly existing, so the junctions that earn a drawing are the ones the
conversion creates: where the dormer lands on the roof, where its flat roof meets the cheek, where
the sloping ceiling meets the dwarf wall, where the new floor meets the old wall, and where a gable
that was outside the envelope is suddenly inside it. Four of the five are insulation-continuity
details and the fifth is a fire and sound floor.

**Conventions for all five** — as the extension set, and repeated here because the sheets are
issued separately.

- **1:10 at A3 landscape**, and the sheets measure it. Geometry is 1:1 in real millimetres and is
  never scaled; the plot scale lives on the layout.
- Status default **For Building Control Approval**, not For Construction.
- **Materials are drawn as they are cut, not as they are seen.** On the sheets cut square to the
  roof slope the roof reads flat: rafters and counter-battens are cut, battens are seen along their
  length. On the sheets cut along the slope it is the other way round. The sub-caption on each
  sheet says which cut it is, and it is not decoration.
- Show the build-up reference (EW1, RF1, IF1) against each element. **References are per job**, so
  EW1 here is the dormer cheek and EW1 on the extension sheets is the full fill cavity wall. They
  are labels on a drawing, not library codes.
- Anything to the structural engineer's design — beams, trimmers, joist sizes, rafter
  strengthening — is drawn indicatively and labelled as such.
- The existing wall is drawn as **215mm solid brick** wherever it appears, because that is what the
  library's own gable clause is calculated on. Every sheet carries a note to confirm the
  construction on site, and the U-value has to be recalculated if it is a cavity wall.

---

## D-217 — Dormer cheek to the main roof

**Substantiates:** the insulation line where the cheek lands on the roof, and the weathering at an
abutment that has to be soakers rather than a single raking flashing.

**Section cuts** vertically, **square to the main roof slope**, so the roof reads flat and the
cheek stands on it.

| Component | Dimension / spec | Annotate |
|---|---|---|
| Cheek | cladding on battens, **25** minimum ventilated and drained cavity, **18** ply sheathing, **140** K112 filling 140 x 38 studs at 400, **37.5** K118 to the room face | EW1 — 0.16 W/m²K |
| Vapour control | continuous on the warm side of the cheek | |
| Trimmer | doubled, to the engineer's design | **Indicative — no size** |
| Sole plate | over the trimmer, under the cheek studs | |
| Continuity | insulation packed round the plate and the trimmer, tying the cheek insulation to the roof insulation | The piece that gets left out |
| Cavity barrier | at the perimeter of the cheek and at the junction with the main roof | **Fire, not thermal** |
| Weathering | Code 4 lead soakers to each course, upstand not less than **150**, on a tilting fillet; patination oil on completion | |
| Main roof | RF1 — **125** K107 between rafters, **25** residual gap under a breathable underlay, **72.5** K118 beneath | |

**The critical check.** The sole plate and the trimmer are about 190mm of solid timber sitting
exactly where the cheek insulation and the roof insulation want to meet. Insulate round them and
the line is continuous; leave it and the cheek is bridged along its whole length. It cannot be done
after the cheek is sheathed.

**Also note:** where the cheek abuts or is close to a boundary, the fire resistance and the extent
of unprotected area are checked against Approved Document B before construction.

---

## D-219 — Dormer flat roof at the cheek head

**Substantiates:** the warm deck meeting the cheek over the head plate, and the vapour control
layer under the deck.

**Section cuts** vertically **between joists**, through the head of the cheek.

| Component | Dimension / spec | Annotate |
|---|---|---|
| Waterproofing | single ply or high performance built-up felt to the BBA certificate, dressed over an edge trim projecting not less than **25** | |
| Insulation | RF2 — **150** Thermaroof TR27 in two layers, break bonded and **fully adhered** | Mechanically fixed takes it to 0.16 — use **160** instead |
| Vapour control | fully bonded to the deck, all laps sealed | |
| Deck | **18** external quality ply or OSB3, laid to a finished fall not flatter than **1:40** | |
| Joists | to the engineer's design; drawn 47 x 200 C24 at 400 | **Indicative** |
| Ceiling | 12.5 plasterboard | |
| Continuity | insulation carried down past the head plate to meet the cheek insulation | |

**The critical check.** Cold deck construction is not to be used — insulation above the deck,
vapour control layer below it, both continuous. And the head plate is 50mm of solid timber directly
between the roof insulation and the cheek insulation: carry the insulation down its outer face.
The falls, the trim and the upstands are all easier to get right than this and all get more
attention.

**Also show:** upstands of not less than **150** at all abutments, with cavity trays and stepped
flashings where the dormer abuts masonry.

---

## D-220 — Eaves at a room in roof: dwarf wall and eaves void

**Substantiates:** the thermal envelope turning two corners at the eaves, and the eaves void being
kept deliberately outside it.

**Section cuts** vertically **between rafters**, along the slope. Drawn at 45°, which is what puts
a 1050 dwarf wall 1465 in from the face of the wall; the pitch is as the sections.

| Component | Dimension / spec | Annotate |
|---|---|---|
| Sloping ceiling | RF1 — **125** K107 between rafters tight to a breathable underlay, **25** residual gap, **72.5** K118 beneath | Starts at the dwarf wall head, **not** at the wall plate |
| Dwarf wall | EW2 — **89** K112 filling 89 x 38 studs at 400 between sole and head plate, **62.5** K118 to the room face | **0.17 W/m²K.** Generally **1050 to 1200** high as the sections |
| Void floor | insulation carried across the floor of the eaves void, filling the joist zone, lapped and sealed to the dwarf wall insulation at the foot | |
| Eaves void | outside the envelope, cross ventilated; insulated and draught sealed access hatch to each isolated section; services in the void insulated | |
| Floor | per IF1 — see D-221 | |

**The critical check — two corners, and one of them is invisible.** The insulation runs from the
sloping ceiling, down the face of the dwarf wall, and across the floor of the eaves void behind it.
The corner behind the wall is the one that gets missed, because once the dwarf wall is up nobody
can see whether it was done. Insulating the dwarf wall and leaving the void floor open makes the
ceiling below it the coldest surface in the house.

**Do not reduce the room-face board.** 62.5mm gives 0.17; **37.5mm gives 0.21 and does not meet
the standard for a new thermal element**, and 52.5mm gives 0.18 with no margin. The dwarf wall is
where floor width is tightest and it is the first board anyone offers to thin down.

**Also show:** the rafters over the eaves void are *not* insulated. The void is outside the
envelope and is ventilated; running the roof insulation down to the wall plate as well is a common
drawing error that puts insulation on both sides of a ventilated space.

---

## D-221 — New loft floor into the existing wall

**Substantiates:** REI 30 and Requirement E2 at the new floor, and the new floor spanning clear of
the existing ceiling.

**Section cuts** vertically **between joists**, where the new floor meets the existing wall.

| Component | Dimension / spec | Annotate |
|---|---|---|
| Beam | new steel beam at wall plate level on a padstone | **Indicative — engineer's design** |
| Joists | to the engineer's design, spanning independently of the existing ceiling joists; drawn 47 x 220 C24 at 400 | IF1 |
| Deck | **22** moisture resistant tongued and grooved board, glued and screwed | |
| Quilt | **100** mineral wool of minimum density **10 kg/m³** between the joists | Requirement E2 |
| Ceiling | **two layers of 12.5** plasterboard, joints staggered, taped and filled | **REI 30** |
| Existing ceiling | retained below; condition and fire resistance confirmed on site | |

**The critical check.** Two layers of 12.5 with staggered joints, not one layer of 25. The fire
resistance comes from the layering and the joint treatment and a single board does not give it
however thick it is. All perimeters and service penetrations sealed.

---

## D-222 — Existing gable to the new roof

**Substantiates:** a renovated thermal element meeting a new one, and the top of the gable where
the two standards meet.

**Section cuts** vertically **square to the roof slope**, so the roof reads flat and the gable
stands beside it.

| Component | Dimension / spec | Annotate |
|---|---|---|
| Existing wall | drawn as **215** solid brick | Confirm on site |
| Lining | EW3 — **72.5** K118 on dabs or battens, joints butted and taped, vapour control layer where the board has none | **0.26 W/m²K** on 215 solid brick |
| Continuity | lining carried up between the gable and the last rafter to meet the roof insulation | |
| Roof | RF1 — **125** K107 between rafters, **25** residual gap, **72.5** K118 beneath | **0.14 W/m²K** |

**The critical check.** Stop the gable lining at the sloping ceiling and the top 222mm of the gable
is uninsulated for the full length of the room. Carry it up between the gable and the last rafter
until it meets the K107, and draw the two touching.

**The two standards are different and that is correct, not an error.** The gable is a *renovated*
thermal element improved to **0.30** (0.26 achieved with 72.5mm board); the roof is a *new* element
at **0.15** (0.14 achieved). Where 0.18 cannot reasonably be reached on the gable, Approved
Document L allows a lesser standard on technical or functional feasibility grounds — state the
achieved value and the reasoning rather than leaving it unaddressed. 112.5mm board or a 90mm
insulated stud lining reaches 0.18 and the loss of floor width is weighed against it.

**Also note:** internal insulation on existing masonry raises the risk of interstitial
condensation. Inspect the wall for damp, defective pointing and cracked render and make good before
lining.

## After these five

Loft Conversion is complete against the register. The details it shares with the extension set —
the window head, jamb and cill — are drawn there and are reusable with only the build-up changing.

The next tranche is the shared ones: `D-209` separating wall to roof and `D-214` party wall at the
ground floor, which unlock New Build, New Build Flats and Flat Conversion at the same time.
