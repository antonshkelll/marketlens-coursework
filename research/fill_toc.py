"""Materialize a readable TOC from page numbers verified in the native PDF."""
from pathlib import Path
import json,re
from docx import Document
from docx.shared import Pt,Cm
from docx.enum.text import WD_TAB_ALIGNMENT,WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
BASE=Path(__file__).parent

def fill(path):
 doc=Document(path);cache=json.loads((BASE/'toc_pages.json').read_text(encoding='utf-8')) if (BASE/'toc_pages.json').exists() else {}
 for p in list(doc.paragraphs):
  if p.style.name=='TOC Entry':p._element.getparent().remove(p._element)
 heads=[(p.text,p.style.name=='Heading 2') for p in doc.paragraphs if p.style.name in ('Heading 1','Heading 2')]
 if 'TOC Entry' not in doc.styles:doc.styles.add_style('TOC Entry',1)
 st=doc.styles['TOC Entry'];st.base_style=doc.styles['Normal'];st.font.name='Times New Roman';st.font.size=Pt(14)
 fmt=st.paragraph_format;fmt.first_line_indent=Cm(0);fmt.line_spacing=1;fmt.space_before=Pt(0);fmt.space_after=Pt(5);fmt.tab_stops.add_tab_stop(Cm(17),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
 target=next(p for p in doc.paragraphs if p.text=='СОДЕРЖАНИЕ')
 for p in list(doc.paragraphs):
  if p._element.xpath('.//w:fldSimple') and 'TOC ' in ''.join(p._element.xpath('.//w:fldSimple/@w:instr')):p._element.getparent().remove(p._element)
 for text,sub in heads:
  element=OxmlElement('w:p');target._p.addnext(element);q=Paragraph(element,target._parent);q.style='TOC Entry';q.paragraph_format.left_indent=Cm(.45 if sub else 0)
  q.add_run(text+'\t'+str(cache.get(text,'?')));target=q
 doc.save(path)
if __name__=='__main__':
 import sys
 fill(sys.argv[1])
