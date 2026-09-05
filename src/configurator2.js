
/* ================= Floor and roof configurators ================= */
const CFGF_DEFAULT={kind:"solid",ground:"clay",insulation:"tf70",thickness:100,slab:"c100",finish:"screed65",edge:"e25x150",pa:0.5,deck:"timber",joistDepth:150,spacing:400,vent:1500,limit:0.18,depth:2.7,wall:300,wallThk:100};
const CFGR_DEFAULT={kind:"flat",insulation:"tr27",thickness:150,joistDepth:200,spacing:400,fixing:"adhered",
                    rIns:"k107",rThick:150,rafterDepth:150,rSpacing:400,under:"k118_625",gapLevel:1,
                    quilt:"lr44",between:100,over:300,cjDepth:100,cSpacing:400,limit:0.15};
function cfgF(){ if(!S.cfgF) S.cfgF={...CFGF_DEFAULT}; return S.cfgF; }
function cfgR(){ if(!S.cfgR) S.cfgR={...CFGR_DEFAULT}; return S.cfgR; }
function isFloorCat(cat){ return /ground floor|basement floor|basement wall/i.test(cat||""); }
function isBasementCat(cat){ return /basement/i.test(cat||""); }
function isRoofCat(cat){ return /roof/i.test(cat||"") && !/dormer construction \(walls\)|additional notes/i.test(cat||""); }

function floorResult(c){
  if(c.kind==="basement") return UC.basement({ground:c.ground,floorIns:c.insulation,wallIns:c.insulation,pa:c.pa,depth:c.depth,wall:c.wall,floorThk:c.thickness,wallThk:c.wallThk,slab:200});
  return c.kind==="solid" ? UC.floorSolid(c)
       : UC.floorSuspended({...c, deck:c.kind==="bb"?"bb":"timber"});
}
function roofResult(c){
  if(c.kind==="flat")    return UC.roofFlat({insulation:c.insulation,thickness:c.thickness,joistDepth:c.joistDepth,spacing:c.spacing,fixing:c.fixing});
  if(c.kind==="rafter")  return UC.roofRafter({insulation:c.rIns,thickness:c.rThick,rafterDepth:c.rafterDepth,spacing:c.rSpacing,under:c.under,gapLevel:c.gapLevel});
  return UC.roofCeiling({quilt:c.quilt,between:c.between,over:c.over,joistDepth:c.cjDepth,spacing:c.cSpacing});
}
const PA_OPTS=[0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.2,1.5];
const DEPTHS=[100,125,150,175,200,225];
function stepsTable(r){
  if(!r.steps) return "";
  return `<table class="wk"><tr><th>Step</th><th></th><th>Value</th></tr>`+r.steps.map(([a,b])=>`<tr><td>${esc(a)}</td><td></td><td>${esc(b)}</td></tr>`).join("")+`</table>`;
}
function layersOnly(r){
  return `<table class="wk"><tr><th>Layer</th><th>mm</th><th>R (m²K/W)</th></tr>`+
    r.layers.map(l=>`<tr><td>${esc(l.n)}${l.bridged?` <i>(combined method: ${(l.fb*100).toFixed(1)}% / ${(l.fm*100).toFixed(1)}%)</i>`:""}</td><td>${l.d!=null?l.d:"—"}</td><td>${l.R.toFixed(3)}</td></tr>`).join("")+`</table>`;
}

