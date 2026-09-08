/* ---------------- practice profile ----------------
   WHOSE document this is: the practice USING the tool, and the app hard-codes none.

   It used to be seeded with the vendor's own practice — name, designer, address, and the logo
   itself compiled into src/logos.js. This app is sold to other practices: every subscriber who
   had not yet filled the profile in issued a specification with another company's name and logo
   on the cover, and savePractice() then wrote that logo into their own stored profile. Corrected
   7 September 2026, alongside the same fault in docgen/brand.py. See PRACTICE_BLANK below, the
   guard in build.py, and the commercial rule in CLAUDE.md.

   Where the details come from now, in order:
     the practice on the session, injected by site/app.php from the practices row  (hosted)
     the profile the practice last saved, in localStorage and in db doc practice/profile
     PRACTICE_BLANK — placeholders, so an unfilled cover reads [Practice name]

   A blank cover gets corrected before issue; another firm's name might not. Specline's own mark
   never appears on a document either: Specline is the software, not the designer. */
/* Keys match site/account/index.php exactly. `undecided` is the account's own default and has to
   be an option here too: without it the select fell through to the first entry and showed Solo
   against an account that says "Not decided", so touching the control committed a plan the
   practice had never chosen. seats:0 means no limit has been chosen, not a limit of none. */
const PLANS = {
  undecided:{n:"Not decided", seats:0, price:""},
  solo:     {n:"Solo",     seats:1, price:"£39/month or £390/year"},
  practice: {n:"Practice", seats:5, price:"£89/month or £890/year"},
  payg:     {n:"Per spec", seats:1, price:"£25 per issued specification"}
};
const PRACTICE_BLANK = {name:"", designer:"", addr:"", email:"", phone:"", accent:"",
  logo:"", logoW:0, logoH:0, plan:"undecided", users:[]};
/* What a profile is merged onto. The hosted app replaces it with the account's practice at boot,
   so a field the practice has not set falls back to its own account details and never to a
   compiled-in firm. */
let PRACTICE_BASE = {...PRACTICE_BLANK};
let P = {...PRACTICE_BASE};
const PRACTICE_KEY="specline-practice";
let practiceStored = false;   // did this browser actually hold a saved profile?
function loadPractice(){ try{ const j=JSON.parse(localStorage.getItem(PRACTICE_KEY)||"null");
  if(j&&j.name){ P={...PRACTICE_BASE,...j}; practiceStored=true; } }catch(e){} }
/* The cover has to carry something. Never a firm — a placeholder that asks to be filled in. */
function pName(){ return P.name || "[Practice name]"; }
let practiceTimer=null;
function savePractice(){ try{ localStorage.setItem(PRACTICE_KEY,JSON.stringify(P)); }catch(e){}
  clearTimeout(practiceTimer); practiceTimer=setTimeout(async()=>{ if(!db) return;
    try{ await db.doc("practice/profile").set({...P,updated:Date.now()}); }catch(e){ console.error(e); } },600); }
async function loadPracticeRemote(){ if(!db) return;
  try{ const snap=await db.doc("practice/profile").get();
    if(snap&&snap.exists){ const j=snap.data(); if(j&&j.name){ P={...PRACTICE_BASE,...j};
      try{ localStorage.setItem(PRACTICE_KEY,JSON.stringify(P)); }catch(e){}
      if(S.type) renderPaper(); if(S.route==="practice") renderPractice(); } }
  }catch(e){ console.error(e); } }
/* The document accent is the PRACTICE'S colour, defaulting to the same neutral dark grey the body
   text uses. It was hard-coded to the vendor's own brand orange, on the cover rule, the
   SPECIFICATION heading, every section rule, every build-up reference and every NOTE bar of every
   document the app produced. The ink variant is used where the accent has to be read as text. */
const ACCENT_NEUTRAL = "3E4244";
function accHex(){ const h=(P.accent||"").replace(/[^0-9a-f]/gi,""); return (h.length===6?h:ACCENT_NEUTRAL).toUpperCase(); }
function accRGB(){ const n=parseInt(accHex(),16); return [n>>16&255, n>>8&255, n&255]; }
function mixHex(rgb,f,t){ return rgb.map(v=>Math.round(v+(t-v)*f)).map(v=>v.toString(16).padStart(2,"0")).join("").toUpperCase(); }
function accInk(){ return mixHex(accRGB(), .22, 0); }     // darkened, for accent-coloured text
function accSoft(){ return mixHex(accRGB(), .90, 255); }  // a pale tint, for the notice panel
/* The three tokens .paper declares, pushed onto the element so the practice's colour wins. */
function applyAccent(node){ if(!node) return;
  node.style.setProperty("--pacc", "#"+accHex());
  node.style.setProperty("--pacc-ink", "#"+accInk());
  node.style.setProperty("--psoft", "#"+accSoft()); }

/* The cover notice, in the practice's voice. The software drafts; building control approves. */
function coverNotice(){
  const who = P.designer ? `${P.designer} of ${pName()}` : pName();
  return {
    lead:`To be read with the ${pName()} drawing pack, the structural engineer's design and calculations, and any specialist sub-contractor design. All work to comply with the Building Regulations 2010 (as amended) and the Approved Documents current at the date of issue.`,
    resp:`${who} is the named designer and remains responsible for the suitability of this specification for this project. Every clause and table reference is to be confirmed against the Approved Documents in force at the date of submission. Compliance of the work is determined by the building control body; this document is the designer's specification of the work, not an approval of it.`
  };
}
const GROUPS = {FD:"Foundations", SW:"Separating walls", SF:"Separating floors", EW:"External walls", IW:"Internal walls", GF:"Ground floors", IF:"Floors", RF:"Roofs", BW:"Basement walls", BF:"Basement floors"};
/* FD first: foundations are built first, so they head the schedule. */
const GORDER = ["FD","SW","SF","EW","IW","GF","IF","RF","BW","BF"];

/* every project type in the library */
const TYPES = [
  {k:"extension", code:"EXT", n:"House Extension",     r:"England", ready:true, d:"Single and two storey, rear and side"},
  {k:"loft",      code:"LFT", n:"Loft Conversion",     r:"England", ready:true, d:"Dormer, hip to gable, room in roof"},
  {k:"flat",      code:"FLT", n:"Flat Conversion",     r:"England", ready:true, d:"Material change of use, Part E"},
  {k:"garage",    code:"GAR", n:"Garage Conversion",   r:"England", ready:true, d:"Integral and detached"},
  {k:"newbuild",  code:"NBH", n:"New Build",           r:"England", ready:true, d:"Dwellinghouse, full notional assessment"},
  {k:"nbflats",   code:"NBF", n:"New Build Flats",     r:"England", ready:true, d:"Purpose built, separating construction"},
  {k:"basement",  code:"BSM", n:"Basement Conversion", r:"England", ready:true, d:"Underpinning, tanking, BS 8102"},
  {k:"garagebld", code:"GBD", n:"Garage Build",        r:"England", ready:true, d:"Detached and attached, unheated"}
];

/* job record: key, label, example, wide, hint */
const FIELDS = [
  ["job","Job number","",0,"Practice sequence. Typed, never generated."],
  ["rev","Revision","P01",0,"Moves on each time you issue."],
  ["client","Client","",0,"Prints on the cover page."],
  ["la","Local authority","London Borough of Hounslow",0,"Prints on the cover page."],
  ["project","Project","",1,"One line, as it should read on the cover."],
  ["address","Site address","",1,"Prints on the cover and in the running header."]
];

/* the practice standards, stated the same way on every job (CLAUDE.md) */
const STANDARDS = [
  {item:"Fire doors", value:"FD30S doorset (E 30 Sa, intumescent strips and cold smoke seals) with self-closer.", flag:"Exceeds the AD B minimum of E 20"},
  {item:"Alarms", value:"BS 5839-6 Grade D1 Category LD2, mains powered with integral back-up, interlinked.", flag:"Exceeds the AD B minimum of D2 LD3"},
  {item:"Escape window", value:"Openable area not less than 0.33 m², clear dimensions not less than 450 × 450 mm, bottom of the openable area not more than 1100 mm and not less than 800 mm above floor level unless guarded, openable without a key.", flag:""},
  {item:"Hot water", value:"Cylinder capable of storage at not less than 60 °C. Bath supply limited to 48 °C by a thermostatic mixing valve to BS EN 1111 or BS EN 1287 (Approved Document G3). Never ‘taps limited to 60 °C’.", flag:""},
  {item:"Fixed lighting", value:"75 lumens per circuit-watt for all fixed internal and external fittings, those under 5 circuit-watts excluded. The ‘three quarters of fittings’ rule was withdrawn in AD L 2021.", flag:""},
  {item:"Building control", value:"Lower case in prose. ‘The Building Control Officer’ for the person.", flag:""}
];

let S = {route:"home", type:null, id:null, data:{}, sel:[], notes:{}, step:-1, open:{}, custom:[], cfg:null, cfgF:null, cfgR:null, history:[], created:0, updated:0, ovr:{}, tab:null};
FIELDS.forEach(f=>S.data[f[0]]=f[2]);

const el = id => document.getElementById(id);
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const spec = () => SPECS[S.type];
const cats = () => (spec().cats) || [];
const typeOf = k => TYPES.find(t=>t.k===k);
const buCat = b => {
  if(b.cat==="__wall__")  return cats().find(isWallCat)||cats()[0];
  if(b.cat==="__floor__") return cats().find(isFloorCat)||cats()[0];
  if(b.cat==="__roof__")  return cats().find(isRoofCat)||cats()[0];
  if(b.cat==="__foundation__") return cats().find(isFoundationCat)||cats()[0];
  if(b.cat==="__frame__")      return cats().find(isFrameCat)||cats()[0];
  return b.c; };
const ntCat = n => n.c;
const fmtDate = t => new Date(t).toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"});
const WORDS = ["No","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Eleven","Twelve"];
const word = n => n<WORDS.length ? WORDS[n] : String(n);

function catItems(cat){
  const bus = allBU().map((b,i)=>({b,i})).filter(x=>buCat(x.b)===cat);
  const nts = spec().notes.map((n,i)=>({n,i})).filter(x=>ntCat(x.n)===cat);
  return {bus,nts};
}
function catCount(cat){
  const {bus,nts}=catItems(cat);
  return bus.filter(x=>S.sel.includes(x.i)).length + nts.filter(x=>S.notes[x.i]).length;
}
function catTotal(cat){ const {bus,nts}=catItems(cat); return bus.length+nts.length; }

function defaults(){
  S.sel=[]; S.notes={}; S.step=-1; S.open={}; S.custom=[]; S.cfg=null; S.cfgF=null; S.cfgR=null; S.visited={}; S.ovr={}; S.tab=null;
  if(!S.data.mfr) S.data.mfr="kingspan";
  spec().notes.forEach((n,i)=>S.notes[i]=true);
  applyM4();
  ["FD","SW","SF","EW","GF","RF","IF","BW","BF"].forEach(g=>{ const i=spec().buildups.findIndex(b=>b.g===g); if(i>=0) S.sel.push(i); });
  S.sel.sort((a,b)=>a-b);
}
/* Part M: a new dwelling is M4(1) unless the planning permission imposes M4(2) or M4(3). The
   library carries one note per category, tagged m4, and the job's category decides which is on. */
const M4 = [["1","M4(1) Visitable dwelling"],["2","M4(2) Accessible and adaptable dwelling"],["3","M4(3) Wheelchair user dwelling"]];
function m4Notes(){ return !!S.type && spec().notes.some(n=>n.m4); }
function applyM4(){ if(!m4Notes()) return; if(!S.data.m4) S.data.m4="1"; spec().notes.forEach((n,i)=>{ if(n.m4) S.notes[i]=(n.m4===S.data.m4); }); }
function m4Label(){ if(!m4Notes()) return ""; const m=M4.find(x=>x[0]===S.data.m4); return m?m[1]:M4[0][1]; }
function mfrLabel(){ const m=MFRS.find(x=>x.id===(S.data.mfr||"kingspan"))||MFRS[0]; const o=Object.keys(S.ovr||{}).length; return m.n+(o?` (${o} build-up${o>1?"s":""} overridden)`:""); }

