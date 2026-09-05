const PRACTICE = {name:"SY Design Studio Ltd", addr:"49 Durham Avenue, Hounslow, TW5 0HG", email:"info@sydesignstudio.co.uk"};
const GROUPS = {SW:"Separating walls", SF:"Separating floors", EW:"External walls", IW:"Internal walls", GF:"Ground floors", IF:"Floors", RF:"Roofs", BW:"Basement walls", BF:"Basement floors"};
const GORDER = ["SW","SF","EW","IW","GF","IF","RF"];

/* every project type in the library, built or not */
const TYPES = [
  {k:"extension", n:"House Extension",     r:"England", ready:true,  d:"Single and two storey"},
  {k:"loft",      n:"Loft Conversion",     r:"England", ready:true,  d:"Dormer, hip to gable, room in roof"},
  {k:"garage",    n:"Garage Conversion",   r:"England", ready:true, d:"Integral and detached"},
  {k:"flat",      n:"Flat Conversion",     r:"England", ready:true,  d:"Material change of use"},
  {k:"newbuild",  n:"New Build",           r:"England", ready:true, d:"Dwellinghouse"},
  {k:"nbflats",   n:"New Build Flats",     r:"England", ready:true, d:"Purpose built"},
  {k:"basement",  n:"Basement Conversion", r:"England", ready:true, d:"Underpinning and tanking"},
  {k:"garagebld", n:"Garage Build",        r:"England", ready:true, d:"Detached and attached"}
];


const FIELDS = [
  ["project","Project","Single storey rear extension",1],
  ["address","Site address","00 Example Road, Hounslow TW3 0AA",1],
  ["client","Client","Mr & Mrs Example",0],
  ["job","Job number","1134",0],
  ["la","Local authority","London Borough of Hounslow",0],
  ["rev","Revision","P01",0]
];

let S = {type:null, data:{}, sel:[], notes:{}, step:0, open:{}, mobile:"build"};
FIELDS.forEach(f=>S.data[f[0]]=f[2]);

const el = id => document.getElementById(id);
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const spec = () => SPECS[S.type];
const cats = () => (spec().cats) || [];
const buCat = b => {
  if(b.cat==="__wall__")  return cats().find(isWallCat)||cats()[0];
  if(b.cat==="__floor__") return cats().find(isFloorCat)||cats()[0];
  if(b.cat==="__roof__")  return cats().find(isRoofCat)||cats()[0];
  return b.c; };
const ntCat = n => n.c;

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
  S.sel=[]; S.notes={}; S.step=0; S.open={}; S.custom=[];
  spec().notes.forEach((n,i)=>S.notes[i]=true);
  ["SW","SF","EW","GF","RF","IF"].forEach(g=>{ const i=spec().buildups.findIndex(b=>b.g===g); if(i>=0) S.sel.push(i); });
  S.sel.sort((a,b)=>a-b);
}
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

/* ---------------- type chooser ---------------- */
function showChooser(){
  el("chooser").hidden=false;
  el("tiles").innerHTML = TYPES.map(t=>`
    <button class="tile ${t.ready?"":"soon"}" data-k="${t.k}" ${t.ready?"":"disabled"}>
      <span class="tn">${esc(t.n)}</span>
      <span class="td">${esc(t.d)}</span>
      <span class="tr">${t.ready?esc(t.r):"Not yet written"}</span>
    </button>`).join("");
  el("tiles").querySelectorAll("button:not(:disabled)").forEach(b=>b.onclick=()=>{
    S.type=b.dataset.k; defaults(); el("chooser").hidden=true; renderAll(); save();
  });
}

/* ---------------- panes ---------------- */
function renderSteps(){
  el("steps").innerHTML = cats().map((c,i)=>{
    const n=catCount(c), tot=catTotal(c);
    return `<button class="step ${i===S.step?"cur":""}" data-i="${i}">
      <span class="sn">${String(i+1).padStart(2,"0")}</span>
      <span class="st">${esc(c)}</span>
      <span class="sc ${n?"has":""}">${n}/${tot}</span></button>`;
  }).join("");
  el("steps").querySelectorAll("button").forEach(b=>b.onclick=()=>{ S.step=+b.dataset.i; renderStage(); renderSteps(); });
}