function renderFloorConfigurator(cat){
  const c=cfgF(); const ins=UC.floorIns.find(x=>x.id===c.insulation)||UC.floorIns[0];
  const bcat=isBasementCat(cat);
  if(bcat && c.kind!=="basement" && !c._userKind){ c.kind="basement"; if(c.insulation==="tf70") c.insulation="k103"; }
  if(!bcat && c.kind==="basement" && !c._userKind) c.kind="solid";
  if(!ins.th.includes(c.thickness)) c.thickness=ins.th.includes(100)?100:ins.th[0];
  if(!ins.th.includes(c.wallThk)) c.wallThk=ins.th.includes(100)?100:ins.th[0];
  const r=floorResult(c); const pass=r.U<=c.limit+1e-9;
  const isB=c.kind==="basement";
  let h=`<div class="card cfgcard"><div class="cfghead"><h3>${isB?"Build a heated basement floor and wall":"Build a ground floor"}</h3>
    <span class="uval ${pass?"ok":"bad"}"><b>${r.U.toFixed(2)}</b> W/m²K <small>(${r.U.toFixed(3)})</small></span></div>
    <div class="cfgbar">${layerBar(r.layers)}${layerKey(r.layers)}</div>
    <p class="lede" style="margin-bottom:14px">${isB?"Heated basements are calculated to BS EN ISO 13370 — the ground reduces the heat loss with depth, so the below-ground wall and the basement floor are calculated together and reported as an area-weighted U-value.":"Ground floors are calculated to BS EN ISO 13370 — the U-value depends on the floor's perimeter-to-area ratio and the ground beneath as much as on the insulation."}</p>
    <div class="cfggrid">
      ${sel("kind",[{v:"solid",n:"Solid — insulation over slab"},{v:"timber",n:"Suspended timber"},{v:"bb",n:"Beam and block"},{v:"basement",n:"Heated basement — floor and below-ground wall"}],c.kind,"Floor type")}
      ${isB?sel("depth",[1.5,2.0,2.4,2.7,3.0,3.5].map(v=>({v,n:v.toFixed(1)+" m below ground"})),c.depth,"Basement depth"):""}
      ${isB?sel("wall",[215,250,300,350].map(v=>({v,n:v+"mm RC / masonry"})),c.wall,"Retaining wall"):""}
      ${isB?sel("wallThk",ins.th.map(v=>({v,n:v+"mm"})),c.wallThk,"Wall lining insulation (same board)"):""}
      ${sel("pa",PA_OPTS.map(v=>({v,n:v.toFixed(1)})),c.pa,"P/A ratio (exposed perimeter ÷ area)")}
      ${sel("ground",UC.ground.map(o=>({v:o.id,n:o.n})),c.ground,"Ground type")}
      ${sel("insulation",UC.floorIns.map(i=>({v:i.id,n:i.n+"  (λ "+i.k+")"})),c.insulation,"Insulation")}
      ${sel("thickness",ins.th.map(v=>({v,n:v+"mm"})),c.thickness,isB?"Floor insulation thickness":"Insulation thickness")}
      ${c.kind==="solid"?sel("slab",UC.slabs.filter(x=>x.id!=="bb150").map(o=>({v:o.id,n:o.n})),c.slab,"Slab"):""}
      ${c.kind==="solid"?sel("finish",UC.floorFinish.map(o=>({v:o.id,n:o.n})),c.finish,"Finish"):""}
      ${c.kind==="solid"?sel("edge",UC.edgeIns.map(o=>({v:o.id,n:o.n})),c.edge,"Perimeter upstand"):""}
      ${c.kind==="timber"?sel("joistDepth",DEPTHS.map(v=>({v,n:"47 × "+v})),c.joistDepth,"Joists"):""}
      ${c.kind==="timber"?sel("spacing",[400,450,600].map(v=>({v,n:v+"mm centres"})),c.spacing,"Joist centres"):""}
      ${c.kind!=="solid"&&!isB?sel("vent",[1500,2000,3000].map(v=>({v,n:v+" mm²/m"})),c.vent,"Void ventilation"):""}
      ${sel("limit",[{v:0.18,n:"0.18 — new element in extension"},{v:0.13,n:"0.13 — new dwelling notional"},{v:0.25,n:"0.25 — retained element threshold"}],c.limit,"Target")}
    </div>
    ${r.notes.length?`<p class="cfgwarn">${r.notes.map(esc).join(" ")}</p>`:""}
    <details class="working"><summary>U-value working</summary>${layersOnly(r)}${stepsTable(r)}</details>
    <div class="cfgfoot"><span class="srcnote">Sources: ${[...new Set(r.src)].map(esc).join(" · ")}</span>
      <button class="btn btn-primary" id="addFloor">Add as ${isB?"BF":"GF"} build-up</button></div></div>`;
  return h;
}
function renderRoofConfigurator(){
  const c=cfgR(); let r, body="";
  if(c.kind==="flat"){
    const ins=UC.flatIns.find(x=>x.id===c.insulation)||UC.flatIns[0]; if(!ins.th.includes(c.thickness)) c.thickness=ins.th.includes(150)?150:ins.th[0];
    r=roofResult(c);
    body=sel("insulation",UC.flatIns.map(i=>({v:i.id,n:i.n+"  (λ "+(i.kl||i.k)+")"})),c.insulation,"Insulation")+
         sel("thickness",ins.th.map(v=>({v,n:v+"mm"})),c.thickness,"Thickness")+
         sel("joistDepth",DEPTHS.map(v=>({v,n:"47 × "+v})),c.joistDepth,"Joists")+
         sel("spacing",[400,450,600].map(v=>({v,n:v+"mm centres"})),c.spacing,"Joist centres")+
         sel("fixing",[{v:"adhered",n:"Fully adhered"},{v:"mech",n:"Mechanically fixed"}],c.fixing,"Insulation fixing");
  } else if(c.kind==="rafter"){
    r=roofResult(c);
    body=sel("rIns",UC.rafterIns.map(i=>({v:i.id,n:i.n+"  (λ "+i.k+")"})),c.rIns,"Between rafters")+
         sel("rThick",[50,75,100,125,150,175,200].map(v=>({v,n:v+"mm"})),c.rThick,"Between-rafter thickness")+
         sel("rafterDepth",DEPTHS.map(v=>({v,n:"47 × "+v})),c.rafterDepth,"Rafters")+
         sel("rSpacing",[400,450,600].map(v=>({v,n:v+"mm centres"})),c.rSpacing,"Rafter centres")+
         sel("under",UC.underIns.map(i=>({v:i.id,n:i.n})),c.under,"Under rafters")+
         sel("gapLevel",UC.gapLevel.map(o=>({v:o.id,n:o.n})),c.gapLevel,"Air-gap correction");
  } else {
    r=roofResult(c);
    body=sel("quilt",UC.quilt.map(i=>({v:i.id,n:i.n})),c.quilt,"Mineral wool")+
         sel("between",[100,150,200].map(v=>({v,n:v+"mm"})),c.between,"Between joists")+
         sel("over",[0,100,150,170,200,250,300].map(v=>({v,n:v?v+"mm":"none"})),c.over,"Over joists")+
         sel("cjDepth",[100,125,150,175,200].map(v=>({v,n:"47 × "+v})),c.cjDepth,"Ceiling joists")+
         sel("cSpacing",[400,450,600].map(v=>({v,n:v+"mm centres"})),c.cSpacing,"Joist centres");
  }
  const pass=r.U<=c.limit+1e-9;
  return `<div class="card cfgcard"><div class="cfghead"><h3>Build a roof</h3>
    <span class="uval ${pass?"ok":"bad"}"><b>${r.U.toFixed(2)}</b> W/m²K <small>(${r.U.toFixed(3)})</small></span></div>
    <div class="cfgbar">${layerBar(r.layers)}${layerKey(r.layers)}</div>
    <p class="lede" style="margin-bottom:14px">Calculated to BS EN ISO 6946 with the combined method for rafter and joist bridging. Rafter bridging roughly halves the effective resistance of a high-performance board — thinner arrangements miss the target by more than intuition suggests.</p>
    <div class="cfggrid">
      ${sel("kind",[{v:"flat",n:"Warm deck flat roof"},{v:"rafter",n:"Pitched — insulation at rafter level"},{v:"ceiling",n:"Pitched — insulation at ceiling level"}],c.kind,"Roof type")}
      ${body}
      ${sel("limit",[{v:0.15,n:"0.15 — new element in extension"},{v:0.11,n:"0.11 — new dwelling notional"},{v:0.16,n:"0.16 — renovated element (ceiling level)"},{v:0.18,n:"0.18 — renovated element (rafter / flat)"}],c.limit,"Target")}
    </div>
    ${r.notes.length?`<p class="cfgwarn">${r.notes.map(esc).join(" ")}</p>`:""}
    <details class="working"><summary>U-value working</summary>${workingTable(r)}</details>
    <div class="cfgfoot"><span class="srcnote">Sources: ${[...new Set(r.src)].map(esc).join(" · ")}</span>
      <button class="btn btn-primary" id="addRoof">Add as RF build-up</button></div></div>`;
}