function refs(){
  const c={}, out={};
  S.sel.forEach(i=>{ const b=allBU()[i]; if(!b) return; const g=b.g; c[g]=(c[g]||0)+1; out[i]=g+c[g]; });
  return out;
}
function orderedSel(){
  const r=refs();
  const L=allBU();
  return [...S.sel].filter(i=>L[i]).sort((a,b)=>{
    const ga=GORDER.indexOf(L[a].g), gb=GORDER.indexOf(L[b].g);
    return ga-gb || (+r[a].slice(2))-(+r[b].slice(2));
  });
}
function noteSections(){
  const m=new Map();
  spec().notes.forEach((n,i)=>{ if(!S.notes[i]) return; const c=ntCat(n); if(!m.has(c)) m.set(c,[]); m.get(c).push(n); });
  const ordered=new Map();
  cats().forEach(c=>{ if(m.has(c)) ordered.set(c,m.get(c)); });
  m.forEach((v,k)=>{ if(!ordered.has(k)) ordered.set(k,v); });
  return ordered;
}
const calcsOnJob = () => orderedSel().map(i=>({i,b:allBU()[i]})).filter(x=>x.b.calc);

/* ---------------- the layer bar: a build-up drawn to scale ---------------- */
function swatchFor(name){
  const n=String(name).toLowerCase();
  if(/plasterboard|plaster|skim/.test(n)) return {c:"#EDE6DA"};
  if(/brick/.test(n)) return {c:"#A8705A"};
  if(/render|stone/.test(n)) return {c:"#C7BFB3"};
  if(/aircrete|block/.test(n)) return {c:"#C3C7CB"};
  if(/screed|concrete|slab/.test(n)) return {c:"#A9ADB2"};
  if(/dritherm|rockwool|mineral wool|quilt|batt|earthwool/.test(n)) return {c:"#D9C98F"};
  if(/kooltherm|celotex|sopra|unilin|ecotherm|pir|thermafloor|thermaclass|cavitytherm|xps|eps|insulat|k10|tf70|tr2|k11|board/.test(n)) return {c:"#E4CF8A"};
  if(/timber|joist|rafter|osb|ply|chipboard|deck|batten|floorboard/.test(n)) return {c:"#C9A676"};
  if(/air|cavity|void|gap/.test(n)) return {c:"#F1F0EC",air:true};
  if(/membrane|vapour|dpm|felt|single ply|covering|underlay/.test(n)) return {c:"#6E7378"};
  if(/hardcore|sand|ground|earth|soil|blinding/.test(n)) return {c:"#B9A68F"};
  return {c:"#CFCBC3"};
}
/* layers: [{n,d,R}] — surfaces (no d) are skipped; opts.small for the 16px variant */
function layerBar(layers, opts){
  const o=opts||{};
  const L=(layers||[]).filter(l=>l.d!=null && +l.d>0);
  if(!L.length) return "";
  return `<div class="lbar ${o.small?"sm":""}" role="img" aria-label="${esc(L.map(l=>l.d+" mm "+l.n).join(", "))}">`+
    L.map((l,i)=>{ const s=swatchFor(l.n);
      return `<span class="${s.air?"air":""}" style="flex:${+l.d};background:${s.c};--i:${i}" title="${esc(l.d+" mm "+l.n)}"></span>`; }).join("")+`</div>`;
}
function layerKey(layers){
  const L=(layers||[]).filter(l=>l.d!=null && +l.d>0);
  return `<p class="lkey">${esc(L.map(l=>(/^\d/.test(String(l.n))?"":l.d+" mm ")+String(l.n).toLowerCase()).join("  ·  "))}</p>`;
}

/* ---------------- type chooser ---------------- */
function showChooser(mode){
  /* mode "new": start a job of the chosen type. mode "change": swap the type of the current job. */
  S.chooserMode = mode||"new";
  el("chooserKicker").textContent = mode==="change" ? "Change project type" : "New job · Project type";
  el("chooserTitle").textContent = mode==="change" ? "Change the project type?" : "What are we specifying?";
  el("chooserLede").textContent = mode==="change"
    ? "The job record stays. Build-up and note selections are reset to the new type's defaults."
    : "Each type carries its own categories, build-ups and notes from the library. You can change it later without losing the job record.";
  el("tiles").innerHTML = typeTiles();
  el("chooser").hidden=false;
  el("tiles").querySelectorAll("button:not(:disabled)").forEach(b=>b.onclick=()=>{
    const k=b.dataset.k;
    el("chooser").hidden=true; el("tiles").innerHTML="";
    if(S.chooserMode==="change" && S.type){ S.type=k; defaults(); renderAll(); save(); }
    else newJob(k);
  });
}
function typeTiles(){
  return TYPES.map(t=>{ const v=SPECS[t.k];
    const g={}; (v?v.buildups:[]).forEach(b=>{g[b.g]=(g[b.g]||0)+1});
    const top=Object.entries(g).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([k,n])=>n+" "+k).join(" · ");
    return `<button class="tile ${t.ready?"":"soon"}" data-k="${t.k}" ${t.ready?"":"disabled"}>
      <span class="tk"><b>${t.code}</b><span>${v?esc(top+" · "+v.notes.length+" notes"):"Not yet written"}</span></span>
      <span class="tn">${esc(t.n)}</span>
      <span class="td">${esc(t.d)}</span></button>`; }).join("");
}

/* ---------------- routing ---------------- */
const ROUTES=["home","job","spec","calc","standards","practice"];
function go(route){
  if(["job","spec","calc"].includes(route) && !S.type){ route="home"; }
  S.route=route;
  el("home").hidden = route!=="home";
  if(route!=="home") el("home").innerHTML="";   /* the desk re-renders on return; keeps one set of .tile nodes in the DOM */
  el("app").hidden = route!=="job";
  el("specpage").hidden = route!=="spec";
  el("calcpage").hidden = route!=="calc";
  el("stdpage").hidden = route!=="standards";
  el("practicepage").hidden = route!=="practice";
  el("tabs").querySelectorAll("button").forEach(b=>{
    b.classList.toggle("cur",b.dataset.r===route);
    b.disabled = ["job","spec","calc"].includes(b.dataset.r) && !S.type;
  });
  /* one paper node, re-parented between the workspace viewer and the specification page */
  const paper=el("paper");
  if(route==="spec"){ el("specpaper").appendChild(paper); } else if(paper.parentNode!==el("viewer")) el("viewer").appendChild(paper);
  if(route==="home") renderHome();
  if(route==="job") { renderSteps(); renderStage(); renderPaper(); }
  if(route==="spec") { renderPaper(); renderSpecNav(); }
  if(route==="calc") renderCalcPage();
  if(route==="standards") renderStandards();
  if(route==="practice") renderPractice();
  window.scrollTo(0,0);
  try{ localStorage.setItem("syds-route",route); }catch(e){}
}
el("tabs").querySelectorAll("button").forEach(b=>b.onclick=()=>go(b.dataset.r));
el("brandHome").onclick=()=>go("home");

/* ---------------- home: the desk ---------------- */
function renderHome(){
  const jobs=jobsCache.slice().sort((a,b)=>(b.updated||0)-(a.updated||0));
  const n=jobs.length, issued=jobs.filter(j=>(j.history||[]).length).length;
  const head = n===0 ? `Nothing on the desk yet.` : `${word(n)} ${n===1?"job":"jobs"} in hand. <em>${issued?word(issued)+" issued.":"None issued yet."}</em>`;
  const sub = n===0 ? "Start the first job from a project type below. It is saved as you go, and comes back here to be reopened, revised and issued."
                    : "Open a job to carry on where you left off, or start another from a project type below.";
  /* the card: the newest calculated build-up on the desk, or the library's default cavity wall */
  let card;
  const withCalc=jobs.map(j=>({j,c:(j.custom||[]).find(b=>b.calc)})).find(x=>x.c);
  if(withCalc){ const {j,c}=withCalc, res=c.calc.result;
    const tgt=(c.calc.params&&c.calc.params.limit)||null, pass=tgt?res.U<=tgt+1e-9:true;
    card={kicker:`${esc(c.g)} · ${esc(c.t)} · job ${esc(j.data.job||"—")}`, U:res.U, tgt, pass, layers:res.layers, note:"Calculated on the job shown. Open it to change the layers."};
  } else { const r=UC.wall(CFG_DEFAULT);
    card={kicker:"Library default · full fill cavity wall", U:r.U, tgt:CFG_DEFAULT.limit, pass:r.U<=CFG_DEFAULT.limit+1e-9, layers:r.layers, note:"The default the External Walls configurator opens with. Every job calculates its own."};
  }
  el("home").innerHTML=`
    <section class="desk">
      <div>
        <p class="eyebrow">${esc(P.name || "Your practice")} · Building regulations · England</p>
        <h1>${head}</h1>
        <p class="lede">${esc(sub)}</p>
        <div class="actions"><button class="btn btn-primary btn-lg" id="homeNew">Start a new job</button>
          ${n?`<button class="btn btn-lg" id="homeOpen">Open ${esc(jobs[0].data.job?"job "+jobs[0].data.job:"the latest job")}</button>`:""}</div>
      </div>
      <div class="ucard">
        <div class="uhead"><span class="eyebrow">${card.kicker}</span><span class="chip ${card.pass?"ok":"bad"}">${card.pass?"Within target":"Over target"}</span></div>
        <div class="ubig"><b>${card.U.toFixed(2)}</b><span class="unit">W/m²K${card.tgt?`<small>target ${card.tgt.toFixed(2)}</small>`:""}</span></div>
        ${layerBar(card.layers)}${layerKey(card.layers)}
      </div>
    </section>
    <section class="section">
      <div class="sechead"><h2>Jobs</h2><span class="aside">${n?n+" saved":"none saved"}</span></div>
      <div class="joblist">${n?jobs.map(jobRow).join(""):`<div class="empty"><b>No jobs yet.</b>Start one from a project type below. The job record, the build-ups you choose and the notes you keep are saved as you work.</div>`}</div>
    </section>
    <section class="section">
      <div class="sechead"><h2>Start a new job</h2><span class="aside">Eight project types · England</span></div>
      <div class="tiles" id="hometiles">${typeTiles()}</div>
    </section>
    <div class="regflag"><span class="chip dim">AD L1 / F1 2026</span>
      <p>The 2026 editions of Approved Documents L1 and F1 were published on 24 March 2026 and come into force on 24 March 2027, with transitional relief for new dwellings commenced before 24 March 2028. Every specification carries the flag.</p></div>`;
  el("homeNew").onclick=()=>showChooser("new");
  const ho=el("homeOpen"); if(ho) ho.onclick=()=>openJob(jobs[0].id);
  el("hometiles").querySelectorAll("button:not(:disabled)").forEach(b=>b.onclick=()=>newJob(b.dataset.k));
  el("home").querySelectorAll(".jobrow").forEach(b=>b.onclick=()=>openJob(b.dataset.id));
}
function jobRow(j){
  const t=typeOf(j.type), hist=j.history||[];
  const L=(SPECS[j.type]?SPECS[j.type].buildups:[]).concat(j.custom||[]);
  const c={}, tags=[]; (j.sel||[]).forEach(i=>{ const b=L[i]; if(!b) return; c[b.g]=(c[b.g]||0)+1; if(c[b.g]===1) tags.push(b.g+"1"); });
  const status = hist.length ? {cls:"done",t:`${hist[hist.length-1].rev} issued`} : {cls:"wip",t:`Drafting ${j.data.rev||"P01"}`};
  return `<button class="jobrow" data-id="${esc(j.id)}">
    <span class="jn">${esc(j.data.job||"—")}</span>
    <span><span class="jt">${esc(j.data.address||j.data.project||"Untitled job")}</span><span class="jm">${esc(t?t.n:j.type)}${j.data.client?" · "+esc(j.data.client):""}${j.data.project&&j.data.address?" · "+esc(j.data.project):""}</span></span>
    <span class="jr">${tags.slice(0,4).map(x=>`<span class="chip ref">${x}</span>`).join("")}</span>
    <span class="js ${status.cls}"><b>${esc(status.t)}</b><small>${fmtDate(j.updated||j.created||Date.now())}</small></span></button>`;
}

