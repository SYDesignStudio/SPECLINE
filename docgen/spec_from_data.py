"""Generate the Word/PDF specification for one project type straight from the app
library (specdata.js) — single source of truth.

Usage: python3 spec_from_data.py <typekey> [<typekey> ...]   e.g. extension loft flat

Whose document it is comes from docgen/practice.py, never from here: the cover, the
address line, the accent colour, the logo and the 'Prepared By' line are all the
subscribing practice's. Set SPECLINE_PRACTICE to a profile, or drop
specline-practice.json in the directory above the repository. With no profile the
cover prints placeholders, which is the safe failure.
"""
import sys, json, subprocess, os, re, shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from build_spec import *
from brand import _rule, _shade, _field
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECDATA=os.path.join(ROOT,'dist','specdata.js').replace('\\','/')
OUT=os.path.join(ROOT,'output')
os.makedirs(OUT,exist_ok=True)

def _soffice():
    """LibreOffice, for the .docx -> .pdf step.

    The Windows installer does not add itself to PATH, so look in the usual
    install locations as well. Returns None when it is not installed; the
    caller then writes the Word file and skips the PDF.
    """
    found = shutil.which('soffice') or shutil.which('soffice.exe')
    if found: return found
    for p in [os.path.join(os.environ.get('PROGRAMFILES',r'C:\Program Files'),'LibreOffice','program','soffice.exe'),
              os.path.join(os.environ.get('PROGRAMFILES(X86)',r'C:\Program Files (x86)'),'LibreOffice','program','soffice.exe'),
              os.path.join(os.environ.get('LOCALAPPDATA',''),'Programs','LibreOffice','program','soffice.exe'),
              '/usr/bin/soffice','/usr/local/bin/soffice',
              '/Applications/LibreOffice.app/Contents/MacOS/soffice']:
        if p and os.path.exists(p): return p
    return None

SOFFICE=_soffice()

def load():
    js=f'const fs=require("fs");eval(fs.readFileSync("{SPECDATA}","utf8")+";globalThis.SPECS=SPECS");process.stdout.write(JSON.stringify(SPECS))'
    return json.loads(subprocess.check_output(['node','-e',js]).decode())

BUILDUPS=[]
def bu(d, ref, title, uval):
    BUILDUPS.append((ref,title,uval))
    p=d.add_paragraph(); p.paragraph_format.space_before=Pt(14); p.paragraph_format.space_after=Pt(2)
    p.paragraph_format.keep_with_next=True
    r=p.add_run(ref); r.font.size=Pt(11); r.font.bold=True; r.font.color.rgb=ACCENT
    r=p.add_run("   "+title.upper()); r.font.size=Pt(10.5); r.font.bold=True; r.font.color.rgb=DARK
    _rule(p,"E8EAEB",6)
def gn(d, title):
    p=d.add_paragraph(); p.paragraph_format.space_before=Pt(13); p.paragraph_format.space_after=Pt(2)
    p.paragraph_format.keep_with_next=True
    r=p.add_run("* "); r.font.size=Pt(10.5); r.font.bold=True; r.font.color.rgb=ACCENT
    r=p.add_run(title.upper()); r.font.size=Pt(10); r.font.bold=True; r.font.color.rgb=DARK
def tgt(d,t):
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(4); p.paragraph_format.keep_with_next=True
    r=p.add_run(t); r.font.size=Pt(9.5); r.font.bold=True; r.font.color.rgb=ACCENT
def sp(d,t):
    p=d.add_paragraph(); p.paragraph_format.space_after=Pt(4)
    r=p.add_run(t); r.font.size=Pt(9.5)
def note(d,t):
    p=d.add_paragraph(); p.paragraph_format.space_before=Pt(5); p.paragraph_format.space_after=Pt(7)
    p.paragraph_format.left_indent=Mm(6)
    r=p.add_run("NOTE  "); r.font.size=Pt(8); r.font.bold=True; r.font.color.rgb=ACCENT
    r=p.add_run(t); r.font.size=Pt(8.4); r.font.color.rgb=MID
    _rule(p, None,6)
def para(d,t):
    if t.startswith("NOTE — "): note(d,t[7:])
    elif t.startswith("NOTE - "): note(d,t[7:])
    else: sp(d,t)

