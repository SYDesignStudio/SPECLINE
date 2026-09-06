/* ===== Framed walls — timber frame panels and dormer cheeks (BS EN ISO 6946) =====

   The last fixed build-ups in the library. Same combined method as the rafter roof:
   the insulation between the studs is bridged by the timber, and a wall that looks
   right on paper can miss the target once the studs are counted.

   One thing about this calculation surprises people, so the working states it. The
   cladding — brick, tile hanging, render on a carrier board, timber boarding — sits
   outside a ventilated and drained cavity. BS EN ISO 6946 requires a well-ventilated
   air layer, and everything outside it, to be disregarded, with the external surface
   resistance taken as still air. So the outer finish changes the specification text
   and the fire and boundary checks, but it does not change the U-value at all. */

Object.assign(UC, {

  /* Between the studs. Every conductivity here is already verified elsewhere in this
     file or in reference/FACTS.md; nothing new has been introduced. */
  frameIns:[
   {id:"k112",  n:"Kingspan Kooltherm K112 Framing Board", k:0.019,
    src:"Kooltherm phenolic range verified at 0.019 on 05/09/2026; K112 is the framing board of that range and is the product the library already specifies"},
   {id:"ga4000f",n:"Celotex GA4000 (now Soprema SOPRATHERM)", k:0.022,
    src:"Soprema product pages verified 05/09/2026"},
   {id:"xtprf", n:"Unilin Thin-R XT/PR-UF (was Xtratherm XT/PR)", k:0.022,
    src:"Unilin handbook 09/2025 + BBA 23/6997 verified 05/09/2026"},
   {id:"ecovf", n:"EcoTherm Eco-Versal", k:0.022,
    src:"EcoTherm datasheet 02/2026 + BBA 24/7114 verified 05/09/2026"},
   {id:"mw35f", n:"Mineral wool slab 0.035", k:0.035, src:"BR 443 typical"}],

  /* Racking board behind the breather membrane. Softwood-based, 0.13 as BR 443. */
  sheathing:[
   {id:"osb9",  n:"9mm OSB3 sheathing",     d:9,  k:0.13, src:"BR 443 typical (softwood board)"},
   {id:"ply18", n:"18mm plywood sheathing", d:18, k:0.13, src:"BR 443 typical (softwood board)"},
   {id:"none",  n:"No sheathing board",     d:0,  k:0.13, src:"—"}],

  STUD_W:[38,47,63], STUD_D:[89,100,140,150,184,200], STUD_SP:[400,600], SERVICE_VOID:[0,25,38,50],

  /* p: {insulation, thickness, studWidth, studDepth, spacing, sheathing, lining, void, gapLevel} */
  frame(p){
    const ins    = this.frameIns.find(x=>x.id===p.insulation)  || this.frameIns[0];
    const sheath = this.sheathing.find(x=>x.id===p.sheathing)  || this.sheathing[0];
    const lin    = this.underIns.find(x=>x.id===p.lining)      || this.underIns[0];
    const sw = p.studWidth || 38, sd = p.studDepth || 140, sp = p.spacing || 600;
    const f  = sw / sp;                                  /* timber fraction, studs only */
    const t  = Math.min(p.thickness || sd, sd);

    const layers = [{n:"External surface — cladding and its ventilated cavity disregarded (BS EN ISO 6946: well-ventilated air layer; Rse taken as still air)", R:this.Rsi_wall}];
    if(sheath.d) layers.push({n:sheath.n, d:sheath.d, R:sheath.d/1000/sheath.k});

    const Rins = t/1000/ins.k, Rtim = t/1000/this.timber;
    const Rbr  = 1/((1-f)/Rins + f/Rtim);
    layers.push({n:`${t}mm ${ins.n} between ${sw} × ${sd} studs at ${sp}mm centres (λ ${ins.k}; timber ${(f*100).toFixed(1)}%)`,
                 d:t, R:Rbr, bridged:true, Rb:Rins, Rm:Rtim, fb:1-f, fm:f});
    if(t < sd) layers.push({n:`${sd-t}mm unfilled stud depth (unventilated cavity)`, d:sd-t, R:this.airGap(sd-t)});
    if(p.void > 0) layers.push({n:`${p.void}mm battened service void`, d:p.void, R:this.airGap(p.void)});
    if(lin.t > 0) layers.push({n:`${lin.t}mm insulation in the lining (${lin.n.split(" (")[0]}, λ ${lin.k})`, d:lin.t, R:lin.t/1000/lin.k});
    layers.push({n:`${lin.pb}mm plasterboard`, d:lin.pb, R:lin.pb/1000/0.21});
    layers.push({n:"Internal surface (Rsi)", R:this.Rsi_wall});

    /* combined method across the bridged layer */
    const others   = layers.filter(l=>!l.bridged).reduce((s,l)=>s+l.R, 0);
    const RT_lower = others + Rbr;
    const RT_upper = 1/((1-f)/(others+Rins) + f/(others+Rtim));
    const RT = (RT_upper + RT_lower)/2, U0 = 1/RT;

    /* Annex F air-gap correction. No fastener term: the wall ties cross the ventilated
       cavity, which is disregarded, so they do not bridge the insulation. */
    const lvl  = this.gapLevel.find(x=>x.id===(p.gapLevel==null?1:p.gapLevel));
    const Rall = Rins + (lin.t ? lin.t/1000/lin.k : 0);
    const dUg  = lvl.dU * Math.pow(Rall/RT, 2);
    const U    = U0 + dUg;

    const notes = [];
    if((p.thickness||sd) > sd)
      notes.push(`Insulation ${p.thickness}mm is deeper than the ${sd}mm studs — only ${sd}mm fits between them. Deepen the studs or add an insulated lining rather than assuming the extra thickness.`);
    if(t === sd && !p.void && lin.t === 0)
      notes.push("The insulation fills the stud depth with no service void, so every socket and switch box penetrates the vapour control layer. A battened service void on the warm side is strongly preferred.");
    if(f > 0.12)
      notes.push(`The timber fraction is ${(f*100).toFixed(1)}% at these stud centres, which is high; wider centres or a continuous insulated lining will do more than thicker insulation between the studs.`);

    return {kind:"frame", U, U0, dUg, dUf:0, RT, RT_upper, RT_lower, layers, notes,
            f, timberOnly:true,
            src:[ins.src, sheath.src, lin.src || "BR 443", lvl.n, "BS EN ISO 6946 §6.9.3 (well-ventilated air layer)"]};
  }
});