/* ---------------- workspace: rail ---------------- */
function renderSteps(){
  const N=cats().length;
  el("stepJob").classList.toggle("cur",S.step===-1);
  el("stepJob").classList.toggle("done",S.step!==-1 && !!S.data.job);
  el("stepReview").classList.toggle("cur",S.step==="review");
  el("steps").innerHTML = cats().map((c,i)=>{
    const n=catCount(c), tot=catTotal(c);
    return `<button class="rstep step ${i===S.step?"cur":""} ${S.visited&&S.visited[i]&&i!==S.step?"done":""}" data-i="${i}">
      <span class="sn">${i+1}</span>
      <span class="st">${esc(c)}</span>
      <span class="sc ${n?"has":""}">${n}/${tot}</span></button>`;
  }).join("");
  el("steps").querySelectorAll("button").forEach(b=>b.onclick=()=>setStep(+b.dataset.i));
  el("stepJob").onclick=()=>setStep(-1);
  el("stepReview").onclick=()=>setStep("review");
  el("jobTitle").textContent = S.data.address || S.data.project || (S.data.job?"Job "+S.data.job:"New job");
  el("jobSub").textContent = [S.data.job?"Job "+S.data.job:"", S.data.rev||"P01"].filter(Boolean).join(" · ");
}
function setStep(s){
  if(typeof S.step==="number" && S.step>=0){ S.visited=S.visited||{}; S.visited[S.step]=1; }
  S.step=s; S.tab=null; renderStage(); renderSteps(); save();
}

/* ---------------- workspace: stage ---------------- */
/* A category can carry the library list and one or more calculators. Stacked, that put two
   calculators above twenty cards on the same page, so they are tabs: one view at a time. The
   strip appears only where there is a calculator to open — most categories are the list alone.
   The foundation one CHECKS rather than calculates (Approved Document A Table 10 is not held
   here), so it is named for what it does. */
function stageTabs(cat){
  const t=[];
  if(isWallCat(cat))       t.push({id:"cavity", n:"Cavity wall calculator",  f:()=>renderConfigurator()});
  if(isFrameCat(cat))      t.push({id:"frame",  n:"Framed wall calculator",  f:()=>renderFrameConfigurator(cat)});
  if(isFloorCat(cat))      t.push({id:"floor",  n:isBasementCat(cat)?"Basement calculator":"Ground floor calculator", f:()=>renderFloorConfigurator(cat)});
  if(isRoofCat(cat))       t.push({id:"roof",   n:"Roof calculator",         f:()=>renderRoofConfigurator()});
  if(isFoundationCat(cat)) t.push({id:"fdn",    n:"Foundation check",        f:()=>renderFoundationConfigurator()});
  return t;
}
function renderStage(){
  if(S.step===-1) return renderJobRecord();
  if(S.step==="review") return renderReview();
  const cat = cats()[S.step];
  if(cat===undefined){ S.step=-1; return renderJobRecord(); }
  const {bus,nts} = catItems(cat);
  const r = refs();
  /* the views this category can show: its build-ups, its notes, and any calculator it offers.
     A strip appears only where there is a choice to make — a category holding notes alone is
     still one page of notes. */
  const views = [];
  if(bus.length) views.push({id:"bus", n:"Build-ups", c:`${bus.filter(x=>S.sel.includes(x.i)).length}/${bus.length}`});
  if(nts.length) views.push({id:"nts", n:"Notes",     c:`${nts.filter(x=>S.notes[x.i]).length}/${nts.length}`});
  const calcs = stageTabs(cat);
  const tabs = views.concat(calcs);
  const strip = tabs.length>1;
  const cur = tabs.some(t=>t.id===S.tab) ? S.tab : ((tabs[0]&&tabs[0].id) || "bus");
  const LEDE = {bus:"Tick the build-ups used on this job. They number themselves in the order you tick them.",
                nts:"Every note is on to begin with. Untick what does not apply to this job."};
  let h = `<div class="stagehead${strip?" tabbed":""}">
      <p class="crumb">Step ${S.step+1} of ${cats().length} &nbsp;·&nbsp; ${esc(spec().name)}</p>
      <h2>${esc(cat)}</h2>
      ${strip?"":(LEDE[cur]?`<p class="lede">${LEDE[cur]}</p>`:"")}
    </div>`;
  if(strip){
    /* the switcher first, then the copy for whichever view is open: a calculator speaks for
       itself once open, so only the two lists carry an instruction */
    h += `<div class="stagetabs" role="tablist">`
      + tabs.map(t=>`<button class="stab${cur===t.id?" cur":""}" data-stab="${t.id}" role="tab" aria-selected="${cur===t.id}">${esc(t.n)}${t.c?` <span class="stn">${t.c}</span>`:""}</button>`).join("")
      + `</div>`;
    if(LEDE[cur]) h += `<p class="lede stagelede">${LEDE[cur]}</p>`;
  }
  const openCalc = calcs.find(t=>t.id===cur);
  if(openCalc) h += openCalc.f();
  if(cur==="bus" && bus.length){
    /* with a strip the tab is the label; without one it is the only thing naming the list */
    if(!strip) h += `<p class="grouplabel">Construction build-ups</p>`;
    h += bus.map(({b,i})=>{
      const on=S.sel.includes(i), opened=S.open["b"+i];
      return `<div class="card ${on?"on":""}">
        <label class="cardhead"><input type="checkbox" data-t="b" data-i="${i}" ${on?"checked":""}>
          <span class="tag ${on?"":"off"}">${on?r[i]:"—"}</span>
          <span class="ct">${esc(b.t)}</span>
          ${b.u?`<span class="cu">${esc(b.u)}</span>`:""}
          ${b.calc&&i>=spec().buildups.length?`<button class="rm" data-rm="${i}" title="Remove this calculated build-up">Remove</button>`:""}</label>
        ${b.mf?mfrRow(b,i):""}
        ${b.calc?`<div class="cfgbar">${layerBar(b.calc.result.layers,{small:true})}</div>`:""}
        ${b.tgt?`<p class="tgt">${esc(b.tgt)}</p>`:""}
        <div class="text ${opened?"":"clip"}">${b.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join("")}</div>
        ${b.p.length>1||b.p[0].length>210?`<button class="more" data-o="b${i}">${opened?"Show less":"Read full clause"}</button>`:""}
      </div>`;
    }).join("");
  }
  if(cur==="nts" && nts.length){
    h += nts.map(({n,i})=>{
      const on=!!S.notes[i], opened=S.open["n"+i];
      return `<div class="card ${on?"on":""}">
        <label class="cardhead"><input type="checkbox" data-t="n" data-i="${i}" ${on?"checked":""}>
          <span class="ct">${esc(n.t)}</span></label>
        <div class="text ${opened?"":"clip"}">${n.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join("")}</div>
        ${n.p.length>1||n.p[0].length>210?`<button class="more" data-o="n${i}">${opened?"Show less":"Read full clause"}</button>`:""}
      </div>`;
    }).join("");
  }
  if(!tabs.length) h += `<p class="lede">Nothing in this category for this project type.</p>`;

  const last = S.step===cats().length-1;
  h += `<div class="navbar">
      <button class="btn" id="prev">← Back</button>
      <span class="prog"><span style="width:${((S.step+1)/(cats().length+1)*100).toFixed(1)}%"></span></span>
      ${last?`<button class="btn btn-primary" id="finish">Review and issue →</button>`
            :`<button class="btn btn-primary" id="next">Next →</button>`}
    </div>`;
  el("stage").innerHTML=h;
  el("stage").scrollTop=0;

  el("stage").querySelectorAll('input[type=checkbox]').forEach(inp=>inp.onchange=()=>{
    const i=+inp.dataset.i;
    if(inp.dataset.t==="b"){ if(inp.checked){ if(!S.sel.includes(i)) S.sel.push(i); } else S.sel=S.sel.filter(x=>x!==i); }
    else S.notes[i]=inp.checked;
    renderStage(); renderSteps(); renderPaper(); save();
  });
  bindConfigurator3(); bindConfigurator4(); bindConfigurator(); bindConfigurator2();
  el("stage").querySelectorAll("[data-stab]").forEach(t=>t.onclick=()=>{ S.tab=t.dataset.stab; renderStage(); });
  el("stage").querySelectorAll("select[data-mo]").forEach(s=>s.onchange=()=>{
    const i=+s.dataset.mo; S.ovr=S.ovr||{}; if(s.value) S.ovr[i]=s.value; else delete S.ovr[i];
    renderStage(); renderSteps(); renderPaper(); save();
  });
  el("stage").querySelectorAll(".rm").forEach(b=>b.onclick=(e)=>{
    e.preventDefault(); const i=+b.dataset.rm, base=spec().buildups.length, ci=i-base;
    if(ci<0) return; S.custom.splice(ci,1);
    S.sel=S.sel.filter(x=>x!==i).map(x=>x>i?x-1:x);
    renderStage(); renderSteps(); renderPaper(); save();
  });
  el("stage").querySelectorAll(".more").forEach(b=>b.onclick=()=>{
    S.open[b.dataset.o]=!S.open[b.dataset.o]; renderStage();
  });
  const p=el("prev"), n=el("next"), f=el("finish");
  if(p) p.onclick=()=>setStep(S.step===0?-1:S.step-1);
  if(n) n.onclick=()=>{ if(S.step<cats().length-1) setStep(S.step+1); };
  if(f) f.onclick=()=>setStep("review");
}

function renderJobRecord(){
  const hist=S.history||[];
  el("stage").innerHTML=`<div class="stagehead">
      <p class="crumb">Job record &nbsp;·&nbsp; ${esc(spec().name)}</p>
      <h2>Which job is this?</h2>
      <p class="lede">These fields print on the cover page and in the running header of every issue. The job number follows the practice sequence: type it, the app never invents one.</p>
    </div>
    <div class="card"><div class="fields" id="fields"></div></div>
    <div class="card hist"><p class="grouplabel" style="margin-top:0">Issue history</p>
      ${hist.length?`<table>${hist.slice().reverse().map(h=>`<tr><td>${esc(h.rev)}</td><td>${esc(h.n)} build-ups · ${esc(h.m)} notes</td><td>${fmtDate(h.at)}</td></tr>`).join("")}</table>`
                   :`<p class="none">Nothing issued yet. ${esc(S.data.rev||"P01")} is the working revision; it moves on when you issue from the last step.</p>`}
    </div>
    <div class="navbar"><button class="btn btn-quiet" id="delJob">Delete this job</button><span class="prog"><span style="width:0%"></span></span><button class="btn btn-primary" id="next">Start on the categories →</button></div>`;
  renderFields();
  el("next").onclick=()=>setStep(0);
  el("delJob").onclick=()=>{ if(confirm("Delete this job and its history? This cannot be undone.")) deleteJob(S.id); };
}
function renderFields(){
  const c=el("fields"); if(!c) return;
  let h = FIELDS.map(f=>
    `<label class="${f[3]?"wide":""}">${esc(f[1])}<input data-k="${f[0]}" value="${esc(S.data[f[0]])}" ${f[0]==="job"?'inputmode="numeric"':""}><small>${esc(f[4])}</small></label>`).join("");
  const mfr=S.data.mfr||"kingspan";
  h += `<label class="${m4Notes()?"":"wide"}">Insulation manufacturer<select data-k="mfr">${MFRS.map(m=>`<option value="${m.id}" ${m.id===mfr?"selected":""}>${esc(m.n)}</option>`).join("")}</select><small>Job default. The library is written with Kingspan; another choice re-runs every insulated build-up with that manufacturer's product and states the result. Override on any build-up's card.</small></label>`;
  if(m4Notes()) h += `<label>Part M category<select data-k="m4">${M4.map(m=>`<option value="${m[0]}" ${m[0]===(S.data.m4||"1")?"selected":""}>${esc(m[1])}</option>`).join("")}</select><small>Decides which Access (Part M) note the specification carries. M4(2) and M4(3) apply only where the planning permission requires them.</small></label>`;
  c.innerHTML = h;
  c.querySelectorAll("input").forEach(i=>i.oninput=()=>{ S.data[i.dataset.k]=i.value; renderPaper(); renderSteps(); save(); });
  c.querySelectorAll("select").forEach(s=>s.onchange=()=>{ S.data[s.dataset.k]=s.value; if(s.dataset.k==="m4") applyM4(); renderPaper(); renderSteps(); save(); });
}

