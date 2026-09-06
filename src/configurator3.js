/* ================= Foundation configurator =================
   Foundations were the only element producing prose and no numbered schedule entry.
   This gives them one, as group FD.

   Nothing here is calculated in the engineering sense: a foundation width comes from
   Approved Document A Table 10 for the load and the subsoil, or from the engineer, and
   this tool does not hold those values. What it does is CHECK a proposed foundation
   against the rules the library already states from Approved Document A Section 2E, and
   show the working, so a dimension that fails is caught at the desk rather than by the
   Building Control Officer.

   Every figure below appears in the library's existing foundation notes and is cited
   there to Approved Document A Section 2E. See reference/FACTS.md. */

const CFGFD_DEFAULT = {
  type:"strip", profile:"level", ground:"clay_firm", trees:"none",
  wall:300, width:600, thickness:225, depth:1000, step:225,
  concrete:"gen1", sulfate:"none"
};
function cfgFD(){ if(!S.cfgFD) S.cfgFD={...CFGFD_DEFAULT}; return S.cfgFD; }
function isFoundationCat(cat){ return /foundation|substructure/i.test(cat||""); }

const FD_TYPES = [
  {id:"strip",  n:"Strip",       calc:true},
  {id:"trench", n:"Trench fill", calc:true},
  {id:"raft",   n:"Raft — engineer's design", calc:false},
  {id:"piled",  n:"Piled — engineer's design", calc:false}
];
/* shrinkable: seasonal moisture movement, so the deeper minimum applies.
   fallback:false means Approved Document A Section 2E does not apply and the
   library sends the job to the engineer instead. */
const FD_GROUND = [
  {id:"clay_firm", n:"Firm clay",         shrinkable:true,  fallback:true},
  {id:"sand",      n:"Sand and gravel",   shrinkable:false, fallback:true},
  {id:"clay_soft", n:"Soft clay",         shrinkable:true,  fallback:false},
  {id:"made",      n:"Made ground / fill",shrinkable:false, fallback:false},
  {id:"rock",      n:"Rock",              shrinkable:false, fallback:true}
];
const FD_CONCRETE = [
  {id:"gen1", n:"GEN1"},
  {id:"rc20", n:"RC20"},
  {id:"eng",  n:"To the engineer's specification"}
];
/* BS 8500 design chemical class. This comes from the ground investigation report,
   never from the soil description, so it is chosen here and never derived. */
const FD_SULFATE = [
  {id:"none", n:"None reported — confirm by ground investigation"},
  {id:"dc1",  n:"DC-1"}, {id:"dc2", n:"DC-2"}, {id:"dc3", n:"DC-3"}, {id:"dc4", n:"DC-4"}
];
const FD_WALLS = [100,140,215,255,300,330,350];
const FD_WIDTHS = [450,500,600,650,700,750,800,850,900,1000];
const FD_THICK = [150,175,200,225,250,300,350,400];
const FD_DEPTHS = [600,750,900,1000,1200,1400,1500,1800,2000,2400];
const FD_STEPS = [150,175,200,225,250,300,350,400];

const fdOf = (list,id) => list.find(x=>x.id===id) || list[0];