def build(key, S):
    BUILDUPS.clear()
    T=S[key]
    meta=dict(type=f"{T['name']} ({T.get('region','England')})", project="[PROJECT DESCRIPTION]",
      address="[SITE ADDRESS]", client="[CLIENT NAME]", job="[JOB NUMBER]", la="[LOCAL AUTHORITY]",
      application="Full Plans Application",
      date="September 2026", rev="P01")
    # No author and no logo path: cover() takes both from the practice profile. Naming a
    # designer here put one practice's director on every practice's specification.
    d=new_doc(); headers(d,meta); cover(d,meta)

    h1(d,"How to Use This Specification","1.0")
    sp(d,"This specification is in two parts.")
    sp(d,"PART A — CONSTRUCTION BUILD-UPS. Each build-up carries a reference of the form EW1, GF1, RF1. "
         "These are allocated per job, in the order the build-ups appear on the drawings: the first "
         "external wall type on the job is EW1, the second EW2, and so on. Select the build-ups used on "
         "the project, delete those that are not, and renumber in drawing order. Tag the same reference "
         "against the element on the wall plan, floor plan and section.")
    sp(d,"PART B — GENERAL SPECIFICATION NOTES. Everything that is not a build-up: site preparation, "
         "foundations, structure, fire, ventilation, drainage, services and the rest. These are not "
         "keyed, because they apply generally rather than to a tagged element. They are arranged by "
         "topic to match the order a Building Control Officer reads a pack.")
    sp(d,"The build-up schedule overleaf is intended to be reproduced as a legend on the drawing sheet. "
         "U-values quoted against build-ups are calculated to BS EN ISO 6946 / BS EN ISO 13370 with BR 443 "
         "conventions using manufacturers' declared thermal conductivities verified at the date of issue; "
         "confirm against the product datasheet current at the time of ordering.")

    d.add_page_break()
    h1(d,"Construction Build-Up Schedule","2.0")
    ANCHOR=d.add_paragraph()

    # ---- PART A, grouped by category in cats order, numbered per group in library order
    h1(d,"Part A — Construction Build-Ups","3.0")
    counters={}
    for cat in T['cats']:
        items=[b for b in T['buildups'] if b['c']==cat]
        if not items: continue
        gn(d,cat)
        for b in items:
            counters[b['g']]=counters.get(b['g'],0)+1
            ref=f"{b['g']}{counters[b['g']]}"
            bu(d,ref,b['t'],b.get('u',''))
            if b.get('tgt'): tgt(d,b['tgt'])
            for t in b['p']: para(d,t)

    # ---- PART B, categories become numbered sections from 4.0
    d.add_page_break()
    h1(d,"Part B — General Specification Notes","4.0")
    n=4
    first=True
    for cat in T['cats']:
        items=[x for x in T['notes'] if x['c']==cat]
        if not items: continue
        if not first:
            n+=1; h1(d,cat,f"{n}.0")
        first=False
        for x in items:
            gn(d,x['t'])
            for t in x['p']: para(d,t)

    # ---- schedule table
    rows=[("Ref","Build-Up","U-value")]+[(r,t,u if u else "—") for r,t,u in BUILDUPS]
    tbl=d.add_table(rows=len(rows),cols=3); tbl.style='Table Grid'; tbl.autofit=False
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=tbl.rows[i].cells[j]; c.width=Mm([20,118,32][j])
            pp=c.paragraphs[0]; pp.paragraph_format.space_after=Pt(2); pp.paragraph_format.space_before=Pt(2)
            rr=pp.add_run(str(v)); rr.font.size=Pt(9)
            if i==0: rr.font.bold=True; rr.font.color.rgb=DARK; _shade(c,LIGHT)
            elif j==0: rr.font.bold=True; rr.font.color.rgb=ACCENT
    ANCHOR._p.addnext(tbl._tbl)

    # Neutral filename: a subscriber's file should not arrive prefixed with another
    # practice's initials. The practice is named inside the document, on the cover.
    fn=f"SPEC_{T['name'].replace(' ','_')}_{T.get('region','England')}.docx"
    path=os.path.join(OUT,fn); d.save(path)
    if SOFFICE:
        subprocess.run([SOFFICE,'--headless','--convert-to','pdf','--outdir',OUT,path],check=True,capture_output=True)
    else:
        print('WARNING: LibreOffice not found - .docx written, PDF skipped',file=sys.stderr)
    print(key,"->",fn,"build-ups:",len(BUILDUPS),"notes:",len(T['notes']))
    return path

if __name__=="__main__":
    S=load()
    for k in (sys.argv[1:] or [k for k in S]):
        build(k,S)