/* the manufacturer row on a build-up card: job default, or an override for this build-up */
function mfrRow(b,i){
  const dflt=MFRS.find(m=>m.id===(S.data.mfr||"kingspan"))||MFRS[0], cur=(S.ovr||{})[i]||"";
  const info=b.mfrInfo;
  const chip = info ? `<span class="chip ${info.ok?"ok":"bad"}">${info.ok?"Recalculated "+info.U.toFixed(2):"Does not meet the target at "+info.U.toFixed(2)}</span>`
                    : (b.lib!=null&&mfrFor(i)!=="kingspan" ? `<span class="chip">Kingspan product retained</span>` : "");
  return `<div class="mfrrow"><label>Insulation <select data-mo="${i}"><option value="">Job default — ${esc(dflt.short)}</option>${MFRS.map(m=>`<option value="${m.id}" ${m.id===cur?"selected":""}>${esc(m.short)}</option>`).join("")}</select></label>${chip}</div>`;
}

function renderReview(){
  const sel=orderedSel(), r=refs(), ns=noteSections(), calcs=calcsOnJob();
  let notes=0; ns.forEach(v=>notes+=v.length);
  const missing=FIELDS.filter(f=>!S.data[f[0]]).map(f=>f[1]);
  /* the job in summary, and the schedule checked build-up by build-up. On a full new build that
     was 23 rows under the buttons, so they are two views — but the actions stay above the strip:
     the point of this step is to issue, and an Issue button behind a tab is a hidden control. */
  const sumRows=[
    ["Job", `${esc(S.data.job||"—")} · ${esc(S.data.rev||"P01")} · ${esc(S.data.address||"no site address")}`, missing.length?["bad",`${missing.length} of ${FIELDS.length} fields not set`]:["ok","Cover page complete"]],
    ["Type", `${esc(spec().name)} · ${esc(spec().region)}`, ["ok","Set"]],
    ["Insulation", esc(mfrLabel()), ["dim", (S.data.mfr||"kingspan")==="kingspan"?"Library products":"Substituted and recalculated"]],
    ...(m4Notes()?[["Access", esc(m4Label()), ["dim","Approved Document M Volume 1"]]]:[]),
    ["Build-ups", sel.length?`${sel.length} in the schedule`:"None selected", [sel.length?"ok":"bad", sel.length?"Part A ready":"Part A empty"]],
    ["Notes", `${notes} notes in ${ns.size} of ${cats().length} categories`, [notes?"ok":"bad", notes?"Part B ready":"No notes selected"]],
    ["Working", calcs.length?`${calcs.length} calculated build-up${calcs.length>1?"s":""} carried into section 4.0`:"No calculated build-ups on this job", ["dim", calcs.length?"BS EN ISO 6946 / 13370":"Optional"]],
    ["Regulatory flag", "AD L1 / F1 2026 editions in force 24 March 2027", ["dim","Carried on the last page"]]
  ];
  const buRows=sel.map(i=>{ const b=allBU()[i]; let f=["dim",b.u||"Library build-up"];
      if(b.calc){ const lim=b.calc.params&&b.calc.params.limit; const pass=lim?b.calc.result.U<=lim+1e-9:true; f=[pass?"ok":"bad",`${b.calc.result.U.toFixed(2)} against ${lim?lim.toFixed(2):"—"}`]; }
      return [r[i], esc(b.t), f]; });
  const toFix=sumRows.filter(x=>x[2][0]==="bad").length, over=buRows.filter(x=>x[2][0]==="bad").length;
  /* a check that fails must say so ON the tab, or a tab becomes somewhere for a failure to hide */
  const tabs=[{id:"sum", n:"Summary",   c:toFix?`${toFix} to fix`:"", bad:!!toFix},
              {id:"bus", n:"Build-ups", c:over?`${over} over target`:String(buRows.length), bad:!!over}];
  const strip=buRows.length>0;
  const cur=(strip && tabs.some(t=>t.id===S.tab)) ? S.tab : "sum";
  const rows=cur==="bus"?buRows:sumRows;
  el("stage").innerHTML=`<div class="stagehead">
      <p class="crumb">Review and issue &nbsp;·&nbsp; ${esc(spec().name)}</p>
      <h2>Ready to issue ${esc(S.data.rev||"P01")}?</h2>
      <p class="lede">Check the summary, then download the PDF. Issuing records this revision in the job's history and moves the working revision on.</p>
    </div>
    <div class="notice"><p class="eyebrow">Before you issue</p><p>${esc(coverNotice().resp)}</p>
      <p class="srcnote">This prints on the cover, with the practice and designer from <a href="#" id="toPractice">Practice settings</a>.</p></div>
    <div class="review">
      <div class="xcard"><span class="eyebrow">Download</span><b>${esc(S.data.rev||"P01")}, unrecorded</b><p>The branded specification with the U-value working as its own section. Word is editable; the PDF is what you send. Nothing is recorded against the job.</p><div class="xrow"><button class="btn" id="finish">PDF</button><button class="btn" id="finishDocx">Word</button></div></div>
      <div class="xcard"><span class="eyebrow">Issue</span><b>Issue ${esc(S.data.rev||"P01")}</b><p>Downloads the PDF, records the issue against this job and sets the working revision to ${esc(nextRev(S.data.rev))}.</p><button class="btn btn-accent" id="issue">Issue ${esc(S.data.rev||"P01")}</button></div>
      <div class="xcard"><span class="eyebrow">Read</span><b>Specification</b><p>Read the whole document as it will print before you send it.</p><button class="btn" id="readSpec">Open specification</button></div>
    </div>
    ${strip?`<div class="stagetabs" role="tablist">`+tabs.map(t=>
      `<button class="stab${cur===t.id?" cur":""}" data-stab="${t.id}" role="tab" aria-selected="${cur===t.id}">${esc(t.n)}${t.c?` <span class="stn${t.bad?" bad":""}">${esc(t.c)}</span>`:""}</button>`).join("")+`</div>`:""}
    <div class="rows">${rows.map(([l,v,f])=>`<div class="row"><span class="rl">${esc(l)}</span><span class="rv">${v}</span><span class="rf ${f[0]}">${esc(f[1])}</span></div>`).join("")}</div>
    <div class="navbar"><button class="btn" id="prev">← Back</button><span class="prog"><span style="width:100%"></span></span></div>`;
  el("stage").querySelectorAll("[data-stab]").forEach(t=>t.onclick=()=>{ S.tab=t.dataset.stab; renderReview(); });
  el("finish").onclick=makePdf;
  el("finishDocx").onclick=makeDocx;
  el("issue").onclick=issue;
  el("readSpec").onclick=()=>go("spec");
  el("toPractice").onclick=e=>{ e.preventDefault(); go("practice"); };
  el("prev").onclick=()=>setStep(cats().length-1);
}
function nextRev(rev){ const m=/^([A-Za-z]*)(\d+)$/.exec(rev||"P01"); if(!m) return "P02";
  return m[1]+String(+m[2]+1).padStart(m[2].length,"0"); }
async function issue(){
  const ok=await makePdf();
  if(!ok) return;
  let n=0, ns=noteSections(); ns.forEach(v=>n+=v.length);
  S.history=S.history||[]; S.history.push({rev:S.data.rev||"P01", at:Date.now(), n:orderedSel().length, m:n});
  const was=S.data.rev||"P01"; S.data.rev=nextRev(was);
  save(); renderStage(); renderSteps(); renderPaper();
  toast(`Issued ${was}. Working revision is now ${S.data.rev}.`);
}

/* ---------------- preview ---------------- */
function renderPaper(){
  if(!S.type) return;
  const r=refs(), sel=orderedSel(), d=S.data;
  const today=new Date().toLocaleDateString("en-GB",{day:"numeric",month:"long",year:"numeric"});
  const nt=coverNotice();
  /* Logo if the practice has uploaded one, otherwise its own name as a wordmark. Never a
     compiled-in mark: that would be another practice's logo on this practice's cover. */
  const w = pName().split(" ");
  const mark = P.logo ? `<img class="plogo" src="${P.logo}" alt="${esc(pName())}">`
                      : `<p class="pmark">${esc(w[0])}${w.length>1?`<span> ${esc(w.slice(1).join(" "))}</span>`:""}</p>`;
  let h=`${mark}
    <p class="paddr">${esc(P.addr)}${P.email?" &nbsp;·&nbsp; "+esc(P.email):""}${P.phone?" &nbsp;·&nbsp; "+esc(P.phone):""}</p>
    <h1 class="ptitle">BUILDING REGULATIONS<span class="o">SPECIFICATION</span></h1>
    <p class="psub">${esc(spec().name)} — ${esc(spec().region)}</p>
    <table class="meta">
      <tr><td>Project</td><td>${esc(d.project||"—")}</td></tr>
      <tr><td>Site address</td><td>${esc(d.address||"—")}</td></tr>
      <tr><td>Client</td><td>${esc(d.client||"—")}</td></tr>
      <tr><td>Job number</td><td>${esc(d.job||"—")}</td></tr>
      <tr><td>Local authority</td><td>${esc(d.la||"—")}</td></tr>
      ${m4Label()?`<tr><td>Access category</td><td>${esc(m4Label())}</td></tr>`:""}
      <tr><td>Prepared by</td><td>${esc(P.designer?P.designer+", ":"")}${esc(pName())}</td></tr>
      <tr><td>Date</td><td>${today}</td></tr>
      <tr><td>Revision</td><td>${esc(d.rev||"P01")}</td></tr>
    </table>
    <div class="flag"><b>ISSUED FOR BUILDING CONTROL APPROVAL.</b> ${esc(nt.lead)}<p class="fl2">${esc(nt.resp)}</p></div>
    <div class="sec" id="s-sched"><i>1.0</i>Construction build-up schedule</div>`;
  if(!sel.length) h+=`<p class="empty">No build-ups selected yet.</p>`;
  else {
    h+=`<table class="sched"><tr><th>Ref</th><th>Build-up</th><th>Standard</th></tr>`+
      sel.map(i=>{const b=allBU()[i];
        return `<tr><td class="r">${r[i]}</td><td>${esc(b.t)}</td><td class="u">${esc(b.u||"—")}</td></tr>`;}).join("")+`</table>`;
    h+=`<div class="sec" id="s-parta"><i>2.0</i>Part A — Construction build-ups</div>`;
    let lg=null;
    sel.forEach(i=>{const b=allBU()[i];
      if(b.g!==lg){lg=b.g; h+=`<p class="glab cat" id="g-${b.g}">${esc(GROUPS[b.g]||b.g)}</p>`;}
      h+=`<div class="eh"><span class="tag2">${r[i]}</span><h4>${esc(b.t)}</h4></div>`;
      if(b.tgt) h+=`<p class="tl">${esc(b.tgt)}</p>`;
      h+=b.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join("");
    });
  }
  const ns=noteSections();
  if(ns.size){
    h+=`<div class="sec" id="s-partb"><i>3.0</i>Part B — General specification notes</div>`;
    let k=0;
    ns.forEach((items,s)=>{ h+=`<p class="glab" id="n-${k++}">${esc(s)}</p>`;
      items.forEach(it=>{ h+=`<div class="eh"><h4>${esc(it.t)}</h4></div>`+it.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join(""); });
    });
  }
  const calcs=calcsOnJob();
  if(calcs.length){
    h+=`<div class="sec" id="s-working"><i>4.0</i>U-value calculations</div>
        <p style="color:var(--pmuted)">Calculated to BS EN ISO 6946 using the combined method for mortar-bridged blockwork and the Annex F corrections for air gaps and wall ties. Indicative — the manufacturer's certified calculation is to be obtained before submission.</p>`;
    calcs.forEach(({i,b})=>{ h+=`<div class="eh"><span class="tag2">${r[i]}</span><h4>${esc(b.t)}</h4></div>`+(b.calc.result.steps?layersOnly(b.calc.result)+stepsTable(b.calc.result):workingTable(b.calc.result))+
      `<p style="font-size:9.5px;color:var(--pmuted)">Sources: ${b.calc.result.src.map(esc).join(" · ")}</p>`; });
  }
  h+=`<div class="flag" style="margin-top:26px"><b>VERIFY BEFORE ISSUE.</b> Approved Documents L1 and F1, 2026
    editions, come into force on 24 March 2027; work with a full plans application submitted before that date
    remains under the current standards provided work commences before 24 March 2028. Confirm all clause and
    table references against the edition in force at the date of submission.</div>`;
  el("paper").innerHTML=h;
  applyAccent(el("paper"));
}
function renderSpecNav(){
  const sel=orderedSel(), ns=noteSections();
  const groups=[]; sel.forEach(i=>{ const g=allBU()[i].g; if(!groups.includes(g)) groups.push(g); });
  el("specTitle").textContent = `${spec().name} — ${S.data.rev||"P01"}`;
  let h=`<p class="raillabel">Contents</p><a href="#s-sched">1.0 Schedule</a><a href="#s-parta">2.0 Part A</a>`;
  h+=groups.map(g=>`<a href="#g-${g}" style="padding-left:22px">${esc(GROUPS[g]||g)}</a>`).join("");
  h+=`<a href="#s-partb">3.0 Part B</a>`;
  let k=0; ns.forEach((v,s)=>{ h+=`<a href="#n-${k++}" style="padding-left:22px">${esc(s)}</a>`; });
  if(calcsOnJob().length) h+=`<a href="#s-working">4.0 U-value working</a>`;
  el("specnav").innerHTML=h;
  el("specnav").querySelectorAll("a").forEach(a=>a.onclick=e=>{ e.preventDefault(); const t=document.querySelector(a.getAttribute("href")); if(t) t.scrollIntoView({behavior:"smooth",block:"start"}); });
}

