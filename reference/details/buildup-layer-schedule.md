# Build-up layer schedule — drawing data

The prose in `data/` specifies the construction. This sheet turns it into the ordered layers,
thicknesses and fixing centres a detail is drawn from. Every figure is taken from the library, so a
detail drawn from this sheet cannot contradict the specification. Where the two ever differ, the
library clause is right and this sheet is out of date.

Order is **outside to inside** for walls, **bottom to top** for floors and roofs — the order the
layers are built in.

---

## EW1 — Full fill cavity wall
Target 0.18 W/m²K · achieved **0.17 W/m²K** (0.18 with a 0.15 W/mK block)

| # | Layer | Thickness | Specification |
|---|---|---|---|
| 1 | Facing brick outer leaf | **103** | Matched to the existing dwelling, 1:1:6 cement:lime:sand mortar |
| 2 | Residual cavity | **10** nominal | Clear, between the face of the insulation and the back of the outer leaf |
| 3 | Full fill insulation | **90** | Kingspan Kooltherm K106, λ 0.019, held against the inner leaf |
| 4 | Aircrete blockwork inner leaf | **100** | λ 0.11 — Celcon Solar / Thermalite Turbo, 2.9N |
| 5 | Dabs | **10** nominal | Plasterboard adhesive |
| 6 | Plasterboard | **12.5** | |
| | **Overall** | **325.5** | 100 cavity = 10 residual + 90 board |

**Fixings to draw.** Stainless steel wall ties at **450 vertical × 900 horizontal, staggered**
(2.5 per m²); **225 vertical centres within 225** of every unbonded jamb, reveal and movement
joint. Ties set with a **slight fall to the outer leaf** — draw the fall, it reads as an error if
they are level or fall inwards.

**Must be shown continuous.** The insulation at every reveal, head and cill. Corner and reveal
geometry follows the BBA certificate, not site improvisation.

---

## GF1 — Solid floor, insulation over slab (screed finish)
Target 0.18 W/m²K · achieved **0.18** at P/A 0.7, **0.17** at P/A 0.5

| # | Layer | Thickness | Specification |
|---|---|---|---|
| 1 | Hardcore | **150** min finished | Compacted in layers not exceeding 150 |
| 2 | Sand blinding | **50** | Or other fine material, to protect the membrane |
| 3 | Ground-bearing slab | **100** min | GEN1 or RC20 to BS EN 206 and BS 8500 |
| 4 | Damp proof membrane | 1200 gauge (300 micron) min | 1600 gauge where radon, gas or the authority requires it. Lapped, sealed, **linked to the DPC in the walls** |
| 5 | Floor insulation | **80** | Kingspan Kooltherm K103 Floorboard, λ 0.019, tightly butted. **100 where P/A exceeds 0.7** |
| 6 | Vapour control layer | — | Over the insulation, 150 laps sealed, turned up at the perimeter behind the skirting |
| 7 | Screed | **65** min | Sand/cement, ready to receive the finish |
| | **FFL to top of slab** | **145** | 65 screed + 80 insulation |

**Perimeter.** **25** edge insulation around the full floor edge, the full depth of screed and
insulation. This is the piece that closes the bridge between the cavity insulation and the floor
insulation — on a detail it is the whole point of the drawing.

**Small extensions.** Three exposed sides pushes the perimeter/area ratio above 0.7 and the
U-value with it. 80mm at P/A 1.0 does not comply. Check the ratio before drawing 80.

---

## RF1 — Warm deck flat roof
Target 0.15 W/m²K · achieved **0.15** fully adhered (**0.16** mechanically fixed — use 160)

| # | Layer | Thickness | Specification |
|---|---|---|---|
| 1 | Timber joists | To engineer's design | |
| 2 | Deck | **18** | External quality plywood or OSB3, laid to falls on firrings |
| 3 | Vapour control layer | — | **Fully bonded to the deck**, all laps sealed |
| 4 | Insulation | **150** | Kingspan Thermaroof TR27, λ 0.024 at 120 and over, **break-bonded in two layers, fully adhered**. 160 if mechanically fixed |
| 5 | Waterproofing | — | Single ply or high-performance built-up felt, to the BBA certificate |

**Edges and abutments.** Proprietary edge trims. Upstands **not less than 150** at every abutment.
Cavity trays with stop ends and weep holes where the roof abuts a cavity wall.

> **Correct this in the library before you draw it.** The clause currently reads "a minimum finished
> fall of 1:40, achieved by a design fall of 1:80". That is the wrong way round and is impossible as
> written — a design fall can never be shallower than the finished fall it has to deliver, because
> deflection and construction tolerance only ever reduce it. The convention is a **design fall of
> 1:40 to achieve a minimum finished fall of 1:80**. Fix the clause first; the drawing then follows
> the clause.

---

## Foundations — what a detail may show

Both are drawn **indicative** and labelled "to the structural engineer's design". A library detail
must not appear to specify a foundation size.

| | Strip | Trench fill |
|---|---|---|
| Width | AD A Table 10 for the load and subsoil; not less than wall + 300 | Not less than wall + 300, and never less than **450** |
| Thickness | Not less than the projection each side, and **not less than 225** | Not less than **750** |
| Depth | Not less than **1000** below finished ground (600 to internal loadbearing walls) | As strip |
| Steps | No step to exceed the foundation thickness; higher to overlap lower by the greater of twice the step, the thickness, or **300** | As strip, but **not less than 1000** overlap |

**Substructure above the foundation, for D-201.** Dense concrete blockwork not less than
**7.0 N/mm²** both leaves. Cavity filled with lean mix to **not less than 225 below the DPC**,
top finished with a fall to the outside. **Weep holes above the fill and above external ground
level** — where the fill top falls below external ground, the weeps go above ground, not above the
fill. DPC **not less than 150 above finished external ground**, lapped **100** at joints, linked to
the floor DPM.

---

## Drawing conventions for the detail library

- **1:5** at A4 portrait; 1:10 only where the detail will not fit.
- Draw in real millimetres. Cut edges heaviest, then component outlines, then hatching, then
  leaders and dimension lines lightest.
- Hatch key on every sheet. Dimensions in millimetres. "Do not scale from this drawing."
- Put the build-up reference (EW1, GF1, RF1) against each element so the detail ties to the
  schedule.
- Status **For Building Control Approval**. Never "For Construction" on a library detail.
- Every dimension on a sheet must appear in this schedule. If it does not, it has been invented.
