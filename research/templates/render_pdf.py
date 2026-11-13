from pathlib import Path
from xml.sax.saxutils import escape
from docx import Document
from docx.text.paragraph import Paragraph as WParagraph
from docx.table import Table as WTable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import mm
from reportlab.lib import colors
import json

base=Path(__file__).parent; out=base.parent/'Курсовая_Шкель_Антон'
for n,f in [('TNR','times.ttf'),('TNRB','timesbd.ttf'),('TNRI','timesi.ttf')]:pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
pdfmetrics.registerFontFamily('TNR',normal='TNR',bold='TNRB',italic='TNRI',boldItalic='TNRB')
styles={
'normal':ParagraphStyle('normal',fontName='TNR',fontSize=14,leading=21,alignment=TA_JUSTIFY,firstLineIndent=12.5*mm,spaceAfter=0,allowWidows=0,allowOrphans=0),
'h1':ParagraphStyle('h1',fontName='TNRB',fontSize=14,leading=21,spaceAfter=8,keepWithNext=True,firstLineIndent=12.5*mm),
'h2':ParagraphStyle('h2',fontName='TNRB',fontSize=14,leading=21,spaceBefore=12,spaceAfter=6,keepWithNext=True,firstLineIndent=12.5*mm),
'center':ParagraphStyle('center',fontName='TNR',fontSize=14,leading=21,alignment=TA_CENTER),
'right':ParagraphStyle('right',fontName='TNR',fontSize=14,leading=17,alignment=TA_RIGHT),
'left':ParagraphStyle('left',fontName='TNR',fontSize=14,leading=21,alignment=TA_LEFT),
'cell':ParagraphStyle('cell',fontName='TNR',fontSize=12,leading=13.5,alignment=TA_LEFT,splitLongWords=True),
'toc0':ParagraphStyle('toc0',fontName='TNR',fontSize=14,leading=21,spaceBefore=5),
'toc1':ParagraphStyle('toc1',fontName='TNR',fontSize=14,leading=20,leftIndent=12*mm)
}
class PDF(SimpleDocTemplate):
 def afterFlowable(self,flowable):
  if hasattr(flowable,'toclevel'):
   text=flowable.getPlainText(); self.notify('TOCEntry',(flowable.toclevel,text,self.page)); self.entries.append((flowable.toclevel,text,self.page))
 def beforeDocument(self):self.entries=[]

def footer(c,d):
 if d.page>1:
  c.setFont('TNR',12);c.drawCentredString(110*mm,10*mm,str(d.page))
doc=Document(out/'Шкель_Антон_Введение_и_глава_1.docx')
story=[]; in_title=True; added_toc=False
def para(text,sty,bold=False):
 t=escape(text).replace('\n','<br/>')
 return Paragraph(('<b>'+t+'</b>') if bold else t,styles[sty])
for el in doc.element.body:
 if el.tag.endswith('}p'):
  p=WParagraph(el,doc); t=p.text
  if t=='СОДЕРЖАНИЕ':
   story.append(PageBreak());story.append(para(t,'center',True));story.append(Spacer(1,10));toc=TableOfContents();toc.levelStyles=[styles['toc0'],styles['toc1']];story.append(toc);in_title=False;added_toc=True;continue
  if el.xpath('.//w:fldSimple'):continue
  if el.xpath('.//w:drawing'):
   story.append(Image(str(out/'ER_модель.png'),width=167*mm,height=105*mm));continue
  if p.style.name=='Heading 1':
   story.append(PageBreak());st='center' if t.isupper() else 'h1';q=para(t,st,True);q.toclevel=0;story.append(q);continue
  if p.style.name=='Heading 2':
   q=para(t,'h2');q.toclevel=1;story.append(q);continue
  if not t:
   if in_title:story.append(Spacer(1,8))
   continue
  alignment=p.alignment
  sty='normal'
  if alignment==1:sty='center'
  elif alignment==2:sty='right'
  if in_title:sty='right' if alignment==2 else 'center'
  if t.startswith(('Таблица ','Таблица А.')):sty='left'
  q=para(t,sty,all(r.bold for r in p.runs if r.text))
  if t.startswith('Таблица '):q.keepWithNext=True
  story.append(q)
 elif el.tag.endswith('}tbl'):
  wt=WTable(el,doc); rows=[]
  for i,r in enumerate(wt.rows):rows.append([para(c.text,'cell',i==0) for c in r.cells])
  widths=[c.width.pt for c in wt.rows[0].cells]
  tab=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
  tab.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
  # Main-text tables should fit on a single page and remain with their titles.
  if len(story) and getattr(story[-1],'keepWithNext',False):
   title=story.pop();story.append(KeepTogether([title,tab]))
  else:story.append(tab)
pdf=PDF(str(out/'Шкель_Антон_Введение_и_глава_1.pdf'),pagesize=(210*mm,297*mm),leftMargin=30*mm,rightMargin=10*mm,topMargin=20*mm,bottomMargin=20*mm,title='Проектирование базы данных маркетплейса: введение и глава 1',author='Шкель Антон Алексеевич')
pdf.multiBuild(story,onFirstPage=footer,onLaterPages=footer)
(base/'pdf_contents.json').write_text(json.dumps(pdf.entries,ensure_ascii=False,indent=2),encoding='utf-8')
print('PDF ready',len(pdf.entries),'entries')