/* ---------------- U-value working page ---------------- */
function renderCalcPage(){
  const calcs=calcsOnJob(), r=refs();
  let h=`<div class="pagehead"><div><p class="eyebrow">U-value working · carried into the PDF</p>
    <h1>${calcs.length?`${calcs.length} calculated build-up${calcs.length>1?"s":""} on job ${esc(S.data.job||"—")}`:"No calculated build-ups yet"}</h1>
    <p class="lede">Calculated to BS EN ISO 6946 by the combined method with the Annex F corrections for air gaps and wall ties, and to BS EN ISO 13370 for ground floors and heated basements. Conductivities verified against manufacturer and BBA data on 5 September 2026.</p></div>
    ${calcs.length?"":`<button class="btn btn-primary btn-lg" id="calcGo">Open the workspace</button>`}</div>`;
  if(!calcs.length) h+=`<div class="empty"><b>Build one from the workspace.</b>The External Walls, Ground Floors and Roofs categories each carry a configurator. Add a build-up there and its working appears here and in section 4.0 of the PDF.</div>`;
  h+=`<div class="calcs">`+calcs.map(({i,b})=>{ const res=b.calc.result, lim=b.calc.params&&b.calc.params.limit, pass=lim?res.U<=lim+1e-9:true;
    return `<div class="ccard"><div class="chead"><div><span class="chip ref">${r[i]}</span><h3 style="margin-top:8px">${esc(b.t)}</h3></div>
      <div class="cu"><b>${res.U.toFixed(2)}</b><span class="muted">W/m²K${lim?` · target ${lim.toFixed(2)}`:""}</span><span class="chip ${pass?"ok":"bad"}">${pass?"Within target":"Over target"}</span></div></div>
      ${layerBar(res.layers)}${layerKey(res.layers)}
      ${res.steps?layersOnly(res)+stepsTable(res):workingTable(res)}
      <p class="srcs">Sources: ${res.src.map(esc).join(" · ")}</p></div>`; }).join("")+`</div>`;
  el("calcpage").innerHTML=h;
  const g=el("calcGo"); if(g) g.onclick=()=>go("job");
}

/* ---------------- practice standards ---------------- */
function renderStandards(){
  el("stdpage").innerHTML=`<div class="pagehead"><div><p class="eyebrow">Practice standards</p><h1>Stated the same way on every job</h1>
    <p class="lede">Where the practice standard exceeds the Approved Document minimum, the specification says so explicitly. The library is written to these; check a new note against them before adding it.</p></div></div>
    <div class="stdtable">${STANDARDS.map(s=>`<div class="stdrow"><span class="si">${esc(s.item)}</span><span class="sv">${esc(s.value)}${s.flag?`<br><span class="chip ok">${esc(s.flag)}</span>`:""}</span></div>`).join("")}</div>
    <div class="section"><div class="sechead"><h2>Regulatory horizon</h2></div>
    <p class="lede" style="max-width:72ch">Approved Documents L1 and F1, 2026 editions, were published on 24 March 2026 and come into force on 24 March 2027, with transitional relief for new dwellings commenced before 24 March 2028. Every specification carries the flag. The Part L and Part F content will need a full pass against the new editions during 2027.</p></div>`;
}

function renderPractice(){
  const plan=PLANS[P.plan]||PLANS.undecided, used=(P.users||[]).filter(Boolean).length;
  /* No plan chosen means no seat limit to count against — say the number, do not invent a limit. */
  const seatLine=(u,pl)=> pl.seats
    ? `<b>${u} of ${pl.seats}</b> seat${pl.seats>1?"s":""} in use${u>pl.seats?`. Over the ${esc(pl.n)} limit; nothing is enforced yet.`:"."}`
    : `<b>${u}</b> user${u===1?"":"s"} listed. The plan sets the seat limit; none chosen yet.`;
  el("practicepage").innerHTML=`<div class="pagehead"><div><p class="eyebrow">Practice settings</p><h1>${esc(P.name||"Your practice")}</h1>
      <p class="lede">Everything here prints on the specification: the logo and address on the cover, the name in the running footer, the named designer in the responsibility statement. Specline's own mark never appears on a document.</p></div></div>
    <div class="pgrid">
      <div class="card"><p class="grouplabel" style="margin-top:0">Identity on the document</p>
        <div class="fields">
          <label>Practice name<input data-p="name" value="${esc(P.name)}"><small>Cover page and footer.</small></label>
          <label>Named designer<input data-p="designer" value="${esc(P.designer||"")}"><small>Prepared by, and the responsibility statement.</small></label>
          <label class="wide">Address<input data-p="addr" value="${esc(P.addr)}"><small>Under the logo on the cover.</small></label>
          <label>Email<input data-p="email" value="${esc(P.email||"")}"><small>Cover and footer.</small></label>
          <label>Phone<input data-p="phone" value="${esc(P.phone||"")}"><small>Cover, if given.</small></label>
          <label>Document accent<input type="color" data-p="accent" value="#${accHex()}"><small>Rules, section headings and build-up references. Neutral dark grey until you set one.</small></label>
        </div></div>
      <div class="card"><p class="grouplabel" style="margin-top:0">Logo</p>
        <div class="logobox">${P.logo?`<img src="${P.logo}" alt="${esc(pName())} logo">`
          :`<p class="pmark" style="--pacc:#${accInk()}">${esc(pName())}</p>`}</div>
        <div class="cfgfoot"><span class="srcnote">${P.logo?"PNG or JPEG up to 3 MB. Fitted to the cover at its own proportions."
          :"No logo yet — the cover sets your practice name as a wordmark. PNG or JPEG up to 3 MB."}</span>
          <label class="btn">${P.logo?"Replace logo":"Add logo"}<input type="file" id="logoFile" accept="image/png,image/jpeg" hidden></label></div>
        ${P.logo?`<p style="margin:12px 0 0"><button class="btn btn-quiet" id="logoClear">Remove logo</button></p>`:""}</div>
      <div class="card"><p class="grouplabel" style="margin-top:0">Plan and seats</p>
        <div class="fields"><label class="wide">Plan<select data-p="plan">${Object.entries(PLANS).map(([k,v])=>`<option value="${k}" ${P.plan===k?"selected":""}>${esc(v.n)}${v.price?" — "+esc(v.price):""}</option>`).join("")}</select><small>Billing is not connected yet. The plan sets the seat limit shown below.</small></label></div>
        <p class="seats">${seatLine(used,plan)}</p>
        <label class="cf">Users, one per line<textarea data-p="users" rows="4">${esc((P.users||[]).join("\n"))}</textarea></label>
        <p class="srcnote" style="margin-top:10px">Every plan carries the practice's own identity on its own documents. Seats and added clauses are what a plan gates.</p></div>
    </div>
    <div class="navbar"><span class="srcnote">Changes save as you type.</span><span class="spacer"></span><button class="btn btn-primary" id="practiceDone">Back to jobs</button></div>`;
  el("practicepage").querySelectorAll("[data-p]").forEach(inp=>{
    const h=()=>{ const k=inp.dataset.p; P[k]= k==="users" ? inp.value.split("\n").map(x=>x.trim()).filter(Boolean) : inp.value;
      savePractice(); if(S.type) renderPaper();
      if(k==="users"||k==="plan") el("practicepage").querySelector(".seats").innerHTML=seatLine((P.users||[]).length, PLANS[P.plan]||PLANS.undecided);
      if(k==="accent"){ const pm=el("practicepage").querySelector(".logobox .pmark"); if(pm) pm.style.setProperty("--pacc","#"+accInk()); } };
    inp.oninput=h; inp.onchange=h;
  });
  el("logoFile").onchange=e=>readLogo(e.target.files[0]);
  const lc=el("logoClear"); if(lc) lc.onclick=()=>{ P.logo=""; P.logoW=0; P.logoH=0; savePractice(); renderPractice(); if(S.type) renderPaper(); };
  el("practiceDone").onclick=()=>go("home");
}
function readLogo(file){
  if(!file) return;
  if(file.size>3*1024*1024){ toast("That file is over 3 MB. Export a smaller PNG or JPEG."); return; }
  const rd=new FileReader();
  rd.onload=()=>{ const img=new Image();
    img.onload=()=>{
      const max=800, sc=Math.min(1,max/Math.max(img.width,img.height));
      const c=document.createElement("canvas"); c.width=Math.max(1,Math.round(img.width*sc)); c.height=Math.max(1,Math.round(img.height*sc));
      const ctx=c.getContext("2d"), jpeg=/jpe?g$/i.test(file.type);
      if(jpeg){ ctx.fillStyle="#fff"; ctx.fillRect(0,0,c.width,c.height); }
      ctx.drawImage(img,0,0,c.width,c.height);
      P.logo=jpeg?c.toDataURL("image/jpeg",.9):c.toDataURL("image/png"); P.logoW=c.width; P.logoH=c.height;
      savePractice(); renderPractice(); if(S.type) renderPaper(); toast("Logo updated");
    };
    img.onerror=()=>toast("Could not read that image");
    img.src=rd.result; };
  rd.readAsDataURL(file);
}

function renderAll(){
  if(!S.type){ go("home"); return; }
  el("typename").textContent = spec().name;
  go(S.route==="home"?"job":S.route);
}

/* ---------------- PDF ---------------- */
/* jsPDF standard fonts use WinAnsi. Anything outside it prints as rubbish, so map the
   likely offenders to safe equivalents and drop anything still unrepresentable. */
