import sys, os, json, datetime
sys.path.insert(0, '/home/claude/syds')
from brand import *
from brand import _rule, _shade, _field

def cover(d, meta, logo=None):
    # ---- logo / wordmark block
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(2)
    logo = logo or LOGO
    if logo and os.path.exists(logo):
        p.add_run().add_picture(logo, width=Mm(33))
    else:
        # No logo: set the practice's own name as the wordmark. It used to read
        # "SY DESIGN STUDIO" whoever the document was for.
        words = PRACTICE["name"].split()
        head = words[0] if words else PRACTICE["name"]
        rest = " " + " ".join(words[1:]) if len(words) > 1 else ""
        r = p.add_run(head); r.font.size = Pt(28); r.font.bold = True; r.font.color.rgb = DARK
        if rest:
            r2 = p.add_run(rest.upper()); r2.font.size = Pt(16); r2.font.bold = True
            r2.font.color.rgb = ACCENT
    p2 = d.add_paragraph(); p2.paragraph_format.space_after = Pt(26); p2.paragraph_format.space_before = Pt(8)
    r = p2.add_run(f"{PRACTICE['addr']}  ·  {PRACTICE['email']}")
    r.font.size = Pt(8); r.font.color.rgb = MID
    _rule(p2, None, 18)

    # ---- title block
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(0)
    r = p.add_run("BUILDING REGULATIONS"); r.font.size = Pt(30); r.font.bold = True; r.font.color.rgb = DARK
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(6)
    r = p.add_run("SPECIFICATION"); r.font.size = Pt(30); r.font.bold = True; r.font.color.rgb = ACCENT
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(30)
    r = p.add_run(meta['type'].upper()); r.font.size = Pt(13); r.font.color.rgb = MID
    r.font.bold = True
    # letter-spacing effect
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(8)

    # ---- project data table
    rows = [("Project",       meta.get('project','')),
            ("Site Address",  meta.get('address','')),
            ("Client",        meta.get('client','')),
            ("Job Number",    meta.get('job','')),
            ("Local Authority", meta.get('la','')),
            ("Application",   meta.get('application','Full Plans / Building Notice')),
            ("Prepared By",   meta.get('author', f"{PRACTICE.get('designer','')}, {PRACTICE['name']}".strip(', '))),
            ("Date",          meta.get('date','')),
            ("Revision",      meta.get('rev','P01'))]
    t = d.add_table(rows=len(rows), cols=2); t.style = 'Table Grid'
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i,(k,v) in enumerate(rows):
        c0, c1 = t.rows[i].cells
        c0.width = Mm(42); c1.width = Mm(128)
        _shade(c0, LIGHT)
        pk = c0.paragraphs[0]; rk = pk.add_run(k)
        rk.font.bold = True; rk.font.size = Pt(9); rk.font.color.rgb = DARK
        pv = c1.paragraphs[0]; rv = pv.add_run(v if v else "—")
        rv.font.size = Pt(9)
        for c in (c0,c1):
            c.paragraphs[0].paragraph_format.space_after = Pt(2)
            c.paragraphs[0].paragraph_format.space_before = Pt(2)

    # ---- status note
    d.add_paragraph()
    p = d.add_paragraph(); p.paragraph_format.space_before = Pt(14)
    _rule(p, "D9DCDD", 8)
    p = d.add_paragraph()
    r = p.add_run("ISSUED FOR BUILDING CONTROL APPROVAL")
    r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = ACCENT
    p = d.add_paragraph()
    r = p.add_run(f"This specification is to be read in conjunction with the {PRACTICE['name']} drawing "
                  "pack listed overleaf, the structural engineer's design and calculations, and any "
                  "specialist sub-contractor design. All work to comply with the Building Regulations "
                  "2010 (as amended) and the relevant Approved Documents current at the date of issue.")
    r.font.size = Pt(8.5); r.font.color.rgb = MID
    # The responsibility statement, in the practice's voice. The software drafts; building control approves.
    who = f"{PRACTICE['designer']} of {PRACTICE['name']}" if PRACTICE.get('designer') else PRACTICE['name']
    p = d.add_paragraph(); p.paragraph_format.space_before = Pt(4)
    r = p.add_run(f"{who} is the named designer and remains responsible for the suitability of this "
                  "specification for this project. Every clause and table reference is to be confirmed "
                  "against the Approved Documents in force at the date of submission. Compliance of the "
                  "work is determined by the building control body; this document is the designer's "
                  "specification of the work, not an approval of it.")
    r.font.size = Pt(8.5); r.font.color.rgb = MID

    d.add_page_break()

def headers(d, meta):
    sec = d.sections[0]
    sec.different_first_page_header_footer = True
    # body header
    h = sec.header.paragraphs[0]
    h.text = ""
    r = h.add_run(f"{meta['type']} — Building Regulations Specification")
    r.font.size = Pt(8); r.font.color.rgb = MID
    h.add_run("\t\t")
    r = h.add_run(f"{meta.get('job','')}  |  Rev {meta.get('rev','P01')}")
    r.font.size = Pt(8); r.font.color.rgb = MID
    _rule(h, "D9DCDD", 6)
    # body footer
    f = sec.footer.paragraphs[0]; f.text = ""
    r = f.add_run(f"{PRACTICE['name']}  ·  {PRACTICE['email']}")
    r.font.size = Pt(7.5); r.font.color.rgb = MID
    f.add_run("\t\t")
    r = f.add_run("Page "); r.font.size = Pt(7.5); r.font.color.rgb = MID
    _field(f, " PAGE ")
    r = f.add_run(" of "); r.font.size = Pt(7.5); r.font.color.rgb = MID
    _field(f, " NUMPAGES ")

def h1(d, text, num=None):
    p = d.add_paragraph()
    p.paragraph_format.space_before = Pt(16); p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    if num:
        r = p.add_run(f"{num}  "); r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = ACCENT
    r = p.add_run(text.upper()); r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = DARK
    _rule(p, None, 10)

def h2(d, text):
    p = d.add_paragraph()
    p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = DARK
    return p

def clause(d, ref, text):
    p = d.add_paragraph()
    p.paragraph_format.left_indent = Mm(14)
    p.paragraph_format.first_line_indent = Mm(-14)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run(f"{ref}\t"); r.font.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = ACCENT
    r = p.add_run(text); r.font.size = Pt(9.5)
    return p
