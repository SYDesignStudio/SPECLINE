/* ================= Framed wall configurator — timber frame and dormer cheeks =================
   Shows on external wall, hip to gable, dormer cheek and dwarf wall categories, alongside the
   cavity wall configurator where both constructions are possible. Generates EW build-ups. */

const CFGFR_DEFAULT = {use:"frame", outer:"brick", insulation:"k112", thickness:140,
  studWidth:38, studDepth:140, spacing:600, sheathing:"osb9", lining:"none", void:0,
  gapLevel:1, limit:0.18};
function cfgFR(){ if(!S.cfgFR) S.cfgFR={...CFGFR_DEFAULT}; return S.cfgFR; }
function isFrameCat(cat){
  return /external wall|hip to gable|dormer construction \(walls\)|dwarf|ashlar/i.test(cat||"")
      && !/additional notes/i.test(cat||"");
}

/* The cladding sits outside a ventilated cavity, so it never changes the U-value.
   It changes the prose, the fire checks and the boundary check, which is why it is here. */
const FR_OUTER = [
  {id:"brick",  n:"Facing brickwork outer leaf",            desc:"103mm facing brickwork on stainless steel ties fixed to the studs, with a minimum 50mm clear ventilated and drained cavity", comb:false},
  {id:"tile",   n:"Tile hanging or slate",                  desc:"plain tile hanging or slate on treated battens and counter-battens, with a ventilated and drained cavity behind", comb:false},
  {id:"render", n:"Render on a carrier board",              desc:"a through-coloured silicone or polymer render system on a proprietary render carrier board fixed to treated battens, with a drained and ventilated cavity behind the board, stainless steel beads and a bellcast drip at the base", comb:false},
  {id:"timber", n:"Timber or fibre cement weatherboarding", desc:"vertical or horizontal boarding of a durable species — larch, western red cedar or thermally modified softwood — or fibre cement weatherboard, fixed with stainless steel fixings to treated battens and counter-battens", comb:true}
];
const FR_USE = [
  {id:"frame",  n:"Timber frame external wall"},
  {id:"cheek",  n:"Dormer cheek"},
  {id:"gable",  n:"Hip to gable — timber frame panel"},
  {id:"dwarf",  n:"Dwarf / ashlar wall at the eaves"}
];
const frOf = (list,id) => list.find(x=>x.id===id) || list[0];

