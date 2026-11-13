"""Export native Word pagination and stabilize the visible table of contents."""
from pathlib import Path
import argparse,subprocess,tempfile,json,re,shutil
from pypdf import PdfReader
from docx import Document
from fill_toc import fill
from normalize_fonts import normalize
BASE=Path(__file__).resolve().parent

def export(soffice):
 path=BASE/'Шкель_Антон_Курсовая_полная.docx'
 norm=lambda s:re.sub(r'\s+','',s)
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);out=root/'pdf';out.mkdir()
  for attempt in range(4):
   result=subprocess.run([str(soffice),'-env:UserInstallation='+ (root/'profile').as_uri(),'--headless','--norestore','--convert-to','pdf','--outdir',str(out),str(path)],capture_output=True,timeout=120)
   pdf=out/(path.stem+'.pdf')
   if result.returncode or not pdf.exists():raise RuntimeError('LibreOffice export failed: '+result.stdout.decode(errors='replace')+result.stderr.decode(errors='replace'))
   pages=PdfReader(pdf);texts=[norm(p.extract_text() or '') for p in pages.pages];cache={}
   for p in Document(path).paragraphs:
    if p.style.name in ('Heading 1','Heading 2'):
     found=[i+1 for i,text in enumerate(texts) if i>=2 and norm(p.text) in text]
     if not found:raise RuntimeError('Heading not found: '+p.text)
     cache[p.text]=found[0]
   prior=json.loads((BASE/'toc_pages.json').read_text(encoding='utf-8'))
   if cache==prior:
    shutil.copy2(pdf,BASE/pdf.name);print('Verified native PDF:',len(pages.pages),'pages; body before appendices:',cache['ПРИЛОЖЕНИЯ']-1);return
   (BASE/'toc_pages.json').write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8');fill(path);normalize(path);pdf.unlink()
  raise RuntimeError('TOC pagination did not stabilize')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--soffice',required=True,type=Path);export(p.parse_args().soffice)
