/* ===== Three more calculations, added 8 September 2026 so that every insulated library
   build-up can be re-run when the practice chooses a different insulation manufacturer =====

   - roofOverRafter: insulation between AND over the rafters (the sarking-board warm roof).
     CLAUDE.md had this on the backlog: it was checked by hand against roofRafter's own
     conventions, and this is the same arithmetic written down — Rse 0.10 for the ventilated
     batten space above the sarking board, 47/spacing bridging of the between-rafter layer,
     the Annex F gap correction scaled by (R insulation / R total)².
   - lined: an existing masonry wall with an internal lining — insulated plasterboard on
     dabs, or an insulated stud lining. BS EN ISO 6946, combined method across the studs.
   - roofFlat gains a concrete deck option, and basement() accepts a product object for the
     floor or the wall board so a product outside floorIns can be run through it. */

Object.assign(UC, {

  /* Existing walls a lining is applied to. Conductivities are BR 443 typical values. */
  lined_walls:[
   {id:"brick215", n:"215mm solid brick wall", layers:[{n:"215mm solid brickwork",d:215,k:0.77}], src:"BR 443 typical (brickwork)"},
   {id:"cavity",   n:"uninsulated cavity wall (103 brick, 50 cavity, 100 dense block)",
    layers:[{n:"103mm brick outer leaf",d:103,k:0.77},{n:"50mm clear cavity",gap:50},{n:"100mm dense block inner leaf",d:100,k:1.13}], src:"BR 443 typical"},
   {id:"block100", n:"100mm single-leaf dense block wall", layers:[{n:"100mm dense blockwork",d:100,k:1.13}], src:"BR 443 typical"}],

  /* p: {wall, internalBoth, gap, lining (underIns id), insulation (frameIns id), thickness,
         studWidth, studDepth, spacing, gapLevel} */
  lined(p){
    const wall = this.lined_walls.find(x=>x.id===p.wall) || this.lined_walls[0];
    const lin  = this.underIns.find(x=>x.id===(p.lining||"none")) || this.underIns[0];
    const Rse  = p.internalBoth ? this.Rsi_wall : this.Rse_wall;
    const layers=[{n:p.internalBoth?"Surface to the adjoining unheated space (treated as internal, 0.13)":"External surface (Rse)",R:Rse}];
    wall.layers.forEach(l=>layers.push(l.gap?{n:l.n,d:l.gap,R:this.airGap(l.gap)}:{n:l.n,d:l.d,R:l.d/1000/l.k}));
    const gap = p.gap==null ? 10 : p.gap;
    if(gap>0) layers.push({n:`${gap}mm ${p.insulation?"clear gap behind the studs":"dab air gap"} (unventilated)`,d:gap,R:this.airGap(gap)});
    let f=0, Rins=0, Rtim=0, Rbr=0;
    if(p.insulation){
      const ins=this.frameIns.find(x=>x.id===p.insulation)||this.frameIns[0];
      const sw=p.studWidth||38, sd=p.studDepth||89, sp=p.spacing||600, t=Math.min(p.thickness||sd, sd);
      f=sw/sp; Rins=t/1000/ins.k; Rtim=t/1000/this.timber; Rbr=1/((1-f)/Rins+f/Rtim);
      layers.push({n:`${t}mm ${ins.n} between ${sw} × ${sd} studs at ${sp}mm centres (λ ${ins.k}; timber ${(f*100).toFixed(1)}%)`,d:t,R:Rbr,ins:true,bridged:true,Rb:Rins,Rm:Rtim,fb:1-f,fm:f});
      if(t<sd) layers.push({n:`${sd-t}mm unfilled stud depth (unventilated cavity)`,d:sd-t,R:this.airGap(sd-t)});
    }
    if(lin.t>0) layers.push({n:`${lin.t}mm insulation in the lining (${lin.n.split(" (")[0]}, λ ${lin.k})`,d:lin.t,R:lin.t/1000/lin.k,ins:!p.insulation});
    layers.push({n:`${lin.pb}mm plasterboard`,d:lin.pb,R:lin.pb/1000/0.21});
    layers.push({n:"Internal surface (Rsi)",R:this.Rsi_wall});
    const others=layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R,0);
    let RT_lower, RT_upper;
    if(p.insulation){ RT_lower=others+Rbr; RT_upper=1/((1-f)/(others+Rins)+f/(others+Rtim)); }
    else { RT_lower=RT_upper=others; }
    const RT=(RT_upper+RT_lower)/2, U0=1/RT;
    const lvl=this.gapLevel.find(x=>x.id===(p.gapLevel==null?0:p.gapLevel));
    const Rall=(p.insulation?Rins:0)+(lin.t?lin.t/1000/lin.k:0);
    const dUg=lvl.dU*Math.pow(Rall/RT,2);
    const U=U0+dUg;
    const notes=[];
    if(p.wall==="brick215"||p.wall==="block100") notes.push("Internal insulation moves the dew point into the existing masonry: a condensation risk analysis to BS 5250 is to be carried out.");
    return {kind:"lined",U,U0,dUg,dUf:0,RT,RT_upper,RT_lower,layers,notes,
            src:[wall.src, lin.src||"BR 443", p.insulation?(this.frameIns.find(x=>x.id===p.insulation)||{}).src:null, lvl.n].filter(Boolean)};
  },

  /* Pitched roof, insulation between AND over the rafters, ventilated batten space above the
     sarking board. p: {insulation (rafterIns id), thickness (between), over, rafterDepth,
     spacing, pb, gapLevel} */
  roofOverRafter(p){
    const ins=this.rafterIns.find(x=>x.id===p.insulation), rd=p.rafterDepth||150, sp=p.spacing||400, f=47/sp;
    const tb=Math.min(p.thickness,rd), to=p.over||0, pb=p.pb==null?12.5:p.pb;
    const layers=[{n:"External surface — ventilated batten space above the sarking board (Rse taken as 0.10)",R:0.10}];
    if(to>0) layers.push({n:`${to}mm ${ins.n} over the rafters, continuous (λ ${ins.k})`,d:to,R:to/1000/ins.k,ins2:true});
    const Rins=tb/1000/ins.k, Rtim=tb/1000/this.timber, Rbr=1/((1-f)/Rins+f/Rtim);
    layers.push({n:`${tb}mm ${ins.n} between 47×${rd} rafters at ${sp} (λ ${ins.k}; bridging ${(f*100).toFixed(1)}%)`,d:tb,R:Rbr,ins:true,bridged:true,Rb:Rins,Rm:Rtim,fb:1-f,fm:f});
    if(tb<rd) layers.push({n:`${rd-tb}mm unfilled rafter depth (unventilated)`,d:rd-tb,R:this.airGapUp(rd-tb)});
    if(pb>0) layers.push({n:`${pb}mm plasterboard`,d:pb,R:pb/1000/0.21});
    layers.push({n:"Internal surface (Rsi, upward)",R:this.Rsi_roof});
    const others=layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R,0);
    const RT_lower=others+Rbr, RT_upper=1/((1-f)/(others+Rins)+f/(others+Rtim)), RT=(RT_upper+RT_lower)/2;
    const U0=1/RT, lvl=this.gapLevel.find(x=>x.id===(p.gapLevel==null?1:p.gapLevel));
    const dUg=lvl.dU*Math.pow((Rins+to/1000/ins.k)/RT,2);
    const U=U0+dUg;
    const notes=[]; if(p.thickness>rd) notes.push(`Insulation ${p.thickness}mm exceeds the rafter depth ${rd}mm — only ${rd}mm fits between.`);
    notes.push("The counter-batten fixings through the sarking board are structural and are to be from the board manufacturer's schedule for the pitch and exposure.");
    return {kind:"roof-over-rafter",U,U0,dUg,dUf:0,RT,RT_upper,RT_lower,layers,notes,src:[ins.src,lvl.n,"BS EN ISO 6946 (ventilated batten space above)"]};
  }
});