/* Returns {calc, ok, summary, checks:[{n,req,got,pass}], notes:[], src:[]} */
function foundationResult(c){
  const type = fdOf(FD_TYPES,c.type), ground = fdOf(FD_GROUND,c.ground);
  const trees = c.trees === "within";
  const notes = [], src = ["Approved Document A Section 2E"];

  if(!type.calc){
    if(trees) src.push("NHBC Chapter 4.2");
    return {calc:false, ok:true, summary:"Engineer's design",
      checks:[], notes:[
        `A ${type.n.split(" —")[0].toLowerCase()} foundation is designed by the structural engineer. No dimension is checked here.`,
        "The ground investigation, the concrete class and the cover to reinforcement still apply and are recorded on the entry."
      ], src};
  }

  const proj = (c.width - c.wall) / 2;
  const minDepth = ground.shrinkable ? 1000 : 750;
  const minWidth = c.type === "trench" ? 450 : 0;
  const checks = [];
  const add = (n,req,got,pass) => checks.push({n,req,got,pass});

  add("Projection each side  (width − wall) ÷ 2", "—", proj.toFixed(0)+" mm", true);
  add("Thickness not less than the projection", proj.toFixed(0)+" mm", c.thickness+" mm", c.thickness >= proj);
  add("Thickness never less than 150 mm", "150 mm", c.thickness+" mm", c.thickness >= 150);
  if(minWidth) add("Trench fill not less than 450 mm wide", "450 mm", c.width+" mm", c.width >= minWidth);
  if(c.width <= c.wall) add("Width greater than the wall thickness", "> "+c.wall+" mm", c.width+" mm", false);

  if(trees){
    add("Depth where trees are within influencing distance",
        "NHBC Chapter 4.2", c.depth+" mm entered", true);
    notes.push("Trees are within influencing distance, so the foundation depth follows NHBC Chapter 4.2 and the engineer's recommendation, with heave precautions where trees have been removed. The depth is not calculated here and the figure entered above is a placeholder until that assessment is done.");
    src.push("NHBC Chapter 4.2");
  } else {
    add(ground.shrinkable ? "Depth not less than 1000 mm in shrinkable clay" : "Depth not less than 750 mm",
        minDepth+" mm", c.depth+" mm", c.depth >= minDepth);
  }

  if(c.profile === "stepped"){
    const overlap = Math.max(2 * c.step, c.thickness, c.type === "trench" ? 1000 : 300);
    add("Step height not to exceed the foundation thickness", c.thickness+" mm", c.step+" mm", c.step <= c.thickness);
    add("Overlap at each step  (greatest of 2 × step, the thickness, and "+(c.type==="trench"?"1 m":"300 mm")+")",
        overlap+" mm", "to be built", true);
    notes.push(`Each step is ${c.step} mm with the higher foundation overlapping the lower by not less than ${overlap} mm, and the masonry below ground stepped to suit.`);
  }

  if(!ground.fallback){
    add("Approved Document A Section 2E applies to this ground", "firm clay, sand, gravel or rock", ground.n, false);
    notes.push(`On ${ground.n.toLowerCase()} the Approved Document A fallback does not apply. A reinforced concrete raft or piled foundation to the structural engineer's design is to be used instead, following a ground investigation.`);
  }

  const ok = checks.every(x => x.pass);
  const summary = c.type === "trench"
    ? `${c.width} wide trench fill, ${c.depth} deep`
    : `${c.width} × ${c.thickness}, ${c.depth} deep`;
  return {calc:true, ok, summary, checks, notes, src, proj, minDepth,
          overlap: c.profile === "stepped" ? Math.max(2*c.step, c.thickness, c.type==="trench"?1000:300) : 0};
}

function fdChecksTable(r){
  if(!r.checks.length) return "";
  return `<table class="wk"><tr><th>Check</th><th>Required</th><th>Proposed</th></tr>`
    + r.checks.map(x=>`<tr><td>${esc(x.n)}${x.pass?"":` <i>— not met</i>`}</td><td>${esc(x.req)}</td><td>${esc(x.got)}</td></tr>`).join("")
    + `</table>`;
}