function renderStage(){
  const cat = cats()[S.step];
  if(cat===undefined) return;
  const {bus,nts} = catItems(cat);
  const r = refs();
  let h = `<div class="stagehead">
      <p class="crumb">Step ${S.step+1} of ${cats().length} &nbsp;·&nbsp; ${esc(spec().name)}</p>
      <h2>${esc(cat)}</h2>
      <p class="lede">${bus.length?"Tick the build-ups used on this project. They number themselves in the order you select them.":"Tick the notes to include. Everything here is on by default — untick what does not apply."}</p>
    </div>`;

  if(S.step===0){
    h += `<div class="card projcard"><h3>Project details</h3><div class="fields" id="fields"></div></div>`;
  }
  if(isWallCat(cat)) h += renderConfigurator();
  if(isFloorCat(cat)) h += renderFloorConfigurator(cat);
  if(isRoofCat(cat)) h += renderRoofConfigurator();
  if(bus.length){
    h += `<p class="grouplabel">Construction build-ups</p>`;
    h += bus.map(({b,i})=>{
      const on=S.sel.includes(i), opened=S.open["b"+i];
      return `<div class="card ${on?"on":""}">
        <label class="cardhead"><input type="checkbox" data-t="b" data-i="${i}" ${on?"checked":""}>
          <span class="tag ${on?"":"off"}">${on?r[i]:"—"}</span>
          <span class="ct">${esc(b.t)}</span>
          ${b.u?`<span class="cu">${esc(b.u)}</span>`:""}
          ${b.calc?`<button class="rm" data-rm="${i}" title="Remove this custom build-up">Remove</button>`:""}</label>
        ${b.tgt?`<p class="tgt">${esc(b.tgt)}</p>`:""}
        <div class="text ${opened?"":"clip"}">${b.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join("")}</div>
        ${b.p.length>1||b.p[0].length>210?`<button class="more" data-o="b${i}">${opened?"Show less":"Read full clause"}</button>`:""}
      </div>`;
    }).join("");
  }
  if(nts.length){
    if(bus.length) h += `<p class="grouplabel">Specification notes</p>`;
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
  if(!bus.length && !nts.length) h += `<p class="lede">Nothing in this category for this project type.</p>`;

  const last = S.step===cats().length-1;
  h += `<div class="navbar">
      <button class="btn" id="prev" ${S.step?"":"disabled"}>← Back</button>
      <span class="prog"><span style="width:${((S.step+1)/cats().length*100).toFixed(1)}%"></span></span>
      ${last?`<button class="btn btn-primary" id="finish">Generate PDF</button>`
            :`<button class="btn btn-primary" id="next">Next →</button>`}
    </div>`;
  el("stage").innerHTML=h;
  el("stage").scrollTop=0;

  if(S.step===0) renderFields();
  el("stage").querySelectorAll('input[type=checkbox]').forEach(inp=>inp.onchange=()=>{
    const i=+inp.dataset.i;
    if(inp.dataset.t==="b"){ if(inp.checked){ if(!S.sel.includes(i)) S.sel.push(i); } else S.sel=S.sel.filter(x=>x!==i); }
    else S.notes[i]=inp.checked;
    renderStage(); renderSteps(); renderPaper(); save();
  });
  bindConfigurator(); bindConfigurator2();
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
  if(p) p.onclick=()=>{ if(S.step){S.step--; renderStage(); renderSteps();} };
  if(n) n.onclick=()=>{ if(S.step<cats().length-1){S.step++; renderStage(); renderSteps();} };
  if(f) f.onclick=makePdf;
}

function renderFields(){
  const c=el("fields"); if(!c) return;
  c.innerHTML = FIELDS.map(f=>
    `<label class="${f[3]?"wide":""}">${esc(f[1])}<input data-k="${f[0]}" value="${esc(S.data[f[0]])}"></label>`).join("");
  c.querySelectorAll("input").forEach(i=>i.oninput=()=>{ S.data[i.dataset.k]=i.value; renderPaper(); save(); });
}

/* ---------------- preview ---------------- */
function renderPaper(){
  if(!S.type) return;
  const r=refs(), sel=orderedSel(), d=S.data;
  const today=new Date().toLocaleDateString("en-GB",{day:"numeric",month:"long",year:"numeric"});
  let h=`<img class="plogo lg-l" src="${LOGO}" alt="SY Design Studio"><img class="plogo lg-d" src="${LOGO_DARK}" alt="">
    <p class="paddr">${esc(PRACTICE.addr)} &nbsp;·&nbsp; ${esc(PRACTICE.email)}</p>
    <h1 class="ptitle">BUILDING REGULATIONS<span class="o">SPECIFICATION</span></h1>
    <p class="psub">${esc(spec().name)} — ${esc(spec().region)}</p>
    <table class="meta">
      <tr><td>Project</td><td>${esc(d.project||"—")}</td></tr>
      <tr><td>Site address</td><td>${esc(d.address||"—")}</td></tr>
      <tr><td>Client</td><td>${esc(d.client||"—")}</td></tr>
      <tr><td>Job number</td><td>${esc(d.job||"—")}</td></tr>
      <tr><td>Local authority</td><td>${esc(d.la||"—")}</td></tr>
      <tr><td>Prepared by</td><td>Salman Yousaf, ${esc(PRACTICE.name)}</td></tr>
      <tr><td>Date</td><td>${today}</td></tr>
      <tr><td>Revision</td><td>${esc(d.rev||"P01")}</td></tr>
    </table>
    <div class="flag"><b>ISSUED FOR BUILDING CONTROL APPROVAL.</b> To be read with the SY Design Studio Ltd
      drawing pack, the structural engineer's design and calculations, and any specialist sub-contractor design.
      All work to comply with the Building Regulations 2010 (as amended) and the Approved Documents current at
      the date of issue.</div>
    <div class="sec"><i>1.0</i>Construction build-up schedule</div>`;
  if(!sel.length) h+=`<p class="empty">No build-ups selected yet.</p>`;
  else {
    h+=`<table class="sched"><tr><th>Ref</th><th>Build-up</th><th>Standard</th></tr>`+
      sel.map(i=>{const b=allBU()[i];
        return `<tr><td class="r">${r[i]}</td><td>${esc(b.t)}</td><td class="u">${esc(b.u||"—")}</td></tr>`;}).join("")+`</table>`;
    h+=`<div class="sec"><i>2.0</i>Part A — Construction build-ups</div>`;
    let lg=null;
    sel.forEach(i=>{const b=allBU()[i];
      if(b.g!==lg){lg=b.g; h+=`<p class="glab">${esc(GROUPS[b.g]||b.g)}</p>`;}
      h+=`<div class="eh"><span class="tag2">${r[i]}</span><h4>${esc(b.t)}</h4></div>`;
      if(b.tgt) h+=`<p class="tl">${esc(b.tgt)}</p>`;
      h+=b.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join("");
    });
  }
  const ns=noteSections();
  if(ns.size){
    h+=`<div class="sec"><i>3.0</i>Part B — General specification notes</div>`;
    ns.forEach((items,s)=>{ h+=`<p class="glab">${esc(s)}</p>`;
      items.forEach(it=>{ h+=`<div class="eh"><h4>${esc(it.t)}</h4></div>`+it.p.map(x=>`<p class="${x.startsWith("NOTE")?"nt":""}">${esc(x)}</p>`).join(""); });
    });
  }
  const calcs=sel.map(i=>({i,b:allBU()[i]})).filter(x=>x.b.calc);
  if(calcs.length){
    h+=`<div class="sec"><i>4.0</i>U-value calculations</div>
        <p style="color:var(--muted)">Calculated to BS EN ISO 6946 using the combined method for mortar-bridged blockwork and the Annex F corrections for air gaps and wall ties. Indicative — the manufacturer's certified calculation is to be obtained before submission.</p>`;
    calcs.forEach(({i,b})=>{ h+=`<div class="eh"><span class="tag2">${r[i]}</span><h4>${esc(b.t)}</h4></div>`+(b.calc.result.steps?layersOnly(b.calc.result)+stepsTable(b.calc.result):workingTable(b.calc.result))+
      `<p style="font-size:9.5px;color:var(--muted)">Sources: ${b.calc.result.src.map(esc).join(" · ")}</p>`; });
  }
  h+=`<div class="flag" style="margin-top:26px"><b>VERIFY BEFORE ISSUE.</b> Approved Documents L1 and F1, 2026
    editions, come into force on 24 March 2027; work with a full plans application submitted before that date
    remains under the current standards provided work commences before 24 March 2028. Confirm all clause and
    table references against the edition in force at the date of submission.</div>`;
  el("paper").innerHTML=h;
}

function renderAll(){
  if(!S.type){ showChooser(); return; }
  el("typename").textContent = spec().name;
  el("app").hidden=false;
  renderSteps(); renderStage(); renderPaper();
}

/* ---------------- PDF ---------------- */
/* jsPDF standard fonts use WinAnsi. Anything outside it prints as rubbish, so map the
   likely offenders to safe equivalents and drop anything still unrepresentable. */
const SAFE_MAP={"\u2264":"<=","\u2265":">=","\u03A8":"psi","\u03C8":"psi","\u00B1":"+/-","\u00D7":"x",
  "\u00F7":"/","\u2192":"->","\u2248":"~","\u2260":"!=","\u2212":"-","\u2013":"-","\u2012":"-",
  "\u00BD":"1/2","\u00BC":"1/4","\u00BE":"3/4","\u00D8":"dia.","\u2300":"dia.","\u2205":"dia.",
  "\u2022":"-","\u00A0":" ","\u03BB":"lambda ","\u03C0":"pi","\u03C8":"psi","\u0394":"delta","\u2080":"0","\u00B7":"."};
const SAFE_KEEP=/[\u2018\u2019\u201C\u201D\u2014\u2026\u20AC\u2122\u0152\u0153\u0160\u0161\u017D\u017E\u0178\u0192\u02C6\u02DC\u2020\u2021\u2030\u2039\u203A\u201A\u201E]/;
function safe(t){
  return String(t==null?"":t)
    .replace(/[\u2264\u2265\u03A8\u03C8\u00B1\u00D7\u00F7\u2192\u2248\u2260\u2212\u2013\u2012\u00BD\u00BC\u00BE\u00D8\u2300\u2205\u2022\u00A0\u03BB\u03C0\u0394\u2080]/g, c=>SAFE_MAP[c])
    .split("").filter(c=>{ const n=c.charCodeAt(0);
      return n<0x100 || SAFE_KEEP.test(c); }).join("");
}

function buildPdf(){
  const {jsPDF}=window.jspdf;
  const doc=new jsPDF({unit:"mm",format:"a4"});
  const L=22,R=18,W=210-L-R,BOT=280;
  const d=S.data,r=refs(),sel=orderedSel();
  const today=new Date().toLocaleDateString("en-GB",{day:"numeric",month:"long",year:"numeric"});
  const ORANGE=[232,133,12],DARK=[34,38,42],MUTED=[113,118,122],RULE=[220,216,210];
  let y=0,page=1;
  const foot=()=>{ doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.line(L,286,210-R,286);
    doc.setFont("helvetica","normal");doc.setFontSize(7.5);doc.setTextColor(...MUTED);
    doc.text(PRACTICE.name+"  ·  "+PRACTICE.email,L,290);
    doc.text("Page "+page,210-R,290,{align:"right"}); };
  const head=()=>{ doc.setFont("helvetica","normal");doc.setFontSize(7.5);doc.setTextColor(...MUTED);
    doc.text(safe(spec().name+" \u2014 Building Regulations Specification"),L,13);
    doc.text(safe((d.job||"")+"  |  Rev "+(d.rev||"P01")),210-R,13,{align:"right"});
    doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.line(L,15.5,210-R,15.5); };
  const newPage=()=>{ foot();doc.addPage();page++;head();y=24; };
  const need=h=>{ if(y+h>BOT) newPage(); };
  const para=(t,size=9,gap=2.4,color=DARK,style="normal")=>{
    doc.setFont("helvetica",style);doc.setFontSize(size);doc.setTextColor(...color);
    doc.splitTextToSize(safe(t),W).forEach(ln=>{ need(5);doc.text(ln,L,y);y+=size*0.42+1.1; }); y+=gap; };

  try{ doc.addImage(LOGO_PDF,"JPEG",L,20,29,32.5); }catch(e){}
  doc.setFont("helvetica","normal");doc.setFontSize(8);doc.setTextColor(...MUTED);
  doc.text(PRACTICE.addr+"  ·  "+PRACTICE.email,L,58.5);
  doc.setDrawColor(...ORANGE);doc.setLineWidth(1.1);doc.line(L,61.5,210-R,61.5);
  doc.setFont("helvetica","bold");doc.setFontSize(28);doc.setTextColor(...DARK);
  doc.text("BUILDING REGULATIONS",L,78);
  doc.setTextColor(...ORANGE);doc.text("SPECIFICATION",L,90);
  doc.setFontSize(11);doc.setTextColor(...MUTED);
  doc.text(safe((spec().name+" \u2014 "+spec().region).toUpperCase()),L,100);
  const rows=[["Project",d.project],["Site address",d.address],["Client",d.client],["Job number",d.job],
    ["Local authority",d.la],["Application","Full Plans Application"],
    ["Prepared by","Salman Yousaf, "+PRACTICE.name],["Date",today],["Revision",d.rev||"P01"]];
  y=114;
  rows.forEach(([k,v])=>{
    doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.setFillColor(251,250,248);
    doc.rect(L,y-5,42,7.6,"FD");doc.rect(L+42,y-5,W-42,7.6,"D");
    doc.setFont("helvetica","bold");doc.setFontSize(8);doc.setTextColor(...DARK);doc.text(safe(k),L+2.5,y);
    doc.setFont("helvetica","normal");doc.setFontSize(8.5);
    doc.text(doc.splitTextToSize(safe(v||"\u2014"),W-46)[0],L+44.5,y); y+=7.6; });
  y+=10;
  doc.setDrawColor(...ORANGE);doc.setLineWidth(.8);doc.line(L,y,L+3,y);
  doc.setFont("helvetica","bold");doc.setFontSize(9);doc.setTextColor(...ORANGE);
  doc.text("ISSUED FOR BUILDING CONTROL APPROVAL",L+6,y+1); y+=7;
  para("To be read with the SY Design Studio Ltd drawing pack, the structural engineer's design and calculations, "+
       "and any specialist sub-contractor design. All work to comply with the Building Regulations 2010 (as "+
       "amended) and the Approved Documents current at the date of issue.",8,2,MUTED);
  foot();doc.addPage();page++;head();y=24;

  const secHead=(num,txt)=>{ need(16);y+=4;
    doc.setFont("helvetica","bold");doc.setFontSize(13);doc.setTextColor(...ORANGE);doc.text(num,L,y);
    doc.setTextColor(...DARK);doc.text(safe(txt.toUpperCase()),L+13,y);
    y+=2.5;doc.setDrawColor(...ORANGE);doc.setLineWidth(.7);doc.line(L,y,210-R,y);y+=6; };
  const grpLabel=t=>{ need(10);y+=3;doc.setFont("helvetica","bold");doc.setFontSize(8);
    doc.setTextColor(...MUTED);doc.text(safe(t.toUpperCase()),L,y);y+=5; };
  const entry=(tag,title)=>{ need(13);y+=3.5;
    doc.setFont("helvetica","bold");doc.setFontSize(9.5);
    if(tag){doc.setTextColor(...ORANGE);doc.text(tag,L,y);}
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
      doc.setFont("helvetica","bold");doc.setFontSize(8);doc.setTextColor(...ORANGE);doc.text(r[i],L+2,y);
      doc.setFont("helvetica","normal");doc.setTextColor(...DARK);
      tl.forEach((ln,k)=>doc.text(ln,L+cw[0]+2,y+k*3.6));
      doc.text(safe(b.u||"\u2014"),L+cw[0]+cw[1]+2,y); y+=rh; });
    y+=4;
    secHead("2.0","Part A — Construction build-ups");
    let lg=null;
    sel.forEach(i=>{ const b=allBU()[i];
      if(b.g!==lg){lg=b.g;grpLabel(GROUPS[b.g]||b.g);}
      entry(r[i],b.t);
      if(b.tgt) para(b.tgt,9,2.2,ORANGE,"bold");
      b.p.forEach(t=>para(t, t.startsWith("NOTE")?8:9, 2.4, t.startsWith("NOTE")?MUTED:DARK)); });
  } else para("No build-ups selected.",9,3,MUTED);

  const ns=noteSections();
  if(ns.size){ secHead("3.0","Part B \u2014 General specification notes");
    let sub=0;
    ns.forEach((items,s)=>{ sub++; grpLabel("3."+sub+"   "+s);
      items.forEach(it=>{ entry("",it.t); it.p.forEach(t=>para(t, t.startsWith("NOTE")?8:9, 2.4, t.startsWith("NOTE")?MUTED:DARK)); }); }); }
  const calcs=sel.map(i=>({i,b:allBU()[i]})).filter(x=>x.b.calc);
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
      doc.text("LAYER",L+1.5,y);doc.text("MM",L+cw[0]+cw[1]-2,y,{align:"right"});doc.text("R  m\u00B2K/W",L+cw[0]+cw[1]+cw[2]-2,y,{align:"right"});
      y+=1.5;doc.setDrawColor(...RULE);doc.setLineWidth(.2);doc.line(L,y,L+cw[0]+cw[1]+cw[2],y);y+=4.2;
      res.layers.forEach(l=>row(l.n, l.d!=null?String(l.d):"\u2014", l.R.toFixed(3)));
      doc.setDrawColor(...RULE);doc.line(L,y-3,L+cw[0]+cw[1]+cw[2],y-3);
      if(res.steps){ res.steps.forEach(([a,bb],k)=>row(a,"",bb,k===res.steps.length-1)); }
      else {
        row("RT upper / lower limit","",res.RT_upper.toFixed(3)+" / "+res.RT_lower.toFixed(3));
        row("RT (mean)","",res.RT.toFixed(3),true);
        row("U0 = 1 / RT","",res.U0.toFixed(3),true);
        if(res.dUg) row("dUg  air gaps (Annex F)","","+"+res.dUg.toFixed(3));
        if(res.dUf) row("dUf  fasteners (Annex F)","","+"+res.dUf.toFixed(3));
        row("U","",res.U.toFixed(3)+"  ->  "+res.U.toFixed(2)+" W/m\u00B2K",true);
      }
      para("Sources: "+res.src.join(" \u00B7 "),7.5,3,MUTED);
    });
  }
  need(24);y+=4;
  doc.setDrawColor(...ORANGE);doc.setLineWidth(.8);doc.line(L,y,L+3,y);
  doc.setFont("helvetica","bold");doc.setFontSize(8.5);doc.setTextColor(...ORANGE);
  doc.text("VERIFY BEFORE ISSUE",L+6,y+1);y+=6;
  para("Approved Documents L1 and F1, 2026 editions, come into force on 24 March 2027. Work with a full plans "+
       "application submitted before that date remains under the current standards provided work commences "+
       "before 24 March 2028. Confirm all clause and table references against the edition in force at the date "+
       "of submission.",8,2,MUTED);
  foot();
  return doc;
}