/* roofFlat: a concrete or metal deck in place of the timber joist void. */
UC._roofFlatTimber = UC.roofFlat;
UC.roofFlat = function(p){
  if(p.deck!=="concrete") return this._roofFlatTimber(p);
  const ins=Object.assign({},this.flatIns.find(x=>x.id===p.insulation));
  if(ins.kt) ins.k=ins.kt(p.thickness);
  const slab=p.slab||150;
  const layers=[{n:"External surface (Rse)",R:this.Rse_roof},{n:"Waterproof membrane",d:0,R:0.02},
    {n:`${p.thickness}mm ${ins.n} (λ ${ins.k}${ins.kt?" at this thickness":""})`,d:p.thickness,R:p.thickness/1000/ins.k,ins:true},
    {n:"Vapour control layer",d:0,R:0},{n:`${slab}mm concrete deck`,d:slab,R:slab/1000/1.35},
    {n:"Internal surface (Rsi, upward)",R:this.Rsi_roof}];
  const RT=layers.reduce((s,l)=>s+l.R,0), U0=1/RT, Rins=p.thickness/1000/ins.k;
  const dUf = p.fixing==="mech" ? 0.8*50*5*1.13e-5/(p.thickness/1000)*Math.pow(Rins/RT,2) : 0;
  const U=U0+dUf;
  return {kind:"roof-flat",U,U0,dUg:0,dUf,RT,RT_upper:RT,RT_lower:RT,layers,notes:[],src:[ins.src,"BR 443 (dense concrete deck)",p.fixing==="mech"?"ISO 6946 Annex F fasteners (steel, 5/m²)":"fully adhered — no fastener correction"]};
};