function renderFoundationConfigurator(){
  const c = cfgFD(), r = foundationResult(c);
  const isCalc = r.calc, stepped = c.profile === "stepped";
  const failed = r.checks.filter(x=>!x.pass).length;

  const body = isCalc ? `
      ${sel("profile",[{v:"level",n:"Level"},{v:"stepped",n:"Stepped — sloping ground"}],c.profile,"Profile")}
      ${sel("wall",FD_WALLS.map(v=>({v,n:v+" mm"})),c.wall,"Wall thickness at the foundation")}
      ${sel("width",FD_WIDTHS.map(v=>({v,n:v+" mm"})),c.width,"Foundation width — from AD A Table 10 for the load and subsoil, or the engineer's design")}
      ${sel("thickness",FD_THICK.map(v=>({v,n:v+" mm"})),c.thickness,"Foundation thickness")}
      ${sel("depth",FD_DEPTHS.map(v=>({v,n:v+" mm"})),c.depth,"Depth below finished ground level")}
      ${stepped?sel("step",FD_STEPS.map(v=>({v,n:v+" mm"})),c.step,"Step height"):""}
      ${sel("concrete",FD_CONCRETE.map(o=>({v:o.id,n:o.n})),c.concrete,"Concrete")}
      ${sel("sulfate",FD_SULFATE.map(o=>({v:o.id,n:o.n})),c.sulfate,"BS 8500 design chemical class")}` : `
      ${sel("concrete",FD_CONCRETE.map(o=>({v:o.id,n:o.n})),c.concrete,"Concrete")}
      ${sel("sulfate",FD_SULFATE.map(o=>({v:o.id,n:o.n})),c.sulfate,"BS 8500 design chemical class")}`;

  return `<div class="card cfgcard"><div class="cfghead"><h3>Set out the foundation</h3>
    <span class="uval ${r.ok?"ok":"bad"}">${r.ok
      ? `<b>${esc(r.summary)}</b>`
      : `<b>Check</b> <small>${failed} rule${failed>1?"s":""} not met</small>`}</span></div>
    <p class="lede" style="margin-bottom:14px">The width comes from Approved Document A Table 10 for the wall load and the subsoil, or from the structural engineer. This does not hold those values and does not choose one for you: it checks the foundation you propose against the rules in Section 2E and shows the working.</p>
    <div class="cfggrid">
      ${sel("type",FD_TYPES.map(o=>({v:o.id,n:o.n})),c.type,"Foundation type")}
      ${sel("ground",FD_GROUND.map(o=>({v:o.id,n:o.n})),c.ground,"Subsoil")}
      ${sel("trees",[{v:"none",n:"No trees within influencing distance"},{v:"within",n:"Trees within influencing distance"}],c.trees,"Trees")}
      ${body}
    </div>
    ${r.notes.length?`<p class="cfgwarn">${r.notes.map(esc).join(" ")}</p>`:""}
    ${isCalc?`<details class="working"><summary>Dimensional checks</summary>${fdChecksTable(r)}</details>`:""}
    <div class="cfgfoot"><span class="srcnote">Sources: ${[...new Set(r.src)].map(esc).join(" · ")}</span>
      <button class="btn btn-primary" id="addFound">Add as FD build-up</button></div></div>`;
}

