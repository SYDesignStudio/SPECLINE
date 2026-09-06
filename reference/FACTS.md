# Verified reference figures (checked against the Approved Documents / manufacturers on 04–05 Sept 2026)

## AD L Volume 1 (2021 edition, as amended 2023) — England
- Notional new dwelling: wall 0.18, floor 0.13, roof 0.11, windows 1.2, rooflights 1.7 (whole-unit, horizontal), doors 1.0 W/m²K; air permeability 5 m³/(h·m²)@50Pa.
- Table 4.1 limiting (new dwellings): wall 0.26, floor 0.18, roof 0.16, party wall 0.20, windows/doors 1.6, rooflights 2.2, AP 8.
- Table 4.2 new elements in existing dwellings (extensions, lofts, conversions): wall 0.18, floor 0.18, roof 0.15, windows 1.4 (or WER B), rooflights 2.2 (or C), doors 1.4 (or DSER B/C).
- Table 4.3 renovated / retained thermal elements: roof (all types) threshold 0.35 → improve to 0.16; cavity wall 0.70 → 0.55; other walls 0.70 → 0.30; floor 0.70 → 0.25.
- Fixed lighting: minimum 75 lumens per circuit-watt for ALL fixed internal and external lighting (no 75%-of-fittings rule any more); fittings under 5 circuit-watts excluded. External lighting also controlled off in daylight / when not needed.
- Heating: wet systems designed for max 55°C flow; gas boilers ≥92% ErP; controls Section 5 (zones, TRVs, cylinder stat, interlock); pipework insulation Table 4.4.
- Extension glazing ≤25% of extension floor area + openings closed off.
- Future Homes Standard: AD L1 and F1 2026 editions published 24 March 2026, in force 24 March 2027, transitional commencement cut-off 24 March 2028 (new dwellings).

## AD F Volume 1 (2021)
- Intermittent extract Table 1.1: kitchen 30 l/s (cooker hood) / 60 l/s elsewhere; utility 30; bathroom 15; WC 6. Continuous: kitchen 13, bath/utility 8, WC 6; whole-dwelling ≥0.3 l/s/m² and bedroom-count rate.
- Background ventilators Table 1.7: 8000 mm² per habitable room/kitchen in multi-storey dwellings, 10,000 mm² single-storey/flats, 4000 mm² wet rooms; ≥1700 mm above floor. MEV (System 3): 4000 mm² per habitable room, bedrooms + 2 minimum.
- Purge: 1/20 floor area (opens ≥30°), 1/10 (15–30°); door undercut 10 mm (7600 mm² for 760 door).
- Commissioning results to BCB within 5 days. Cooker hoods 650–750 mm above hob.

## Reg 16 (as amended Oct 2023)
- Notice of intention: at least 2 clear days before start.
- Commencement notice within 5 days of Reg 46A commencement (new building / horizontal extension: sub-structure incl. ground floor structure complete; other work: 15% complete).
- Completion notice within 5 days of completion, with client, principal designer and principal contractor details and compliance statements.

## AD B Volume 1 (2019 + 2020/2022 amendments)
- Alarms: minimum Grade D2 Category LD3 to BS 5839-6; SY Design Studio standard is Grade D1 Category LD2 house-wide (mains, tamper-proof standby), heat alarm in kitchen, interlinked, CO alarm to BS EN 50291 where combustion appliance.
- Escape window: openable area ≥0.33 m², ≥450 mm × 450 mm, bottom of openable area ≤1100 mm above floor (not below 800 mm unless guarded); rooms ≤4.5 m above ground.
- Loft (3-storey house): protected stair to final exit or two escape routes, FD30 doors (self-closers not required in a dwellinghouse but FD30S adopted); alternatives sprinklers etc.
- Fire doors: use "FD30S doorset" (E 30 Sa) wording; garage separation REI 30, 100 mm step or fall.
- Boundary: unprotected areas within 1 m ≤1 m² & 4 m apart; roof BROOF(t4) within 6 m; Section 11 table values 5.6/12/18/24/30 m² at 1–5 m.
- Flats: separating floors/walls REI 60 (REI 30 where ≤5 m top storey / 2-storey house conversions may be 30 in some cases — state accurately); flat entrance doors FD30S; fire-fighting: B4(1) applies to >11 m in conversions (Regulation 6 MCU: Q1 and S2 apply to flat conversions, O1 does not).
- Regulation 38 fire safety information for buildings with flats/new dwellings that are non-single-dwelling.