/* basement: accept a product object for either board, so a board outside floorIns (a cavity
   board on a block inner leaf, a framing board in a stud lining) can be run through it. */
UC._basementIds = UC.basement;
UC.basement = function(p){
  const q=Object.assign({},p);
  const fake=[];
  if(p.floorProduct){ q.floorIns="__fp"; fake.push(Object.assign({id:"__fp"},p.floorProduct)); }
  if(p.wallProduct){ q.wallIns="__wp"; fake.push(Object.assign({id:"__wp"},p.wallProduct)); }
  if(!fake.length) return this._basementIds(p);
  const saved=this.floorIns; this.floorIns=saved.concat(fake);
  try{ return this._basementIds(q); } finally{ this.floorIns=saved; }
};

/* ---- Recticel, verified from the manufacturer's product pages on 8 September 2026 (reference/FACTS.md) ---- */
UC.insulation.push({id:"ewplus", n:"Recticel Eurowall+ full fill cavity board", k:0.022, fill:"full", th:[75,90,115,140], residual:10, src:"Recticel product page (CCPI assessed) verified 08/09/2026"});
UC.floorIns.push({id:"egp",  n:"Recticel Eurothane GP", k:0.022, th:[25,30,40,50,60,70,75,80,90,100,110,120,130,140,150,160], src:"Recticel product page + BBA (underfloor) verified 08/09/2026"});
UC.rafterIns.push({id:"egpr", n:"Recticel Eurothane GP", k:0.022, th:[25,30,40,50,60,70,75,80,90,100,110,120,130,140,150,160], src:"Recticel product page verified 08/09/2026"});
UC.frameIns.push({id:"egpf", n:"Recticel Eurothane GP", k:0.022, th:[25,30,40,50,60,70,75,80,90,100,110,120,130,140,150,160], src:"Recticel product page verified 08/09/2026"});
/* Thickness lists for the roof and frame boards that are the same product as the floor board of
   that name (GA4000, XT/PR-UF, Eco-Versal), so the substitution can step through them. */
[["ga4000r","ga4000"],["xtpr","xtuf"],["ecovr","ecov"]].forEach(([r,f])=>{ const a=UC.rafterIns.find(x=>x.id===r), b=UC.floorIns.find(x=>x.id===f); if(a&&b&&!a.th) a.th=b.th.slice(); });
[["ga4000f","ga4000"],["xtprf","xtuf"],["ecovf","ecov"]].forEach(([r,f])=>{ const a=UC.frameIns.find(x=>x.id===r), b=UC.floorIns.find(x=>x.id===f); if(a&&b&&!a.th) a.th=b.th.slice(); });