function renderFrameConfigurator(cat){
  const c = cfgFR();
  /* a dormer cheek defaults to 400 centres and tile hanging; a wall to 600 and brick */
  if(!c._userUse){
    if(/dormer/i.test(cat||"") && c.use !== "cheek"){ c.use="cheek"; c.spacing=400; c.outer="tile"; }
    if(/dwarf|ashlar/i.test(cat||"") && c.use !== "dwarf"){ c.use="dwarf"; c.spacing=400; }
    if(/hip to gable/i.test(cat||"") && c.use !== "gable"){ c.use="gable"; }
  }
  if(c.thickness > c.studDepth) c.thickness = c.studDepth;
  const r = UC.frame(c), pass = r.U <= c.limit + 1e-9;

  return `<div class="card cfgcard"><div class="cfghead"><h3>Build a framed wall</h3>
    <span class="uval ${pass?"ok":"bad"}"><b>${r.U.toFixed(2)}</b> W/m²K <small>(${r.U.toFixed(3)})</small></span></div>
    <div class="cfgbar">${layerBar(r.layers)}${layerKey(r.layers)}</div>
    <p class="lede" style="margin-bottom:14px">The studs bridge the insulation, so the timber fraction matters as much as the board. The cladding and the ventilated cavity behind it are disregarded in the calculation, as BS EN ISO 6946 requires for a well-ventilated air layer — the outer finish changes the specification and the boundary check, not the U-value.</p>
    <div class="cfggrid">
      ${sel("fr_use",FR_USE.map(o=>({v:o.id,n:o.n})),c.use,"What is being built")}
      ${sel("fr_outer",FR_OUTER.map(o=>({v:o.id,n:o.n})),c.outer,"External finish (does not affect the U-value)")}
      ${sel("fr_insulation",UC.frameIns.map(i=>({v:i.id,n:i.n+"  (λ "+i.k+")"})),c.insulation,"Insulation between studs")}
      ${sel("fr_studDepth",UC.STUD_D.map(v=>({v,n:v+"mm"})),c.studDepth,"Stud depth")}
      ${sel("fr_thickness",UC.STUD_D.filter(v=>v<=c.studDepth).map(v=>({v,n:v+"mm"})),c.thickness,"Insulation thickness")}
      ${sel("fr_studWidth",UC.STUD_W.map(v=>({v,n:v+"mm"})),c.studWidth,"Stud width")}
      ${sel("fr_spacing",UC.STUD_SP.map(v=>({v,n:v+"mm centres"})),c.spacing,"Stud centres")}
      ${sel("fr_sheathing",UC.sheathing.map(o=>({v:o.id,n:o.n})),c.sheathing,"Sheathing")}
      ${sel("fr_lining",UC.underIns.map(o=>({v:o.id,n:o.n})),c.lining,"Internal lining")}
      ${sel("fr_void",UC.SERVICE_VOID.map(v=>({v,n:v?v+"mm battened":"None"})),c.void,"Service void")}
      ${sel("fr_gapLevel",UC.gapLevel.map(o=>({v:o.id,n:o.n})),c.gapLevel,"Air-gap correction")}
      ${sel("fr_limit",[{v:0.18,n:"0.18 — new element in an existing dwelling"},{v:0.26,n:"0.26 — new dwelling notional"},{v:0.30,n:"0.30 — retained element threshold"}],c.limit,"Target")}
    </div>
    ${r.notes.length?`<p class="cfgwarn">${r.notes.map(esc).join(" ")}</p>`:""}
    <details class="working"><summary>U-value working</summary>${workingTable(r)}
      <p class="srcnote" style="margin-top:10px">The timber fraction counts the studs at the stated centres only. Noggins, head and sole plates, headers and lintels add to it, so the certified calculation is to be obtained before submission.</p></details>
    <div class="cfgfoot"><span class="srcnote">Sources: ${[...new Set(r.src)].map(esc).join(" · ")}</span>
      <button class="btn btn-primary" id="addFrame">Add as EW build-up</button></div></div>`;
}