function floorSpecText(c,r){
  const ins=UC.floorIns.find(x=>x.id===c.insulation), g=UC.ground.find(x=>x.id===c.ground);
  const pa=(+c.pa).toFixed(1), U=r.U.toFixed(2);
  const tgt=`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${U} W/m²K to BS EN ISO 13370 at P/A ${pa} on ${g.n.split(" (")[0].toLowerCase()} — see U-value working; confirm the perimeter/area ratio and ground type against the site)`;
  let t,p;
  if(c.kind==="basement"){
    const tb=`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${U} W/m²K area-weighted to BS EN ISO 13370 for a heated basement ${(+c.depth).toFixed(1)}m below ground at P/A ${pa} on ${g.n.split(" (")[0].toLowerCase()}: floor ${r.Ubf.toFixed(2)}, below-ground wall ${r.Ubw.toFixed(2)} — see U-value working)`;
    t=`Heated Basement — ${c.thickness}mm ${ins.n.split(" ")[0]} floor, ${c.wallThk}mm wall lining`;
    p=[`Basement slab of 200mm minimum reinforced concrete and ${c.wall}mm reinforced concrete or masonry retaining walls to the structural engineer's design, waterproofed to Grade 3 of BS 8102:2022 by two forms of protection as the waterproofing specialist's design, with a Type C cavity drainage membrane to the walls and floor draining to a perimeter channel and a sump with duplicate pumps, battery back-up and a high-level alarm.`,
       `Floor: ${c.thickness}mm ${ins.n} laid over the floor membrane with 25mm perimeter upstands, a separating layer and a 75mm screed. Walls: ${c.wallThk}mm ${ins.n.replace("Floorboard","board")} on treated battens or independent studs clear of the wall membrane, a continuous vapour control layer taped at all joints and to the floor and ceiling, and 12.5mm plasterboard; no fixing to penetrate the membrane other than the manufacturer's sealed plugs.`,
       `The below-ground elements are calculated together to BS EN ISO 13370 for a heated basement: the floor at ${r.Ubf.toFixed(2)} W/m²K and the wall at ${r.Ubw.toFixed(2)} W/m²K, weighted by area to ${U}. Any part of the wall exposed above ground is an external wall and is to be insulated as one. The basement depth, perimeter/area ratio and ground type are to be confirmed against the site before issue.`];
    return {g:"BF",cat:"__floor__",t,u:U+" W/m²K",tgt:tb,p,
      calc:{params:{...c},result:{U:r.U,U0:r.U,dUg:0,dUf:0,dUe:0,RT:1/r.U,RT_upper:1/r.U,RT_lower:1/r.U,layers:r.layers.map(l=>({n:l.n,d:l.d,R:l.R})),steps:r.steps,src:[...new Set(r.src)]}}};
  }
  if(c.kind==="solid"){
    const slab=UC.slabs.find(x=>x.id===c.slab), fin=UC.floorFinish.find(x=>x.id===c.finish), edge=UC.edgeIns.find(x=>x.id===c.edge);
    t=`Solid Ground Floor — ${c.thickness}mm ${ins.n.split(" ")[0]} over slab`;
    p=[`Ground floor built up from the formation as compacted hardcore in layers not exceeding 150mm to a minimum 150mm finished thickness, blinded with 50mm sand; a proprietary polyethylene damp proof membrane of not less than 1200 gauge lapped 150mm and sealed at joints and linked to the wall damp proof course; ${slab.n.toLowerCase()} in GEN1 or RC20 concrete to BS EN 206 and BS 8500; ${c.thickness}mm ${ins.n} laid over the slab with joints tightly butted${fin.layers.length?`; a separating layer; and ${fin.n.toLowerCase()} ready to receive the floor finish`:"; and the slab power-floated as the finished surface"}.`,
       edge.D>0?`${edge.n} to be carried around the full floor perimeter against the inner leaf, lapped to the floor insulation, to limit thermal bridging at the wall/floor junction. Its effect on the area U-value is small; its purpose is the junction psi-value.`:`No perimeter upstand is specified. The wall/floor junction is to be detailed to limit thermal bridging, and the junction psi-value confirmed where relied upon in the SAP calculation.`,
       `The U-value of a ground floor depends on its perimeter-to-area ratio and on the ground beneath. This build-up is calculated at P/A ${pa}; where the floor plan differs materially, the ratio is to be re-measured and the U-value recalculated before issue.`];
  } else if(c.kind==="timber"){
    t=`Suspended Timber Ground Floor — ${c.thickness}mm ${ins.n.split(" ")[0]} between joists`;
    p=[`Suspended timber ground floor of 47mm x ${c.joistDepth}mm C16 joists at ${c.spacing}mm centres to the structural engineer's design, with ${Math.min(c.thickness,c.joistDepth)}mm ${ins.n} fitted tightly between the joists on breathable support netting${c.thickness>c.joistDepth?` and a further ${c.thickness-c.joistDepth}mm below the joists`:""}, decked with 22mm moisture resistant tongued and grooved flooring grade board glued and screwed.`,
       `A minimum 150mm clear ventilated void is to be maintained beneath the joists, with through ventilation to opposing external walls of not less than ${c.vent}mm² per metre run by proprietary air bricks and telescopic ducts carried through the cavity. Oversite of 100mm concrete or compacted hardcore blinded over a damp proof membrane. All timber isolated from masonry by a damp proof course.`,
       `The joists bridge the insulation and the ventilated void draws heat from beneath; both are allowed for in the calculation. Where the target is not met, insulation is to be added below the joists rather than the ventilation reduced.`];
  } else {
    t=`Beam and Block Ground Floor — ${c.thickness}mm ${ins.n.split(" ")[0]} over deck`;
    p=[`Precast prestressed concrete beams to the manufacturer's design with infill blocks, joints grouted, over a minimum 150mm clear ventilated void with through ventilation of not less than ${c.vent}mm² per metre run to opposing external walls. Damp proof membrane over the deck, ${c.thickness}mm ${ins.n} laid over with joints tightly butted, a vapour control layer where required by the insulation manufacturer, and a 65mm minimum sand/cement screed.`,
       `Beam layout, bearings and trimming to openings to the manufacturer's design coordinated with the structural engineer. Oversite to be treated to prevent plant growth.`];
  }
  return {g:"GF",cat:"__floor__",t,u:U+" W/m²K",tgt,p,
    calc:{params:{...c},result:{U:r.U,U0:r.U0,dUg:0,dUf:0,dUe:r.dUe||0,RT:r.Rf,RT_upper:r.Rf,RT_lower:r.Rf,layers:r.layers.map(l=>({n:l.n,d:l.d,R:l.R})),steps:r.steps,src:[...new Set(r.src)]}}};
}
function roofSpecText(c,r){
  const U=r.U.toFixed(2);
  let t,p,tgt;
  if(c.kind==="flat"){
    const ins=UC.flatIns.find(x=>x.id===c.insulation);
    t=`Warm Deck Flat Roof — ${c.thickness}mm ${ins.n.split(" ")[0]}`;
    tgt=`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${U} W/m²K to BS EN ISO 6946 — see U-value working)`;
    p=[`Warm deck flat roof of 47mm x ${c.joistDepth}mm joists at ${c.spacing}mm centres to the structural engineer's design, 18mm external quality plywood or OSB3 decking laid to falls, a vapour control layer fully bonded to the deck with all laps sealed, ${c.thickness}mm ${ins.n} ${c.fixing==="mech"?"mechanically fixed":"fully adhered"} in two break-bonded layers, and a single ply or high performance built-up waterproofing system to the manufacturer's specification and BBA certificate.`,
       `Falls to be a minimum finished 1:40 achieved by firrings or a tapered insulation scheme. Upstands not less than 150mm at all abutments with cavity trays and stepped flashings at masonry. The joist void is unventilated and the vapour control layer must be continuous for the warm deck to perform; cold deck construction is not to be used.`,
       c.fixing==="mech"?`Mechanical fixings through the insulation are allowed for in the calculation as a fastener correction. Where the system is fully adhered instead, the U-value improves slightly.`:`The insulation is fully adhered; no fastener correction applies. Where mechanical fixings are substituted the U-value is to be recalculated.`];
  } else if(c.kind==="rafter"){
    const ins=UC.rafterIns.find(x=>x.id===c.rIns), und=UC.underIns.find(x=>x.id===c.under);
    const tb=Math.min(c.rThick,c.rafterDepth);
    t=`Pitched Roof at Rafter Level — ${tb}mm ${ins.n.split(" ")[0]} between + ${und.t?und.n.split(" (")[0]:"plasterboard"}`;
    tgt=`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${U} W/m²K to BS EN ISO 6946 at ${c.rSpacing}mm rafter centres, allowing for rafter bridging — see U-value working)`;
    p=[`Roof covering on battens and counter-battens over a breathable roofing underlay to BS 5534, on 47mm x ${c.rafterDepth}mm rafters at ${c.rSpacing}mm centres to the structural engineer's design. ${tb}mm ${ins.n} fitted tightly between the rafters${tb<c.rafterDepth?` leaving a ${c.rafterDepth-tb}mm gap above, ventilated where a non-breathable underlay is used`:", fully filling the rafter depth, which requires a breathable underlay"}${und.t?`, with ${und.n} fixed beneath the rafters through to the timbers`:", with 12.5mm plasterboard beneath"}, joints staggered, tightly butted and taped.`,
       `A continuous vapour control layer on the warm side of the insulation, sealed at all laps, junctions and service penetrations. Downlighters are not to penetrate the vapour control layer unless a proprietary sealed hood is used.`,
       `The rafters bridge the between-rafter insulation at ${(47/c.rSpacing*100).toFixed(1)}% of the area, which is allowed for in the calculation by the combined method. Where the existing rafters are shallower or more closely spaced than stated, the U-value is to be recalculated and the rafters deepened rather than the insulation reduced.`];
  } else {
    const q=UC.quilt.find(x=>x.id===c.quilt);
    t=`Pitched Roof at Ceiling Level — ${c.between}${c.over?" + "+c.over:""}mm mineral wool`;
    tgt=`To achieve a maximum U-value of ${c.limit.toFixed(2)} W/m²K (calculated ${U} W/m²K to BS EN ISO 6946 — see U-value working)`;
    p=[`${Math.min(c.between,c.cjDepth)}mm ${q.n.split(" (")[0]} laid between 47mm x ${c.cjDepth}mm ceiling joists at ${c.cSpacing}mm centres${c.over?`, with a further ${c.over}mm laid cross-wise over the joists`:""}, on 12.5mm plasterboard with skim. Insulation to be continuous over the wall plate and abutting the eaves insulation stops without blocking the ventilation path.`,
       `The roof void is to be ventilated with openings equivalent to a continuous 10mm gap at the eaves on two opposite sides, plus 5mm at the ridge where the pitch exceeds 35° or the span 10m. Proprietary eaves ventilators and insulation stops to be provided. Loft hatches to be insulated and draught sealed; tanks and pipework in the void to be insulated.`];
  }
  return {g:"RF",cat:"__roof__",t,u:U+" W/m²K",tgt,p,
    calc:{params:{...c},result:{U:r.U,U0:r.U0,dUg:r.dUg||0,dUf:r.dUf||0,RT:r.RT,RT_upper:r.RT_upper,RT_lower:r.RT_lower,layers:r.layers.map(l=>({n:l.n,d:l.d,R:l.R})),src:[...new Set(r.src)]}}};
}
function bindConfigurator2(){
  document.querySelectorAll(".cfgcard select[data-cf]").forEach(s=>{
    if(s.dataset.bound) return; s.dataset.bound="1";
    const card=s.closest(".cfgcard"), isF=!!card.querySelector("#addFloor"), isR=!!card.querySelector("#addRoof");
    if(!isF&&!isR) return;
    s.onchange=()=>{ const k=s.dataset.cf; let v=s.value;
      if(!isNaN(parseFloat(v)) && isFinite(v) && !["kind","ground","insulation","slab","finish","edge","fixing","rIns","under","quilt"].includes(k)) v=+v;
      (isF?cfgF():cfgR())[k]=v; if(isF&&k==="kind") cfgF()._userKind=1; renderStage(); save(); };
  });
  const af=el("addFloor"); if(af) af.onclick=()=>{ const c=cfgF(); const r=floorResult(c);
    S.custom=S.custom||[]; S.custom.push(floorSpecText(c,r)); const idx=allBU().length-1; S.sel.push(idx);
    renderStage(); renderSteps(); renderPaper(); save(); toast("Added "+refs()[idx]); };
  const ar=el("addRoof"); if(ar) ar.onclick=()=>{ const c=cfgR(); const r=roofResult(c);
    S.custom=S.custom||[]; S.custom.push(roofSpecText(c,r)); const idx=allBU().length-1; S.sel.push(idx);
    renderStage(); renderSteps(); renderPaper(); save(); toast("Added "+refs()[idx]); };
}
