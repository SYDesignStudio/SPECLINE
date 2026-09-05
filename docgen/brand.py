# SY Design Studio Ltd - document brand kit
from docx import Document
from docx.shared import Pt, Mm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

ORANGE = RGBColor(0xF5, 0x90, 0x0A)
DARK   = RGBColor(0x3E, 0x42, 0x44)
MID    = RGBColor(0x6E, 0x74, 0x77)
LIGHT  = "E8EAEB"

PRACTICE = {
    "name":    "SY Design Studio Ltd",
    "addr":    "49 Durham Avenue, Hounslow, TW5 0HG",
    "email":   "info@sydesignstudio.co.uk",
    "web":     "www.sydesignstudio.co.uk",
}

def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)

def _rule(par, color="F5900A", size=12):
    p = par._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), str(size))
    bot.set(qn('w:space'), '4'); bot.set(qn('w:color'), color)
    pbdr.append(bot); p.append(pbdr)

def _field(par, instr):
    r = par.add_run()
    fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = instr
    fc2 = OxmlElement('w:fldChar'); fc2.set(qn('w:fldCharType'), 'end')
    r._r.append(fc); r._r.append(it); r._r.append(fc2)
    return r

def new_doc():
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Mm(210), Mm(297)
    s.top_margin, s.bottom_margin = Mm(20), Mm(18)
    s.left_margin, s.right_margin = Mm(22), Mm(18)
    st = d.styles['Normal']
    st.font.name = 'Calibri'; st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')
    pf = st.paragraph_format
    pf.space_after = Pt(4); pf.line_spacing = 1.08
    return d