const SAFE_MAP={"≤":"<=","≥":">=","Ψ":"psi","ψ":"psi","±":"+/-","×":"x",
  "÷":"/","→":"->","≈":"~","≠":"!=","−":"-","–":"-","‒":"-",
  "½":"1/2","¼":"1/4","¾":"3/4","Ø":"dia.","⌀":"dia.","∅":"dia.",
  "•":"-"," ":" ","λ":"lambda ","π":"pi","Δ":"delta","₀":"0","·":"."};
const SAFE_KEEP=/[‘’“”—…€™ŒœŠšŽžŸƒˆ˜†‡‰‹›‚„]/;
function safe(t){
  return String(t==null?"":t)
    .replace(/[≤≥Ψψ±×÷→≈≠−–‒½¼¾Ø⌀∅• λπΔ₀]/g, c=>SAFE_MAP[c])
    .split("").filter(c=>{ const n=c.charCodeAt(0);
      return n<0x100 || SAFE_KEEP.test(c); }).join("");
}

function buildPdf(){
  const {jsPDF}=window.jspdf;
  const doc=new jsPDF({unit:"mm",format:"a4"});
  const L=22,R=18,W=210-L-R,BOT=280;
  const d=S.data,r=refs(),sel=orderedSel();
  const today=new Date().toLocaleDateString("en-GB",{day:"numeric",month:"long",year:"numeric"});
  /* ACC is the practice's accent, not a fixed brand colour. See accHex(). */
  const ACC=accRGB(),DARK=[34,38,42],MUTED=[113,118,122],RULE=[220,216,210];
  let y=0,page=1;
  const foot=()=>{ doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.line(L,286,210-R,286);
    doc.setFont("helvetica","normal");doc.setFontSize(7.5);doc.setTextColor(...MUTED);
    doc.text(safe(pName()+(P.email?"  ·  "+P.email:"")),L,290);
    doc.text("Page "+page,210-R,290,{align:"right"}); };
  const head=()=>{ doc.setFont("helvetica","normal");doc.setFontSize(7.5);doc.setTextColor(...MUTED);
    const left=safe(spec().name+" — Building Regulations Specification"+(d.address?"  ·  "+d.address:""));
    doc.text(doc.splitTextToSize(left,W-40)[0],L,13);
    doc.text(safe((d.job?"Job "+d.job:"")+"  |  Rev "+(d.rev||"P01")),210-R,13,{align:"right"});
    doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.line(L,15.5,210-R,15.5); };
  const newPage=()=>{ foot();doc.addPage();page++;head();y=24; };
  const need=h=>{ if(y+h>BOT) newPage(); };
  const para=(t,size=9,gap=2.4,color=DARK,style="normal")=>{
    doc.setFont("helvetica",style);doc.setFontSize(size);doc.setTextColor(...color);
    doc.splitTextToSize(safe(t),W).forEach(ln=>{ need(5);doc.text(ln,L,y);y+=size*0.42+1.1; }); y+=gap; };

  /* The practice's logo, fitted to a 34 x 30 mm box at its own proportions. No logo: its own
     name as a wordmark, never a compiled-in mark. */
  if(P.logo){
    try{ const fmt=/^data:image\/png/i.test(P.logo)?"PNG":"JPEG"; const bw=34,bh=30; let w=bw,hh=bh;
      if(P.logoW&&P.logoH){ const ar=P.logoW/P.logoH; if(ar>=bw/bh){ w=bw; hh=bw/ar; } else { hh=bh; w=bh*ar; } }
      doc.addImage(P.logo,fmt,L,20,w,hh); }catch(e){ console.error(e); }
  } else {
    const wd=pName().split(" ");
    doc.setFont("helvetica","bold");doc.setFontSize(22);doc.setTextColor(...DARK);
    doc.text(safe(wd[0]),L,45);
    if(wd.length>1){ const adv=doc.getTextWidth(safe(wd[0])+" ");
      doc.setFontSize(13);doc.setTextColor(...ACC);
      doc.text(safe(wd.slice(1).join(" ").toUpperCase()),L+adv,45); }
  }
  doc.setFont("helvetica","normal");doc.setFontSize(8);doc.setTextColor(...MUTED);
  doc.text(safe(P.addr+(P.email?"  ·  "+P.email:"")+(P.phone?"  ·  "+P.phone:"")),L,58.5);
  doc.setDrawColor(...ACC);doc.setLineWidth(1.1);doc.line(L,61.5,210-R,61.5);
  doc.setFont("helvetica","bold");doc.setFontSize(28);doc.setTextColor(...DARK);
  doc.text("BUILDING REGULATIONS",L,78);
  doc.setTextColor(...ACC);doc.text("SPECIFICATION",L,90);
  doc.setFontSize(11);doc.setTextColor(...MUTED);
  doc.text(safe((spec().name+" — "+spec().region).toUpperCase()),L,100);
  const rows=[["Project",d.project],["Site address",d.address],["Client",d.client],["Job number",d.job],
    ["Local authority",d.la],...(m4Label()?[["Access category",m4Label()]]:[]),["Application","Full Plans Application"],
    ["Prepared by",(P.designer?P.designer+", ":"")+pName()],["Date",today],["Revision",d.rev||"P01"]];
  y=114;
  rows.forEach(([k,v])=>{
    doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.setFillColor(251,250,248);
    doc.rect(L,y-5,42,7.6,"FD");doc.rect(L+42,y-5,W-42,7.6,"D");
    doc.setFont("helvetica","bold");doc.setFontSize(8);doc.setTextColor(...DARK);doc.text(safe(k),L+2.5,y);
    doc.setFont("helvetica","normal");doc.setFontSize(8.5);
    doc.text(doc.splitTextToSize(safe(v||"—"),W-46)[0],L+44.5,y); y+=7.6; });
  y+=10;
  doc.setDrawColor(...ACC);doc.setLineWidth(.8);doc.line(L,y,L+3,y);
  doc.setFont("helvetica","bold");doc.setFontSize(9);doc.setTextColor(...ACC);
  doc.text("ISSUED FOR BUILDING CONTROL APPROVAL",L+6,y+1); y+=7;
  { const nt=coverNotice(); para(nt.lead,8,1.6,MUTED); para(nt.resp,8,2,MUTED); }
  const hist=S.history||[];
  if(hist.length){ y+=6;
    doc.setFont("helvetica","bold");doc.setFontSize(8);doc.setTextColor(...MUTED);doc.text("ISSUE HISTORY",L,y);y+=5;
    hist.forEach(hh=>{ doc.setFont("helvetica","normal");doc.setFontSize(8);doc.setTextColor(...DARK);
      doc.text(safe(hh.rev),L,y); doc.text(safe("Issued "+fmtDate(hh.at)),L+16,y); y+=4.6; }); }
  foot();doc.addPage();page++;head();y=24;

  const secHead=(num,txt)=>{ need(16);y+=4;
    doc.setFont("helvetica","bold");doc.setFontSize(13);doc.setTextColor(...ACC);doc.text(num,L,y);
    doc.setTextColor(...DARK);doc.text(safe(txt.toUpperCase()),L+13,y);
    y+=2.5;doc.setDrawColor(...ACC);doc.setLineWidth(.7);doc.line(L,y,210-R,y);y+=6; };
  /* The bullet is DRAWN, not written: safe() maps the character to a hyphen because jsPDF's
     WinAnsi fonts cannot be relied on for it. Part A's category headings carry it, matching the
     practice documents; Part B's headings are numbered there and here, so they do not. */
  const grpLabel=(t,cat)=>{ need(10);y+=3;doc.setFont("helvetica","bold");doc.setFontSize(8);
    if(cat){ doc.setFillColor(...ACC); doc.circle(L+1.1,y-1.1,1.05,"F"); }
    doc.setTextColor(...MUTED);doc.text(safe(t.toUpperCase()),cat?L+5:L,y);y+=5; };
  const entry=(tag,title)=>{ need(13);y+=3.5;
    doc.setFont("helvetica","bold");doc.setFontSize(9.5);
    if(tag){doc.setTextColor(...ACC);doc.text(tag,L,y);}
    doc.setTextColor(...DARK);doc.text(safe(title.toUpperCase()),L+(tag?14:0),y);
    y+=1.8;doc.setDrawColor(...RULE);doc.setLineWidth(.15);doc.line(L,y,210-R,y);y+=4.6; };

  secHead("1.0","Construction build-up schedule");
  if(sel.length){
    const cw=[18,112,40];
    doc.setFillColor(251,250,248);doc.setDrawColor(...RULE);doc.setLineWidth(.2);
    /* draw all header cells first, then the labels, so no fill paints over a neighbour's text */
    let x=L;cw.forEach(w=>{doc.rect(x,y-4.6,w,7,"FD");x+=w;});
    x=L;doc.setFont("helvetica","bold");doc.setFontSize(7.5);doc.setTextColor(...MUTED);
    ["REF","BUILD-UP","STANDARD"].forEach((hd,j)=>{doc.text(hd,x+2,y);x+=cw[j];});
    y+=7;
    sel.forEach(i=>{ const b=allBU()[i];need(9);
      const tl=doc.splitTextToSize(safe(b.t),cw[1]-4), rh=Math.max(7,tl.length*3.6+3.4);
      let x2=L;cw.forEach(w=>{doc.rect(x2,y-4.6,w,rh,"D");x2+=w;});
      doc.setFont("helvetica","bold");doc.setFontSize(8);doc.setTextColor(...ACC);doc.text(r[i],L+2,y);
      doc.setFont("helvetica","normal");doc.setTextColor(...DARK);
      tl.forEach((ln,k)=>doc.text(ln,L+cw[0]+2,y+k*3.6));
      doc.text(safe(b.u||"—"),L+cw[0]+cw[1]+2,y); y+=rh; });
    y+=4;
    secHead("2.0","Part A — Construction build-ups");
    let lg=null;
    sel.forEach(i=>{ const b=allBU()[i];
      if(b.g!==lg){lg=b.g;grpLabel(GROUPS[b.g]||b.g,true);}
      entry(r[i],b.t);
      if(b.tgt) para(b.tgt,9,2.2,ACC,"bold");
      b.p.forEach(t=>para(t, t.startsWith("NOTE")?8:9, 2.4, t.startsWith("NOTE")?MUTED:DARK)); });
  } else para("No build-ups selected.",9,3,MUTED);

  const ns=noteSections();
  if(ns.size){ secHead("3.0","Part B — General specification notes");
    let sub=0;
    ns.forEach((items,s)=>{ sub++; grpLabel("3."+sub+"   "+s);
      items.forEach(it=>{ entry("",it.t); it.p.forEach(t=>para(t, t.startsWith("NOTE")?8:9, 2.4, t.startsWith("NOTE")?MUTED:DARK)); }); }); }
  const calcs=calcsOnJob();
  if(calcs.length){
    need(75);
    secHead("4.0","U-value calculations");
    para("Calculated to BS EN ISO 6946 using the combined method for mortar-bridged blockwork and the Annex F corrections for air gaps and wall ties. Indicative: the manufacturer's certified calculation is to be obtained before submission.",8.5,3,MUTED);
    calcs.forEach(({i,b},ci)=>{
      if(ci>0) need(46);
      entry(r[i],b.t);
      const res=b.calc.result, cw=[112,18,40];
      const row=(a,bb,c,bold)=>{ need(6.5);
        doc.setFont("helvetica",bold?"bold":"normal");doc.setFontSize(8);doc.setTextColor(...DARK);
        doc.splitTextToSize(safe(a),cw[0]-3).forEach((ln,k)=>doc.text(ln,L+1.5,y+k*3.4));
        doc.text(safe(bb),L+cw[0]+cw[1]-2,y,{align:"right"}); doc.text(safe(c),L+cw[0]+cw[1]+cw[2]-2,y,{align:"right"});
        y+=Math.max(4.6,doc.splitTextToSize(safe(a),cw[0]-3).length*3.4+1.2); };
      doc.setFont("helvetica","bold");doc.setFontSize(7.5);doc.setTextColor(...MUTED);
      doc.text("LAYER",L+1.5,y);doc.text("MM",L+cw[0]+cw[1]-2,y,{align:"right"});doc.text("R  m²K/W",L+cw[0]+cw[1]+cw[2]-2,y,{align:"right"});
      y+=1.5;doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.line(L,y,L+cw[0]+cw[1]+cw[2],y);y+=4.2;
      res.layers.forEach(l=>row(l.n, l.d!=null?String(l.d):"—", l.R.toFixed(3)));
      doc.setDrawColor(...RULE);doc.line(L,y-3,L+cw[0]+cw[1]+cw[2],y-3);
      if(res.steps){ res.steps.forEach(([a,bb],k)=>row(a,"",bb,k===res.steps.length-1)); }
      else {
        row("RT upper / lower limit","",res.RT_upper.toFixed(3)+" / "+res.RT_lower.toFixed(3));
        row("RT (mean)","",res.RT.toFixed(3),true);
        row("U0 = 1 / RT","",res.U0.toFixed(3),true);
        if(res.dUg) row("dUg  air gaps (Annex F)","","+"+res.dUg.toFixed(3));
        if(res.dUf) row("dUf  fasteners (Annex F)","","+"+res.dUf.toFixed(3));
        row("U","",res.U.toFixed(3)+"  ->  "+res.U.toFixed(2)+" W/m²K",true);
      }
      para("Sources: "+res.src.join(" · "),7.5,3,MUTED);
    });
  }
  need(24);y+=4;
  doc.setDrawColor(...ACC);doc.setLineWidth(.8);doc.line(L,y,L+3,y);
  doc.setFont("helvetica","bold");doc.setFontSize(8.5);doc.setTextColor(...ACC);
  doc.text("VERIFY BEFORE ISSUE",L+6,y+1);y+=6;
  para("Approved Documents L1 and F1, 2026 editions, come into force on 24 March 2027. Work with a full plans "+
       "application submitted before that date remains under the current standards provided work commences "+
       "before 24 March 2028. Confirm all clause and table references against the edition in force at the date "+
       "of submission.",8,2,MUTED);
  foot();
  return doc;
}

