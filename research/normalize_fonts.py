"""Set every Word font slot explicitly, including fields and style defaults."""
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as ET
from pathlib import Path
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
def normalize(path):
 path=Path(path)
 with ZipFile(path) as z: parts={n:z.read(n) for n in z.namelist()}
 for name,blob in list(parts.items()):
  if not name.startswith('word/') or not name.endswith('.xml'):continue
  root=ET.fromstring(blob)
  for node in root.iter('{'+W+'}rPr'):
   font=node.find('{'+W+'}rFonts')
   if font is None:font=ET.SubElement(node,'{'+W+'}rFonts')
   font.attrib.clear()
   for key in ['ascii','hAnsi','eastAsia','cs']:font.set('{'+W+'}'+key,'Times New Roman')
  for node in root.iter('{'+W+'}r'):
   props=node.find('{'+W+'}rPr')
   if props is None:props=ET.Element('{'+W+'}rPr');node.insert(0,props)
   font=props.find('{'+W+'}rFonts')
   if font is None:font=ET.SubElement(props,'{'+W+'}rFonts')
   font.attrib.clear()
   for key in ['ascii','hAnsi','eastAsia','cs']:font.set('{'+W+'}'+key,'Times New Roman')
  for node in root.iter():
   if node.tag=='{'+W+'}t' and node.text:node.text=node.text.replace('—','–')
   if node.tag in ['{'+A+'}latin','{'+A+'}ea','{'+A+'}cs']:node.set('typeface','Times New Roman')
  parts[name]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 with ZipFile(path,'w',ZIP_DEFLATED) as z:
  for name,blob in parts.items():z.writestr(name,blob)
if __name__=='__main__':
 import sys
 normalize(sys.argv[1])