## AD A Section 2E — foundation fallback (used by the FD configurator, 06/09/2026)
These are the rules the foundation configurator checks against. Every one of them was already
stated in the library's own foundation notes (extension, garage, garagebld) citing Approved
Document A Section 2E; they are recorded here because a calculator now depends on them.
- Strip: thickness not less than the projection of the foundation beyond each face of the wall, and in no case less than 150 mm. Projection each side = (width − wall thickness) ÷ 2.
- Width: from AD A **Table 10** for the wall load and the subsoil, or the engineer's design. **Table 10 values are NOT held in this repo and are NOT verified** — the width is always an input and every generated FD entry carries a NOTE to confirm it.
- Trench fill: not less than 450 mm wide.
- Depth: not less than 750 mm below finished ground level generally, not less than 1000 mm in shrinkable clay. Internal loadbearing walls not less than 600 mm deep.
- Steps: step height not to exceed the foundation thickness; the higher foundation overlaps the lower by the greatest of twice the step, the thickness, and 300 mm (1 m for trench fill).
- Trees within influencing distance: depth follows **NHBC Chapter 4.2** and the engineer's recommendation, with heave precautions where trees have been or are to be removed. Not computed.
- Soft clay, made ground, fill or variable ground: the Section 2E fallback does not apply — raft or piled to the engineer's design, after ground investigation. Raft reinforcement lapped 450 mm, 40 mm cover.
- Sulfates: BS 8500 design chemical class from the **ground investigation report**, never derived from the soil description. Concrete to BS EN 206 and BS 8500.

## AD C / other
- Cavity fill 225 mm below DPC; DPC ≥150 mm above ground; oversite 100 mm concrete or 50 mm on DPM; BS 5250 50 mm void above rafter insulation under non-breathable underlay; suspended floor void ventilation 1500 mm²/m or 500 mm²/m².
- PD 6697 wall ties 900×450 (2.5/m²), 300 mm vertical centres within 225 mm of jambs.
- AD H drain cover 600 (gardens) / 900 (drives); drainage field 15 m from building, 10 m watercourse, 50 m well.
- AD M Table 1.1 corridor widths (door 750 → 1200; 775 → 1050; 800 → 900); M4(3) storage 1.5/2.0/2.5/3.0 m².
- AD E: separating wall 45 dB DnT,w+Ctr (new build) / 43 dB (conversions); floors 45/43 dB airborne, 62/64 dB LnT,w impact; internal walls/floors 40 dB Rw.
- AD G3: cylinder stored ≥60°C; bath supply ≤48°C by TMV (BS EN 1111/1287); unvented systems by competent person; G2 new dwellings 125 l/person/day (110 optional).
- AD K: private stair rise 150–220, going ≥220, pitch ≤42°, 2R+G 550–700, headroom 2 m, handrail 900–1000, guarding 900 internal / 1100 external balconies, 100 mm sphere, guarding load 0.36 kN/m dwellings.
- AD J: hearth 125 mm concrete, 500 mm front/150 mm sides; flue ≥150 mm closed appliance ≤30 kW; air supply 550 mm² per kW over 5 kW; CO alarm.
- AD P: notifiable work by registered competent person; sockets/switches 450–1200 mm in new dwellings (M).

## Materials (manufacturer-verified λ W/mK, 05/09/2026)
Kingspan K103/K106/K107/K108/K118 = 0.019; TF70 0.022; TR26 0.022; TR27 0.027 (<80 mm) / 0.025 (80–119) / 0.024 (≥120). Celotex is now SOPRATHERM (CW4000/GA4000/XR4000/PL4000 0.022; Thermaclass 21 0.021). Unilin (ex-Xtratherm) CavityTherm 0.021, XT/CW, XT/PR-UF, FR/ALU 0.022. EcoTherm Eco-Cavity full/partial 0.022, Eco-Versal 0.022. ROCKWOOL Full Fill 0.037; Knauf DriTherm 32/37. Aircrete 7.3N λ 0.18/0.185.