/* ---------------- Word export ----------------
   Same content and order as the PDF, written straight to .docx by src/docx.js.
   The practice profile supplies the logo, the cover and the running header, exactly
   as it does for the PDF: Specline's own mark never appears on a document. */
/* ACC_HEX is read per document, not fixed: it was the vendor's own brand orange, which coloured
   every heading, rule and reference on every subscriber's specification. */
const DARK_HEX = "23262A", MUTED_HEX = "6E7477", RULE_HEX = "D9DCDD", WELL_HEX = "FBFAF8";

function buildDocx(){
  const D = DOCX, d = S.data, r = refs(), sel = orderedSel();
  const ACC_HEX = accInk();
  const today = new Date().toLocaleDateString("en-GB", {day:"numeric", month:"long", year:"numeric"});
  const nt = coverNotice();
  const out = [];

  /* ---- cover ---- */
  const img = P.logo ? D.dataUriToImage(P.logo) : null;
  if(img){
    /* fit inside 34 x 30 mm at the logo's own proportions, as the PDF does */
    const bw = 34, bh = 30; let w = bw, h = bh;
    if(P.logoW && P.logoH){ const ar = P.logoW / P.logoH;
      if(ar >= bw/bh){ w = bw; h = bw/ar; } else { h = bh; w = bh*ar; } }
    out.push(D.image("rIdLogo", w * D.EMU_PER_MM, h * D.EMU_PER_MM, pName() + " logo"));
  } else {
    /* No logo: the practice's own name as a wordmark, as the cover page does. */
    const w = pName().split(" ");
    out.push(D.para([D.run(w[0], {b:true, sz:56, color:DARK_HEX})].concat(
      w.length > 1 ? [D.run(" " + w.slice(1).join(" ").toUpperCase(), {b:true, sz:32, color:ACC_HEX})] : []),
      {after:80}));
  }
  out.push(D.para(D.run(P.addr + (P.email ? "  ·  " + P.email : "") + (P.phone ? "  ·  " + P.phone : ""),
    {sz:16, color:MUTED_HEX}), {after:40, border:{side:"bottom", sz:12, color:ACC_HEX}}));

  out.push(D.para(D.run("BUILDING REGULATIONS", {b:true, sz:56, color:DARK_HEX}), {before:360, after:0}));
  out.push(D.para(D.run("SPECIFICATION", {b:true, sz:56, color:ACC_HEX}), {after:80}));
  out.push(D.para(D.run((spec().name + " — " + spec().region).toUpperCase(), {b:true, sz:22, color:MUTED_HEX}), {after:400}));

  const rows = [["Project", d.project], ["Site address", d.address], ["Client", d.client],
    ["Job number", d.job], ["Local authority", d.la], ...(m4Label()?[["Access category", m4Label()]]:[]), ["Application", "Full Plans Application"],
    ["Prepared by", (P.designer ? P.designer + ", " : "") + pName()], ["Date", today], ["Revision", d.rev || "P01"]];
  out.push(D.table(rows.map(([k,v]) => [
    {text:k, w:2600, b:true, sz:18, shade:WELL_HEX},
    {text:v || "—", w:6760, sz:18}
  ])));

  out.push(D.para(D.run("ISSUED FOR BUILDING CONTROL APPROVAL", {b:true, sz:20, color:ACC_HEX}),
    {before:360, after:60}));
  out.push(D.para(D.run(nt.lead, {sz:17, color:MUTED_HEX}), {after:80}));
  out.push(D.para(D.run(nt.resp, {sz:17, color:MUTED_HEX}), {after:80}));

  const hist = S.history || [];
  if(hist.length){
    out.push(D.para(D.run("ISSUE HISTORY", {b:true, sz:16, color:MUTED_HEX}), {before:240, after:60}));
    hist.forEach(h => out.push(D.para(
      [D.run(h.rev + "   ", {b:true, sz:17}), D.run("Issued " + fmtDate(h.at) + " · " + h.n + " build-ups, " + h.m + " notes", {sz:17, color:MUTED_HEX})],
      {after:40})));
  }
  out.push(D.pageBreak());

  /* ---- helpers matching the PDF's furniture ---- */
  const secHead = (num, txt) => {
    out.push(D.para([D.run(num + "   ", {b:true, sz:26, color:ACC_HEX}),
                     D.run(txt.toUpperCase(), {b:true, sz:26, color:DARK_HEX})],
      {before:320, after:60, keepNext:true, border:{side:"bottom", sz:10, color:ACC_HEX}}));
  };
  const grpLabel = (t, cat) => out.push(D.para(
    (cat ? [D.run("•  ", {b:true, sz:16, color:ACC_HEX})] : [])
      .concat(D.run(t.toUpperCase(), {b:true, sz:16, color:MUTED_HEX})),
    {before:240, after:60, keepNext:true}));
  const entry = (tag, title) => out.push(D.para(
    (tag ? [D.run(tag + "   ", {b:true, sz:19, color:ACC_HEX})] : []).concat(
      [D.run(title.toUpperCase(), {b:true, sz:19, color:DARK_HEX})]),
    {before:200, after:60, keepNext:true, border:{side:"bottom", sz:4, color:RULE_HEX}}));
  const body = t => out.push(D.para(D.run(t, t.startsWith("NOTE") ? {sz:16, color:MUTED_HEX} : {sz:18, color:DARK_HEX}),
    {after:100, ind:t.startsWith("NOTE") ? 220 : 0}));

  /* ---- 1.0 schedule ---- */
  secHead("1.0", "Construction build-up schedule");
  if(sel.length){
    const head = [{text:"REF", w:900, b:true, sz:15, color:MUTED_HEX, shade:WELL_HEX},
                  {text:"BUILD-UP", w:6000, b:true, sz:15, color:MUTED_HEX, shade:WELL_HEX},
                  {text:"STANDARD", w:2460, b:true, sz:15, color:MUTED_HEX, shade:WELL_HEX}];
    const trs = sel.map(i => { const b = allBU()[i];
      return [{text:r[i], w:900, b:true, sz:17, color:ACC_HEX},
              {text:b.t, w:6000, sz:17},
              {text:b.u || "—", w:2460, sz:17}]; });
    out.push(D.table([head].concat(trs)));
  } else {
    out.push(D.para(D.run("No build-ups selected.", {sz:18, color:MUTED_HEX, i:true})));
  }

  /* ---- 2.0 Part A ---- */
  if(sel.length){
    secHead("2.0", "Part A — Construction build-ups");
    let lg = null;
    sel.forEach(i => { const b = allBU()[i];
      if(b.g !== lg){ lg = b.g; grpLabel(GROUPS[b.g] || b.g, true); }
      entry(r[i], b.t);
      if(b.tgt) out.push(D.para(D.run(b.tgt, {b:true, sz:18, color:ACC_HEX}), {after:80}));
      b.p.forEach(body);
    });
  }

  /* ---- 3.0 Part B ---- */
  const ns = noteSections();
  if(ns.size){
    secHead("3.0", "Part B — General specification notes");
    let sub = 0;
    ns.forEach((items, sname) => { sub++; grpLabel("3." + sub + "   " + sname);
      items.forEach(it => { entry("", it.t); it.p.forEach(body); }); });
  }

  /* ---- 4.0 U-value working ---- */
  const calcs = calcsOnJob();
  if(calcs.length){
    secHead("4.0", "U-value calculations");
    out.push(D.para(D.run("Calculated to BS EN ISO 6946 using the combined method for mortar-bridged blockwork and the Annex F corrections for air gaps and wall ties. Indicative: the manufacturer's certified calculation is to be obtained before submission.",
      {sz:17, color:MUTED_HEX}), {after:140}));
    calcs.forEach(({i,b}) => {
      entry(r[i], b.t);
      const res = b.calc.result;
      const head = [{text:"LAYER", w:6000, b:true, sz:15, color:MUTED_HEX, shade:WELL_HEX},
                    {text:"MM", w:1200, b:true, sz:15, color:MUTED_HEX, shade:WELL_HEX, align:"right"},
                    {text:"R  m²K/W", w:2160, b:true, sz:15, color:MUTED_HEX, shade:WELL_HEX, align:"right"}];
      const trs = res.layers.map(l => [
        {text:l.n, w:6000, sz:16},
        {text:l.d != null ? String(l.d) : "—", w:1200, sz:16, align:"right"},
        {text:l.R.toFixed(3), w:2160, sz:16, align:"right"}]);
      const steps = [];
      if(res.steps){
        res.steps.forEach(([a,v], k) => steps.push([
          {text:a, w:6000, sz:16, b:k === res.steps.length-1},
          {text:"", w:1200, sz:16},
          {text:v, w:2160, sz:16, align:"right", b:k === res.steps.length-1}]));
      } else {
        const line = (a, v, bold) => steps.push([
          {text:a, w:6000, sz:16, b:bold}, {text:"", w:1200, sz:16},
          {text:v, w:2160, sz:16, align:"right", b:bold}]);
        line("RT upper / lower limit", res.RT_upper.toFixed(3) + " / " + res.RT_lower.toFixed(3));
        line("RT (mean)", res.RT.toFixed(3), true);
        line("U0 = 1 / RT", res.U0.toFixed(3), true);
        if(res.dUg) line("ΔUg  air gaps (Annex F)", "+" + res.dUg.toFixed(3));
        if(res.dUf) line("ΔUf  fasteners (Annex F)", "+" + res.dUf.toFixed(3));
        line("U", res.U.toFixed(3) + "  →  " + res.U.toFixed(2) + " W/m²K", true);
      }
      out.push(D.table([head].concat(trs, steps)));
      out.push(D.para(D.run("Sources: " + res.src.join(" · "), {sz:15, color:MUTED_HEX}), {before:60, after:140}));
    });
  }

  /* ---- closing flag ---- */
  out.push(D.para(D.run("VERIFY BEFORE ISSUE", {b:true, sz:18, color:ACC_HEX}), {before:320, after:60}));
  out.push(D.para(D.run("Approved Documents L1 and F1, 2026 editions, come into force on 24 March 2027. Work with a full plans application submitted before that date remains under the current standards provided work commences before 24 March 2028. Confirm all clause and table references against the edition in force at the date of submission.",
    {sz:16, color:MUTED_HEX}), {after:0}));

  return D.build({
    body: out.join(""),
    header: {left: spec().name + " — Building Regulations Specification" + (d.address ? "  ·  " + d.address : ""),
             right: (d.job ? "Job " + d.job : "") + "  |  Rev " + (d.rev || "P01")},
    footer: {left: pName() + (P.email ? "  ·  " + P.email : "")},
    image: img
  });
}

