from pathlib import Path
import json,re,runpy,sys
BASE=Path(__file__).parent;ROOT=BASE.parent
sys.path.insert(0,str(BASE))
PRIOR=BASE/'templates'
runpy.run_path(str(BASE/'prepare_coursework.py'),run_name='__main__')
s=(PRIOR/'build_document.py').read_text(encoding='utf-8')
s=s.replace("OUT=BASE.parent/'Курсовая_Шкель_Антон'","OUT=BASE")
s=s.replace("p();center('Введение и глава 1')","p()")
s=s.replace("q=p(t,WD_ALIGN_PARAGRAPH.CENTER)","q=p(t.replace('\\n',' \\n'),WD_ALIGN_PARAGRAPH.CENTER)")
s=s.replace("head('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',centered=True)",'''for number,key,title in [(2,'chapter2','Проектирование и реализация прототипа базы данных'),(3,'chapter3','Проверка прототипа и представление результатов')]:
 head(str(number)+' '+title)
 for section in data[key]:
  head(section['title'],2)
  for text in section['paragraphs']:p(text)
  if section['title'].startswith('3.2'):
   table('Таблица 4 — Итоговое сравнение рекомендаций',['Набор и стратегия','Precision@10','Recall@10','Охват'],[
    ('Синтетика: популярность','0,035736','0,107241','17,50%'),('Синтетика: совместные покупки','0,042943','0,137558','100,00%'),
    ('Retailrocket: популярность','0,003226','0,010753','0,02072%'),('Retailrocket: совместные покупки','0,003226','0,010753','0,02813%')],[7,3.3,3.3,3.4])
  if section['title'].startswith('3.1'):
   p('Сводные результаты сравнения стратегий далее представлены в таблице 4. Временные интервалы, число участников и правила формирования каталога используются при интерпретации каждого показателя.')
 p('Выводы по главе '+str(number)).runs[0].bold=True
 p('Во второй главе реализованы структура базы, подготовка двух наборов данных и воспроизводимый алгоритм расчёта рекомендаций. Выбор параметра отделён от тестового периода, а торговые операции демонстрируются в локальном интерфейсе.' if number==2 else 'В третьей главе подтверждено выполнение двенадцати автоматических проверок и пользовательского сценария. На реальной выборке преимущество по точности не установлено; измеренный эффект индекса ограничен одним локальным запросом. Результаты представлены с указанием происхождения и ограничений данных.')
head('ЗАКЛЮЧЕНИЕ',centered=True)
for text in data['conclusion']:p(text)
head('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',centered=True)''')
s=s.replace("head('ПРИЛОЖЕНИЯ',centered=True)","p('Источник экспериментальных данных').runs[0].bold=True\np(data['data_source'])\nhead('ПРИЛОЖЕНИЯ',centered=True)")
appendix='''
head('ПРИЛОЖЕНИЕ Б',centered=True)
center('Паспорт данных и протокол воспроизведения',True)
p('Источник: Retailrocket, events.csv (Kaggle), обращение 13.11.2026. Полная ссылка и лицензия приведены в разделе источников данных; состав наборов сопоставлен в таблице Б.1.')
table('Таблица Б.1 — Происхождение и назначение данных',['Признак','Контрольный магазин','Retailrocket'],[
 ('Происхождение','experiment.py; seed 13112026','events.csv из открытого набора Kaggle'),
 ('Пользователи','360 синтетических профилей','50 000 анонимных visitorid'),
 ('События','49 162 сгенерированных действия','354 863 исходных события выбранной когорты'),
 ('Назначение','Проверка функций, ограничений и SQL','Офлайн-сравнение рекомендаций'),
 ('Цены и продавцы','Условные, явно сгенерированные','Не восстанавливаются'),
 ('Даты событий','01.09–30.10.2026','Май–сентябрь 2015'),
 ('Право использования','Собственные демонстрационные данные','CC BY-NC-SA 4.0')],[4.2,6.4,6.4])
p('Контрольная сумма SHA-256 исходного events.csv.zip: b605e916a9379585d4a0a3f3c76abe7e5be4ed178b73d969e89061a2340ae191. Исходный архив содержит 2 756 101 строку; файлы свойств товаров в настоящем эксперименте не используются.')
p('Когорта: не менее трёх событий до 01.08.2015 UTC; 50 000 минимальных SHA-256(13112026:visitorid) из 137 654 кандидатов. Будущие действия не участвуют в отборе.')
p('UTC: обучение < 01.08.2015; валидация [01.08; 25.08); итоговая история < 25.08; тест [25.08; 19.09). Время – Unix, мс. Каталог – ранее наблюдавшиеся товары.')
p('real_study.py загружает архив; data/real_results.json содержит результат и контрольную сумму. Архив в Git не включён.')
head('ПРИЛОЖЕНИЕ В',centered=True)
center('Электронные материалы и порядок проверки',True)
p('Электронное приложение marketlens-coursework доступно по адресу https://github.com/antonshkelll/marketlens-coursework. Состав кода и результатов указан в таблице В.1. Переписка и отчёт сторонней проверки текста не публикуются.')
table('Таблица В.1 — Файлы электронного приложения',['Файл','Содержание'],[
 ('sql/schema.sql','Четырнадцать отношений, ограничения и триггеры'),('sql/sessionize.sql','Выделение сессий по 30 минутам бездействия'),('sql/analytics.sql','Воронка и активность сессий'),('sql/recommendations.sql','Проверочный расчёт рекомендаций средствами SQL'),('experiment.py','Создание контрольного набора, метрики и микробенчмарк'),('real_study.py','Загрузка Retailrocket, когорта и временное оценивание'),('tests/test_core.py','Двенадцать автоматических проверок'),('data/results.json; data/real_results.json','Численные результаты и параметры запусков'),('server.py; docs/','Локальный сервер и статическая демонстрация'),('Dockerfile; compose.yaml; DEPLOY.md','Контейнерный запуск и инструкция установки')],[7,10])
p('Запуск из корня проекта: python experiment.py; python real_study.py; python -m unittest discover -s tests -v; python server.py. Команды последовательно создают контрольную базу, загружают архив и выполняют исследование, запускают проверки и сервер на 127.0.0.1:8000. Приложение использует стандартную библиотеку Python; сборка текста – python-docx, ReportLab, matplotlib и lxml.')
p('Перед повторением experiment.py следует остановить сервер и сохранить нужные демозаказы: генератор заменяет контрольную базу. Метрики воспроизводимы, а время запросов зависит от машины.')
head('ПРИЛОЖЕНИЕ Г',centered=True)
center('Листинг выделения сессий',True)
for line in (BASE.parent/'sql/sessionize.sql').read_text(encoding='utf-8').splitlines():
 q=p(line);q.paragraph_format.first_line_indent=0;q.paragraph_format.line_spacing=1
 for run in q.runs:run.font.size=Pt(11)
p('Полные листинги остальных SQL и Python-файлов находятся в электронном приложении, перечисленном в таблице В.1. Это позволяет повторять расчёты непосредственно по исполняемому коду.')
'''
s=s.replace("doc.core_properties.title=",appendix+"\ndoc.core_properties.title=")
s=s.replace('Шкель_Антон_Введение_и_глава_1.docx','Шкель_Антон_Курсовая_полная.docx').replace('Проектирование базы данных маркетплейса: введение и глава 1','Проектирование базы данных маркетплейса с рекомендательной подсистемой и аналитикой пользовательского поведения')
(BASE/'_build_docx.py').write_text(s,encoding='utf-8');runpy.run_path(str(BASE/'_build_docx.py'),run_name='__main__')
import sys
sys.path.insert(0,str(BASE))
from normalize_fonts import normalize
from fill_toc import fill
fill(BASE/'Шкель_Антон_Курсовая_полная.docx')
normalize(BASE/'Шкель_Антон_Курсовая_полная.docx')
t=(PRIOR/'render_pdf.py').read_text(encoding='utf-8').replace("out=base.parent/'Курсовая_Шкель_Антон'","out=base")
t=t.replace('Шкель_Антон_Введение_и_глава_1','Шкель_Антон_Курсовая_полная')
t=t.replace('Проектирование базы данных маркетплейса: введение и глава 1','Проектирование базы данных маркетплейса с рекомендательной подсистемой и аналитикой пользовательского поведения')
t=t.replace("PDF(str(out/'Шкель_Антон_Курсовая_полная.pdf')","PDF(str(out/'Шкель_Антон_Курсовая_предпросмотр.pdf')")
t=t.replace("'toc0',fontName='TNR',fontSize=14,leading=21,spaceBefore=5","'toc0',fontName='TNR',fontSize=12,leading=16,spaceBefore=5")
t=t.replace("'toc1',fontName='TNR',fontSize=14,leading=20,leftIndent=12*mm","'toc1',fontName='TNR',fontSize=12,leading=16,leftIndent=8*mm")
t=t.replace("spaceBefore=12,spaceAfter=6","spaceBefore=10,spaceAfter=6")
t=t.replace("if el.xpath('.//w:fldSimple'):continue","if p.style.name=='TOC Entry':continue\n  if el.xpath('.//w:fldSimple'):continue")
# Preserve small single-spaced listing paragraphs in the PDF too.
t=t.replace("q=para(t,sty,all(r.bold for r in p.runs if r.text))","q=para(t,sty,all(r.bold for r in p.runs if r.text))\n  if p.paragraph_format.line_spacing==1 and p.runs and p.runs[0].font.size and p.runs[0].font.size.pt==11:\n   small=ParagraphStyle('code',parent=styles['left'],fontSize=11,leading=13);q=Paragraph(escape(t).replace(' ','&nbsp;'),small)")
(BASE/'_render_pdf.py').write_text(t,encoding='utf-8');runpy.run_path(str(BASE/'_render_pdf.py'),run_name='__main__')
print('Complete DOCX and PDF built')