function fdSpecText(c,r){
  const type = fdOf(FD_TYPES,c.type), ground = fdOf(FD_GROUND,c.ground),
        conc = fdOf(FD_CONCRETE,c.concrete), sul = fdOf(FD_SULFATE,c.sulfate);
  const trees = c.trees === "within";
  const concTxt = conc.id === "eng" ? "concrete to the structural engineer's specification"
                                    : conc.n + " concrete";
  const sulTxt = sul.id === "none"
    ? "The ground investigation is to confirm whether sulfates are present; where they are, the concrete is to the BS 8500 design chemical class the report gives."
    : `Concrete to BS 8500 design chemical class ${sul.n} as the ground investigation requires.`;
  const p = [], notes = [];

  if(!r.calc){
    const kind = c.type === "raft" ? "reinforced concrete raft" : "piled";
    /* no CAPS heading paragraph here: the entry title is already rendered as the heading */
    p.push(`A ${kind} foundation to the structural engineer's design and calculations, submitted to building control before the affected work commences, on ${ground.n.toLowerCase()} confirmed by ground investigation. ${c.type === "raft" ? "Edge beams under all loadbearing walls, reinforcement lapped not less than 450 mm with 40 mm cover, laid on a compressible blinding and a damp proof membrane." : "Pile type, depth, spacing and the ground beam arrangement to the engineer's design, with the piling contractor's records provided to building control."} All ${concTxt} to BS EN 206 and BS 8500.`);
    p.push(sulTxt);
    p.push("All excavations to be inspected and approved by the Building Control Officer before concrete is placed. No service is to be built into or cast through the foundation without the engineer's written approval. To be read with the Foundations note in Part B.");
    notes.push("NOTE — The ground investigation report is to be obtained and issued to the engineer and to building control before the foundation design is finalised.");
  } else {
    const desc = c.type === "trench"
      ? `mass concrete trench fill ${c.width} mm wide`
      : `strip foundation ${c.width} mm wide and ${c.thickness} mm thick`;
    p.push(`${desc.charAt(0).toUpperCase()+desc.slice(1)} in ${concTxt} to BS EN 206 and BS 8500, taken to not less than ${c.depth} mm below finished ground level, beneath a ${c.wall} mm wall, on ${ground.n.toLowerCase()}. The projection beyond each face of the wall is ${r.proj.toFixed(0)} mm and the thickness is not less than that projection and in no case less than 150 mm, in accordance with Approved Document A Section 2E.`);
    if(c.profile === "stepped"){
      p.push(`Where the ground falls the foundation is stepped, each step not exceeding ${c.thickness} mm — the thickness of the foundation — with the higher foundation overlapping the lower by not less than ${r.overlap} mm, and the masonry below ground stepped to suit.`);
    }
    if(trees){
      p.push(`Trees are within influencing distance. The foundation depth is to follow NHBC Chapter 4.2 and the structural engineer's recommendation for the species, the mature height and the distance from the building, with heave precautions — compressible material to the face of the foundation and a void former beneath the ground floor — where trees have been removed or are to be removed. The depth stated above is provisional until that assessment is made.`);
    } else if(ground.shrinkable){
      p.push(`The subsoil is a shrinkable clay, so the foundation is taken to not less than 1000 mm below finished ground level to be clear of seasonal moisture movement. Internal loadbearing walls are founded not less than 600 mm deep.`);
    } else {
      p.push(`The foundation is taken to not less than 750 mm below finished ground level to be clear of frost action, and deeper where required to reach undisturbed bearing strata. Internal loadbearing walls are founded not less than 600 mm deep.`);
    }
    p.push(`${sulTxt} Foundations are to be taken below the invert of any adjacent drain and are not to be undermined by it. All excavations to be inspected and approved by the Building Control Officer before concrete is placed. To be read with the Foundations note in Part B.`);
    notes.push(`NOTE — The ${c.width} mm width is to be confirmed against Approved Document A Table 10 for the wall load and the subsoil, or against the structural engineer's design. This tool does not hold the Table 10 values and has not chosen the width.`);
    if(!ground.fallback){
      notes.push(`NOTE — On ${ground.n.toLowerCase()} the Approved Document A Section 2E fallback does not apply. A raft or piled foundation to the engineer's design is required instead; this entry is not to be issued as drawn.`);
    }
    r.checks.filter(x=>!x.pass).forEach(x=>{
      notes.push(`NOTE — ${x.n}: ${x.got} against a requirement of ${x.req}. This does not comply and is to be corrected before issue.`);
    });
  }

  const title = r.calc
    ? `${type.n} Foundation — ${c.width} × ${c.thickness}${c.profile === "stepped" ? ", Stepped" : ""}`
    : `${type.n.split(" —")[0]} Foundation — Engineer's Design`;

  return {
    g:"FD", cat:"__foundation__", t:title, u:r.summary,
    tgt: r.calc
      ? `To Approved Document A Section 2E, or the structural engineer's design${r.ok ? "" : " — the dimensions below do not yet satisfy Section 2E"}`
      : "To the structural engineer's design and calculations",
    p: p.concat(notes),
    calcFD:{params:{...c}, result:{summary:r.summary, ok:r.ok, checks:r.checks, src:r.src}}
  };
}

function bindConfigurator3(){
  document.querySelectorAll(".cfgcard select[data-cf]").forEach(s=>{
    if(s.dataset.bound3) return;
    const card = s.closest(".cfgcard");
    if(!card.querySelector("#addFound")) return;
    s.dataset.bound3 = "1"; s.dataset.bound = "1";   /* keep configurator2 off this card */
    s.onchange = () => {
      const k = s.dataset.cf; let v = s.value;
      if(["wall","width","thickness","depth","step"].includes(k)) v = +v;
      cfgFD()[k] = v; renderStage(); save();
    };
  });
  const a = el("addFound");
  if(a) a.onclick = () => {
    const c = cfgFD(), r = foundationResult(c);
    S.custom = S.custom || []; S.custom.push(fdSpecText(c,r));
    const idx = allBU().length - 1; S.sel.push(idx);
    renderStage(); renderSteps(); renderPaper(); save();
    toast(r.ok ? "Added " + refs()[idx] : "Added " + refs()[idx] + " — it carries a note, the checks are not met");
  };
}