function frameSpecText(c,r){
  const use = frOf(FR_USE,c.use), outer = frOf(FR_OUTER,c.outer);
  const ins = frOf(UC.frameIns,c.insulation), sheath = frOf(UC.sheathing,c.sheathing);
  const lin = frOf(UC.underIns,c.lining);
  const U = r.U.toFixed(2);
  const t = Math.min(c.thickness, c.studDepth);
  const noun = {frame:"Timber frame external wall", cheek:"Dormer cheek",
                gable:"Hip to gable timber frame panel", dwarf:"Dwarf wall at the eaves"}[c.use];

  const p = [
    `${noun} finished externally in ${outer.desc}, on a breather membrane${sheath.d?` over ${sheath.n.toLowerCase()}`:""}, framed in ${c.studWidth} × ${c.studDepth}mm C16 studs at ${c.spacing}mm centres to the frame designer's specification with head and sole plates and solid noggins at board edges. The full ${t}mm between the studs is filled with ${ins.n} (thermal conductivity ${ins.k} W/mK), tightly butted and cut to a firm friction fit with no gaps at the studs, plates or openings.`,

    `${c.void ? `A ${c.void}mm battened service void is formed on the warm side of a continuous vapour control layer, so that sockets, switches and cabling do not penetrate it. ` : `A continuous vapour control layer is provided on the warm side of the insulation, sealed at all laps, junctions and service penetrations. `}${lin.t ? `The lining is ${lin.n.split(" (")[0]}, giving ${lin.t}mm of continuous insulation across the studs, with joints taped.` : `The lining is ${lin.pb}mm plasterboard with a skim finish.`} All perimeters sealed to maintain the air barrier.`,

    `This build-up calculates at ${U} W/m²K to BS EN ISO 6946 by the combined method, allowing for the studs bridging the insulation at ${(r.f*100).toFixed(1)}% of the area at ${c.spacing}mm centres. The cladding and the ventilated cavity behind it are disregarded and the external surface resistance taken as still air, as BS EN ISO 6946 requires for a well-ventilated air layer; the outer finish therefore does not change the U-value.`,

    c.outer === "brick"
      ? `Stainless steel wall ties to be fixed to the studs at 450mm vertical centres and at every stud horizontally, with additional ties at openings and movement joints. Cavity barriers to be provided at the perimeter of the panel, at every junction with the main roof or an adjoining wall, and around openings, in accordance with Approved Document B. All timber to be treated and isolated from masonry by a damp proof course.`
      : `Cavity barriers to be provided at the perimeter of the panel, at every junction with the main roof or an adjoining wall, and around openings, in accordance with Approved Document B. Battens and counter-battens to be treated softwood, fixed with stainless steel fixings, and all timber isolated from masonry by a damp proof course.`
  ];

  if(c.use === "cheek"){
    p.push(`Where the cheek is close to a boundary, the fire resistance and the extent of unprotected area are to be checked against Approved Document B before construction.${outer.comb ? " Timber boarding is a combustible surface: within 1m of the boundary it is to be fire retardant treated to Class B-s3, d2, or the cheek clad in a non-combustible finish instead." : ""}`);
  } else if(outer.comb){
    p.push(`Timber boarding is a combustible surface. Where the wall is within 1m of the relevant boundary the cladding is to be fire retardant treated to Class B-s3, d2, or a non-combustible finish used instead, and the extent of unprotected area checked against Approved Document B.`);
  }

  const notes = [
    `NOTE — The timber fraction in the calculation counts the studs at ${c.spacing}mm centres only. Noggins, head and sole plates, headers and lintels increase it, so the manufacturer's or the frame designer's certified calculation is to be obtained before submission.`
  ];
  if(!r.notes.length && t === c.studDepth && !c.void && lin.t === 0){
    notes.push("NOTE — Confirm on site that no socket, switch or cable penetrates the vapour control layer, or add a battened service void before the lining is fixed.");
  }
  r.notes.forEach(n => notes.push("NOTE — " + n));

  const title = `${noun} — ${t}mm ${ins.n.split(" ")[0] === "Mineral" ? "mineral wool" : ins.n.split(" ").slice(0,3).join(" ")}${lin.t?` + ${lin.n.split(" (")[0].split(" ").slice(-1)[0]} lining`:""}`;

  return {
    g:"EW", cat:"__frame__", t:title, u:U+" W/m²K",
    tgt:`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${U} W/m²K to BS EN ISO 6946 allowing for stud bridging — see U-value working)`,
    p: p.concat(notes),
    calc:{params:{...c}, result:{U:r.U,U0:r.U0,dUg:r.dUg,dUf:0,RT:r.RT,RT_upper:r.RT_upper,RT_lower:r.RT_lower,
          layers:r.layers.map(l=>({n:l.n,d:l.d,R:l.R})), src:[...new Set(r.src)]}}
  };
}

function bindConfigurator4(){
  document.querySelectorAll(".cfgcard select[data-cf]").forEach(s=>{
    if(s.dataset.bound4) return;
    const card = s.closest(".cfgcard");
    if(!card.querySelector("#addFrame")) return;
    s.dataset.bound4 = "1"; s.dataset.bound = "1";   /* keep configurator2 off this card */
    s.onchange = () => {
      const k = s.dataset.cf.replace(/^fr_/, ""); let v = s.value;
      if(["thickness","studWidth","studDepth","spacing","void","gapLevel"].includes(k)) v = +v;
      if(k === "limit") v = parseFloat(v);
      const c = cfgFR(); c[k] = v;
      if(k === "use") c._userUse = 1;
      if(k === "studDepth" && c.thickness > v) c.thickness = v;
      renderStage(); save();
    };
  });
  const a = el("addFrame");
  if(a) a.onclick = () => {
    const c = cfgFR(), r = UC.frame(c);
    S.custom = S.custom || []; S.custom.push(frameSpecText(c,r));
    const idx = allBU().length - 1; S.sel.push(idx);
    renderStage(); renderSteps(); renderPaper(); save(); toast("Added " + refs()[idx]);
  };
}