/* ---------------- actions ---------------- */
let downloads=null, db=null;
function toast(m){ const t=document.createElement("div");t.className="toast";t.textContent=m;
  document.body.appendChild(t);setTimeout(()=>t.remove(),3400); }

function specFilename(ext){
  return `${(S.data.job||"spec").replace(/[^\w-]/g,"")}_${spec().name.replace(/\s+/g,"_")}_Spec_${S.data.rev||"P01"}.${ext}`;
}
async function deliver(blob, filename, label){
  if(downloads){
    try{ await downloads.save({filename,data:blob}); toast(label+" saved"); return true; }
    catch(e){ toast(e&&e.code==="declined" ? "Download declined" : "Could not save the "+label); return false; }
  }
  const u=URL.createObjectURL(blob), a=document.createElement("a");
  a.href=u; a.download=filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(u),4000);
  toast(label+" downloaded"); return true;
}
/* fmt: "pdf" | "docx" */
async function makeDoc(fmt){
  const label = fmt==="docx" ? "Word file" : "PDF";
  const btns=[el("btnPdf"),el("btnPdf2"),el("btnDocx"),el("btnDocx2"),el("finish"),el("finishDocx"),el("issue")].filter(Boolean);
  btns.forEach(b=>{b.disabled=true;b.dataset.l=b.textContent;});
  const active=[el("btnPdf"),el("btnPdf2"),el("btnDocx"),el("btnDocx2"),el("finish"),el("finishDocx"),el("issue")].filter(Boolean);
  active.forEach(b=>{ if((fmt==="docx") === /Word/.test(b.dataset.l||"")) b.textContent="Building the "+label+"…"; });
  let ok=false;
  try{
    const blob = fmt==="docx" ? buildDocx() : buildPdf().output("blob");
    ok = await deliver(blob, specFilename(fmt), label);
  }catch(e){ toast("Something went wrong building the "+label); console.error(e); }
  btns.forEach(b=>{b.disabled=false;b.textContent=b.dataset.l;});
  return ok;
}
const makePdf  = () => makeDoc("pdf");
const makeDocx = () => makeDoc("docx");

/* ---------------- jobs: draft, store, list ---------------- */
function uid(){ return "j"+Date.now().toString(36)+Math.random().toString(36).slice(2,6); }
function snapshot(){ return {id:S.id,type:S.type,data:{...S.data},sel:[...S.sel],notes:{...S.notes},step:S.step,visited:S.visited||{},custom:S.custom||[],ovr:S.ovr||{},cfg:S.cfg||null,cfgF:S.cfgF||null,cfgR:S.cfgR||null,history:S.history||[],created:S.created||Date.now(),updated:Date.now(),route:S.route}; }
function loadInto(j){
  S.id=j.id||uid(); S.type=j.type; S.data={}; FIELDS.forEach(f=>S.data[f[0]]=f[2]); S.data={...S.data,...j.data};
  S.ovr=j.ovr||{}; if(!S.data.mfr) S.data.mfr="kingspan"; S.sel=[...(j.sel||[])]; S.notes={...(j.notes||{})};
  S.step=(j.step===undefined||j.step===null)?-1:j.step; S.visited=j.visited||{}; S.open={}; S.custom=j.custom||[];
  S.cfg=j.cfg||null; S.cfgF=j.cfgF||null; S.cfgR=j.cfgR||null; S.history=j.history||[]; S.created=j.created||Date.now();
  /* a job saved before the Part M category existed carried all three notes: settle it on M4(1) */
  if(m4Notes() && !S.data.m4) applyM4();
}
function newJob(type){
  S.id=uid(); S.type=type; S.data={}; FIELDS.forEach(f=>S.data[f[0]]=f[2]); S.data.mfr="kingspan"; S.history=[]; S.created=Date.now();
  defaults(); S.route="job"; renderAll(); save();
  toast("New job started. It saves as you go.");
}
function openJob(id){
  const j=jobsCache.find(x=>x.id===id); if(!j||!SPECS[j.type]) return;
  loadInto(j); S.route="job"; renderAll(); save(); toast("Job opened");
}

let jobsCache=[], saveTimer=null;
const JOBS_KEY="syds-jobs";
function localJobs(){ try{ return JSON.parse(localStorage.getItem(JOBS_KEY)||"{}"); }catch(e){ return {}; } }
function localPut(j){ try{ const m=localJobs(); m[j.id]=j; localStorage.setItem(JOBS_KEY,JSON.stringify(m)); }catch(e){} }
function localDel(id){ try{ const m=localJobs(); delete m[id]; localStorage.setItem(JOBS_KEY,JSON.stringify(m)); }catch(e){} }

function setSaveState(cls,txt){ const s=el("savestate"); s.hidden=!S.type; s.className="savestate "+cls; el("savetext").textContent=txt; }
function save(){
  try{ localStorage.setItem("syds-spec-draft",JSON.stringify(snapshot())); }catch(e){}
  if(!S.type) return;
  setSaveState("busy","Saving…");
  clearTimeout(saveTimer); saveTimer=setTimeout(persist,650);
}
async function persist(){
  const j=snapshot(); localPut(j);
  const k=jobsCache.findIndex(x=>x.id===j.id); if(k>=0) jobsCache[k]=j; else jobsCache.push(j);
  if(db){
    try{ await db.doc("jobs/"+j.id).set(j); setSaveState("","Saved · "+(j.data.job?"job "+j.data.job:"unnumbered")); }
    catch(e){ setSaveState("err", window.SPECLINE_SIGNED_OUT
        ? "Signed out — the job is safe in this browser. Sign in again to save it to the practice."
        : "Kept in this browser only"); console.error(e); }
  } else setSaveState("","Kept in this browser");
  if(S.route==="home") renderHome();
}
function restore(){
  try{ const j=JSON.parse(localStorage.getItem("syds-spec-draft")||"null");
    if(j&&j.type&&SPECS[j.type]){ loadInto(j); S.route=j.route&&ROUTES.includes(j.route)?j.route:"job"; return true; }
  }catch(e){} return false;
}
async function loadJobs(){
  const local=Object.values(localJobs());
  if(db){
    try{
      const snap=await db.collection("jobs").limit(100).get();
      const docs=(snap&&(snap.docs||snap))||[];
      jobsCache=docs.map(x=>x.data?{id:x.id,...x.data()}:x).filter(j=>j&&j.type);
      /* anything saved offline that the store has not seen yet */
      local.forEach(j=>{ if(!jobsCache.find(x=>x.id===j.id)) jobsCache.push(j); });
    }catch(e){ jobsCache=local; console.error(e); }
  } else jobsCache=local;
  if(S.route==="home") renderHome();
}
async function deleteJob(id){
  localDel(id); jobsCache=jobsCache.filter(j=>j.id!==id);
  if(db){ try{ await db.doc("jobs/"+id).delete(); }catch(e){} }
  if(S.id===id){ S.type=null; S.id=null; try{ localStorage.removeItem("syds-spec-draft"); }catch(e){} }
  go("home"); toast("Job deleted");
}

/* ---------------- header and chrome ---------------- */
/* Adding a build-up from a calculator puts a card in the library list, so go back to it: the
   new reference is the thing to see, and a toast alone leaves the page looking unchanged.
   Capture, so this runs before the configurator's own handler re-renders the stage. */
el("stage").addEventListener("click", e=>{
  if(e.target && e.target.closest && e.target.closest("#addWall,#addFrame,#addFloor,#addRoof,#addFound")) S.tab="bus";
}, true);

el("btnPdf").onclick=makePdf;
el("btnPdf2").onclick=makePdf;
el("btnDocx").onclick=makeDocx;
el("btnDocx2").onclick=makeDocx;
el("btnNew").onclick=()=>showChooser("new");
el("btnType").onclick=()=>showChooser("change");
el("closeChooser").onclick=()=>{ el("chooser").hidden=true; el("tiles").innerHTML=""; };
el("chooser").addEventListener("click",e=>{ if(e.target===el("chooser")) el("closeChooser").click(); });
document.addEventListener("keydown",e=>{ if(e.key==="Escape"&&!el("chooser").hidden) el("closeChooser").click(); });
el("btnSave").onclick=async()=>{ clearTimeout(saveTimer); await persist(); toast(db?"Job saved":"Job kept in this browser"); };
el("btnPrev").onclick=()=>{ document.body.classList.toggle("showprev");
  el("btnPrev").textContent = document.body.classList.contains("showprev") ? "Hide preview" : "Preview"; };
el("themeBtn").onclick=()=>{
  const root=document.documentElement;
  const dark = root.dataset.theme==="dark" || (!root.dataset.theme && matchMedia("(prefers-color-scheme:dark)").matches);
  root.dataset.theme = dark?"light":"dark";
  try{ localStorage.setItem("syds-theme",root.dataset.theme); }catch(e){}
};
try{ const t=localStorage.getItem("syds-theme"); if(t) document.documentElement.dataset.theme=t; }catch(e){}

loadPractice();
jobsCache=Object.values(localJobs());
if(restore()){ renderAll(); setSaveState("",db?"Saved":"Kept in this browser"); } else { go("home"); }
(async()=>{
  /* Hosted on specline.co.uk behind the practice login: site/app.php injects SPECLINE, and
     the store is the practice's own on the server. The browser's own download does the
     saving, so no downloads capability is needed. */
  if(window.SPECLINE && window.SPECLINE.api){
    db = serverStore(window.SPECLINE);
    /* The signed-in account's own practice becomes what a profile is merged onto, so a field
       this practice has not filled in falls back to its account details — never to a firm
       compiled into the app. app.php builds it from the practices row. */
    if(window.SPECLINE.practice){
      PRACTICE_BASE = {...PRACTICE_BLANK, ...window.SPECLINE.practice};
      /* A saved profile is what the practice last chose, so it wins where it has a value;
         with nothing saved the account's own details stand on their own. Merging an unsaved
         blank over the account would have wiped the cover back to placeholders. */
      P = practiceStored ? {...PRACTICE_BASE, ...P} : {...PRACTICE_BASE};
    }
    /* Hosted behind the practice login, so give the header a way back out of the tool. */
    const nb = el("btnNew");
    if(nb && nb.parentNode && window.SPECLINE.account){
      const who = document.createElement("a");
      who.className = "btn btn-quiet"; who.href = window.SPECLINE.account;
      who.textContent = (window.SPECLINE.user && window.SPECLINE.user.name) || "Account";
      who.title = "Your Specline account";
      const out = document.createElement("a");
      out.className = "btn btn-quiet"; out.href = window.SPECLINE.signout || "/account/logout.php";
      out.textContent = "Sign out";
      nb.parentNode.insertBefore(who, nb); nb.parentNode.insertBefore(out, nb);
    }
    await loadJobs(); await loadPracticeRemote();
    setSaveState("", S.type ? "Saved to your practice" : "");
    return;
  }
  if(!window.claude||!claude.use) return;
  try{ downloads=await claude.use("downloads"); }catch(e){}
  try{ db=await claude.use("db"); }catch(e){}
  if(db){ loadJobs(); loadPracticeRemote(); }
})();