/* ---------------- actions ---------------- */
let downloads=null, db=null;
function toast(m){ const t=document.createElement("div");t.className="toast";t.textContent=m;
  document.body.appendChild(t);setTimeout(()=>t.remove(),3200); }

async function makePdf(){
  const btns=[el("btnPdf"),el("finish")].filter(Boolean);
  btns.forEach(b=>{b.disabled=true;b.dataset.l=b.textContent;b.textContent="Generating…";});
  try{
    const blob=buildPdf().output("blob");
    const fn=`${(S.data.job||"spec").replace(/[^\w-]/g,"")}_${spec().name.replace(/\s+/g,"_")}_Spec_${S.data.rev||"P01"}.pdf`;
    if(downloads){
      try{ await downloads.save({filename:fn,data:blob}); toast("PDF saved"); }
      catch(e){ toast(e&&e.code==="declined"?"Download declined":"Could not save the PDF"); }
    } else {
      const u=URL.createObjectURL(blob), a=document.createElement("a");
      a.href=u; a.download=fn; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(()=>URL.revokeObjectURL(u),4000);
      toast("PDF downloaded");
    }
  }catch(e){ toast("Something went wrong building the PDF"); console.error(e); }
  btns.forEach(b=>{b.disabled=false;b.textContent=b.dataset.l;});
}

function snapshot(){ return {type:S.type,data:{...S.data},sel:[...S.sel],notes:{...S.notes},step:S.step,custom:S.custom||[],cfg:S.cfg||null,cfgF:S.cfgF||null,cfgR:S.cfgR||null,at:Date.now()}; }
function save(){ try{ localStorage.setItem("syds-spec-draft",JSON.stringify(snapshot())); }catch(e){} }
function restore(){
  try{ const j=JSON.parse(localStorage.getItem("syds-spec-draft")||"null");
    if(j&&j.type&&SPECS[j.type]){ S.type=j.type;S.data=j.data;S.sel=j.sel;S.notes=j.notes;S.step=j.step||0;S.custom=j.custom||[];S.cfg=j.cfg||null;S.cfgF=j.cfgF||null;S.cfgR=j.cfgR||null; return true; }
  }catch(e){} return false;
}

el("btnPdf").onclick=makePdf;
el("btnType").onclick=()=>showChooser();
el("closeChooser").onclick=()=>{ if(S.type) el("chooser").hidden=true; };
el("btnSave").onclick=async()=>{
  if(!db){ toast("Saved jobs need the database capability — your draft is kept in this browser"); return; }
  const id=(S.data.job||"job").replace(/[^\w-]/g,"")+"-"+S.type;
  try{ await db.doc("jobs/"+id).set({...snapshot(),label:(S.data.job||"—")+" "+(S.data.address||"")});
       toast("Job saved"); loadJobs(); }catch(e){ toast("Could not save the job"); }
};
async function loadJobs(){
  if(!db) return;
  try{
    const snap=await db.collection("jobs").limit(40).get();
    const docs=(snap&&(snap.docs||snap))||[];
    const list=docs.map(x=>x.data?{id:x.id,...x.data()}:x).filter(Boolean);
    if(!list.length){ el("jobsWrap").hidden=true; return; }
    el("jobsWrap").hidden=false;
    el("jobs").innerHTML=list.map(j=>`<div class="job"><b>${esc((j.data&&j.data.job)||j.id)}</b>
      <span class="n">${esc(j.label||"")}</span>
      <button data-id="${esc(j.id)}" data-a="load">Load</button>
      <button data-id="${esc(j.id)}" data-a="del">Delete</button></div>`).join("");
    el("jobs").querySelectorAll("button").forEach(btn=>btn.onclick=async()=>{
      const j=list.find(x=>x.id===btn.dataset.id); if(!j) return;
      if(btn.dataset.a==="load"){ S.type=j.type;S.data={...j.data};S.sel=[...j.sel];S.notes={...j.notes};S.step=j.step||0;S.custom=j.custom||[];S.cfg=j.cfg||null;
        el("chooser").hidden=true; renderAll(); save(); toast("Job loaded"); }
      else { try{ await db.doc("jobs/"+j.id).delete(); loadJobs(); toast("Job deleted"); }catch(e){ toast("Could not delete"); } }
    });
  }catch(e){ el("jobsWrap").hidden=true; }
}
el("btnPrev").onclick=()=>{ document.body.classList.toggle("showprev");
  el("btnPrev").textContent = document.body.classList.contains("showprev") ? "Hide preview" : "Preview"; };

el("brandLogo").src=LOGO; el("brandLogoD").src=LOGO_DARK;
if(restore()){ renderAll(); } else { showChooser(); }
(async()=>{
  if(!window.claude||!claude.use) return;
  try{ downloads=await claude.use("downloads"); }catch(e){}
  try{ db=await claude.use("db"); if(db) loadJobs(); }catch(e){}
})();
