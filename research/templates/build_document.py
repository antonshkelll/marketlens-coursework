import json, re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family']='Times New Roman'
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BASE=Path(__file__).parent
OUT=BASE.parent/'Курсовая_Шкель_Антон'
OUT.mkdir(exist_ok=True)
data=json.loads((BASE/'content.json').read_text(encoding='utf-8'))
for item in data['sections']:
 item['paragraphs']=[s.replace('[5, с. 16:1]','[5, с. 1]') for s in item['paragraphs']]
fig,ax=plt.subplots(figsize=(12,7.6))
ax.set_xlim(0,12); ax.set_ylim(0,7.6); ax.axis('off')
boxes={
'user':(0.2,6.4,'Пользователь'),'session':(4.4,6.4,'Сессия'),'event':(8.6,6.4,'Событие'),
'cart':(0.2,4.7,'Корзина'),'run':(4.4,4.7,'Запуск стратегии'),'ri':(8.6,4.7,'Позиция выдачи'),
'ci':(0.2,3,'Позиция корзины'),'seller':(4.4,3,'Продавец'),'product':(8.6,3,'Товар'),
'order':(0.2,1.3,'Заказ'),'oi':(4.4,1.3,'Позиция заказа'),'offer':(8.6,1.3,'Предложение')}
for k,(x,y,t) in boxes.items():
 ax.add_patch(FancyBboxPatch((x,y),2.8,.65,boxstyle='round,pad=0.03',facecolor='white',edgecolor='black',lw=1.2)); ax.text(x+1.4,y+.325,t,ha='center',va='center',fontsize=18)
def edge(a,b,aa,bb,label,dx=0,dy=0):
 x,y=boxes[a][0]+aa[0],boxes[a][1]+aa[1]; xx,yy=boxes[b][0]+bb[0],boxes[b][1]+bb[1]
 ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'-','lw':1.1,'color':'black'})
 ax.text((x+xx)/2+dx,(y+yy)/2+dy,label,ha='center',va='center',fontsize=15,bbox=dict(facecolor='white',edgecolor='none',pad=1))
edge('user','session',(2.8,.325),(0,.325),'1 : N')
edge('session','event',(2.8,.325),(0,.325),'1 : N')
edge('user','cart',(1.4,0),(1.4,.65),'1 : N',.36)
edge('session','run',(1.4,0),(1.4,.65),'1 : N',.36)
edge('run','ri',(2.8,.325),(0,.325),'1 : N')
edge('ri','product',(1.4,0),(1.4,.65),'N : 1',.36)
edge('cart','ci',(1.4,0),(1.4,.65),'1 : N',.36)
edge('seller','offer',(2.8,.325),(1.4,.65),'1 : N',0,.18)
edge('product','offer',(1.4,0),(1.4,.65),'1 : N',.36)
edge('order','oi',(2.8,.325),(0,.325),'1 : N')
edge('oi','offer',(2.8,.325),(0,.325),'N : 1')
ax.text(6,.5,'Дополнительные связи: пользователь — заказ; позиция корзины — предложение;\nсобытие — товар; переход — позиция выдачи; категория — товар; тип — событие.',ha='center',va='center',fontsize=14)
fig.tight_layout(pad=.2); fig.savefig(OUT/'ER_модель.png',dpi=220,bbox_inches='tight'); plt.close(fig)

doc=Document(); sec=doc.sections[0]
sec.page_width=Cm(21); sec.page_height=Cm(29.7)
sec.left_margin=Cm(3); sec.right_margin=Cm(1); sec.top_margin=Cm(2); sec.bottom_margin=Cm(2)
sec.header_distance=Cm(.8); sec.footer_distance=Cm(1)
sec.different_first_page_header_footer=True
normal=doc.styles['Normal']; normal.font.name='Times New Roman'; normal.font.size=Pt(14)
normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
pf=normal.paragraph_format; pf.line_spacing=1.5; pf.space_before=Pt(0); pf.space_after=Pt(0); pf.first_line_indent=Cm(1.25); pf.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
for s in ['Heading 1','Heading 2','Heading 3']:
 st=doc.styles[s]; st.font.name='Times New Roman'; st.font.size=Pt(14); st.font.bold=True; st.font.color.rgb=__import__('docx').shared.RGBColor(0,0,0)
 st.paragraph_format.space_before=Pt(12); st.paragraph_format.space_after=Pt(6); st.paragraph_format.line_spacing=1.5; st.paragraph_format.first_line_indent=Cm(1.25)
 st.paragraph_format.keep_with_next=True
doc.styles['Heading 1'].paragraph_format.page_break_before=True
for sty in ['TOC 1','TOC 2']:
 if sty in doc.styles:
  doc.styles[sty].font.name='Times New Roman'; doc.styles[sty].font.size=Pt(14)
foot=sec.footer.paragraphs[0]; foot.alignment=WD_ALIGN_PARAGRAPH.CENTER; foot.paragraph_format.first_line_indent=0
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); foot._p.append(fld)
def p(text='',align=None):
 q=doc.add_paragraph(text)
 if align is not None: q.alignment=align; q.paragraph_format.first_line_indent=0
 return q
def center(t,bold=False,size=14):
 q=p(t,WD_ALIGN_PARAGRAPH.CENTER)
 for r in q.runs:r.bold=bold;r.font.size=Pt(size)
 return q
def head(t,level=1,centered=False):
 q=doc.add_paragraph(t,'Heading '+str(level))
 if centered:q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.first_line_indent=0
 return q
def table(title,headers,rows,widths):
 q=p(title); q.paragraph_format.first_line_indent=0; q.paragraph_format.keep_with_next=True; q.paragraph_format.space_before=Pt(6)
 t=doc.add_table(rows=1, cols=len(headers)); t.style='Table Grid'; t.autofit=False
 for i,w in enumerate(widths):t.columns[i].width=Cm(w)
 for c,s in zip(t.rows[0].cells,headers):c.text=s
 trPr=t.rows[0]._tr.get_or_add_trPr(); rep=OxmlElement('w:tblHeader');trPr.append(rep)
 for row in rows:
  for c,s in zip(t.add_row().cells,row):c.text=s
 for i,row in enumerate(t.rows):
  trpr=row._tr.get_or_add_trPr(); trpr.append(OxmlElement('w:cantSplit'))
  for j,c in enumerate(row.cells):
   c.width=Cm(widths[j])
   for q in c.paragraphs:
    q.paragraph_format.first_line_indent=0;q.paragraph_format.line_spacing=1;q.paragraph_format.space_after=Pt(4);q.paragraph_format.space_before=Pt(4); q.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in q.runs:r.font.size=Pt(12);r.bold=(i==0)
 p('Источник: составлено автором.').paragraph_format.first_line_indent=0

center('Федеральное государственное образовательное бюджетное\nучреждение высшего образования')
center('«Финансовый университет при Правительстве\nРоссийской Федерации»',True)
center('(Финансовый университет)')
p();center('Факультет «Высшая школа управления»')
center('Кафедра стратегического и инновационного развития')
p();center('КУРСОВАЯ РАБОТА',True)
center('по дисциплине «Базы данных и аналитические системы»')
p();center('Проектирование базы данных маркетплейса\nс рекомендательной подсистемой и аналитикой\nпользовательского поведения',True)
p();center('Введение и глава 1')
p();q=p('Выполнил: студент группы ПрИнж25-1\nШкель Антон Алексеевич\n\nНаучный руководитель:\nк.х.н., доцент\nМихайлов Сергей Александрович',WD_ALIGN_PARAGRAPH.RIGHT)
q.paragraph_format.line_spacing=1.15
p();center('Москва — 2026')
q=center('СОДЕРЖАНИЕ',True); q.paragraph_format.page_break_before=True; q.paragraph_format.keep_with_next=True
q=p();q.paragraph_format.first_line_indent=0
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'TOC \\o "1-2" \\h \\z \\u'); q._p.append(field)
head('ВВЕДЕНИЕ',centered=True)
for s in data['intro']:p(s)
head('1 Анализ предметной области и постановка задачи')
rows1=[
('AppUser','user_id (PK); created_at','Условный профиль пользователя'),
('Seller','seller_id (PK); seller_name','Продавец маркетплейса'),
('Category','category_id (PK); category_name','Категория каталога'),
('Product','product_id (PK); category_id (FK); product_name','Карточка товара'),
('Offer','offer_id (PK); seller_id, product_id (FK); current_price; is_active','Предложение продавца'),
('Cart','cart_id (PK); user_id (FK); created_at','Корзина пользователя'),
('CartItem','cart_id, offer_id (PK, FK); quantity','Состав корзины'),
('CustomerOrder','order_id (PK); user_id, session_id (FK); ordered_at; status','Заказ; сессия необязательна'),
('OrderItem','order_id (PK, FK); line_no (PK); offer_id (FK); quantity; unit_price','Позиция и цена покупки')]
rows2=[
('UserSession','session_id (PK); user_id (FK); started_at','Контекст последовательности действий'),
('EventType','event_type_id (PK); event_code','Справочник видов действий'),
('Event','event_id (PK); session_id, event_type_id, product_id (FK); occurred_at; run_id (необязательный FK)','Событие; run_id и product_id ссылаются на позицию выдачи'),
('RecommendationRun','run_id (PK); session_id (FK); strategy_code; strategy_version; generated_at; history_cutoff','Контекст запуска стратегии'),
('RecommendationItem','run_id (PK, FK); product_id (PK, FK); rank_no; score; reason_code; source_product_id (необязательный FK)','Результат и основание рекомендации')]
for section in data['sections']:
 head(section['title'],2)
 for idx,s in enumerate(section['paragraphs']):
  p(s)
  if section['title'].startswith('1.2') and idx==0:
   q=p();q.paragraph_format.first_line_indent=0;q.alignment=WD_ALIGN_PARAGRAPH.CENTER
   q.add_run().add_picture(str(OUT/'ER_модель.png'),width=Cm(16.7))
   center('Рисунок 1 — Основные связи концептуальной модели')
   center('Источник: составлено автором.')
  if section['title'].startswith('1.2') and idx==3:
   table('Таблица 1 — Логическая структура торгового ядра',['Отношение','Основные атрибуты и ключи','Назначение'],rows1,[3.4,8,5.6])
   table('Таблица 2 — Логическая структура событий и рекомендаций',['Отношение','Основные атрибуты и ключи','Назначение'],rows2,[3.4,8,5.6])
  if section['title'].startswith('1.3') and idx==3:
   table('Таблица 3 — Требования и способы проверки решения',['Требование','Результат','Проверка'],[
   ('Согласованность данных','Заказы, события и выдачи связаны ключами','Отказ при вставке строки с отсутствующей ссылкой'),
   ('Однозначность показателей','Единые правила воронки и повторных покупок','Сравнение SQL с ручным расчётом'),
   ('Воспроизводимость','Сохранены версия стратегии и временная граница','Повторный запуск даёт тот же список'),
   ('Работа без истории','Используется популярность','Выдача для нового пользователя без дублей'),
   ('Корректность сравнения','Единый каталог и временные интервалы','Контроль отсутствия будущих данных в агрегатах'),
   ('Обоснованная оптимизация','Сохранён результат запросов','Сравнение результатов и медианного времени')],[4.3,6.1,6.6])
head('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',centered=True)
for i,s in enumerate(data['references'],1):
 q=p(f'{i}. {s}');q.paragraph_format.first_line_indent=0;q.paragraph_format.space_after=Pt(6)
head('ПРИЛОЖЕНИЯ',centered=True)
head('ПРИЛОЖЕНИЕ А',centered=True)
center('Связи и дополнительные ограничения логической модели',True)
p('Перечень дополняет таблицы 1 и 2. Обязательность внешнего ключа означает наличие родительской строки для каждого дочернего объекта. У родительского объекта может ещё не быть дочерних записей; заказ в статусе «подтверждён» и завершённый запуск выдачи проверяются отдельно на наличие позиций.')
links=[
('Product.category_id → Category','N : 1; обязательная'),('Offer.seller_id → Seller; Offer.product_id → Product','N : 1; обязательные'),
('Cart.user_id → AppUser; CustomerOrder.user_id → AppUser','N : 1; обязательные'),('CartItem.cart_id → Cart; CartItem.offer_id → Offer','N : 1; обязательные'),
('OrderItem.order_id → CustomerOrder; OrderItem.offer_id → Offer','N : 1; обязательные'),('UserSession.user_id → AppUser','N : 1; обязательная'),
('CustomerOrder.session_id → UserSession','N : 1; необязательная'),('Event.session_id → UserSession; Event.event_type_id → EventType; Event.product_id → Product','N : 1; обязательные'),
('RecommendationRun.session_id → UserSession','N : 1; обязательная'),('RecommendationItem.run_id → RecommendationRun; RecommendationItem.product_id → Product','N : 1; обязательные'),
('RecommendationItem.source_product_id → Product','N : 1; необязательная'),('Event.(run_id, product_id) → RecommendationItem.(run_id, product_id)','N : 1; только при переходе из выдачи')]
table('Таблица А.1 — Внешние ключи и кратности',['Связь','Правило'],links,[12,5])
p('Дополнительные уникальные ограничения: Seller.seller_name не используется как ключ; Offer(seller_id, product_id), OrderItem(order_id, offer_id), RecommendationItem(run_id, rank_no) и EventType.event_code уникальны. Идентификатор Event.event_id служит ключом устранения дублей при повторной загрузке. Для исходного журнала без устойчивых идентификаторов требуется отдельное правило идентификации, обоснованное во второй главе.')
p('Зависимости, принятые при проверке нормализации: user_id → created_at; seller_id → seller_name; category_id → category_name; product_id → category_id, product_name; offer_id → seller_id, product_id, current_price, is_active; cart_id → user_id, created_at; (cart_id, offer_id) → quantity; order_id → user_id, session_id, ordered_at, status; (order_id, line_no) → offer_id, quantity, unit_price; session_id → user_id, started_at; event_type_id → event_code; event_id → session_id, event_type_id, product_id, occurred_at, run_id; run_id → session_id, strategy_code, strategy_version, generated_at, history_cutoff; (run_id, product_id) → rank_no, score, reason_code, source_product_id. Дополнительные кандидатные ключи следуют из перечисленных ограничений уникальности.')
p('Временные ограничения: history_cutoff ≤ generated_at; для контрольного эксперимента исходные заказы имеют ordered_at < history_cutoff. Событие относится к своей сессии, а переход из рекомендации — к запуску той же сессии с generated_at ≤ occurred_at. Внутри сессии соблюдается принятый порог разрыва. Изменение статуса заказа в демонстрационном сценарии не моделируется: статус задаётся при подготовке данных; для реальной истории потребуется журнал изменений статусов.')
p('Для персональной выдачи source_product_id обозначает товар истории с наибольшим вкладом в итоговый балл кандидата; при равном вкладе выбирается меньший идентификатор. Полный балл восстанавливается по всей истории на history_cutoff. Для выдачи по популярности source_product_id отсутствует. Объяснение одного основного вклада не заменяет проверку полного расчёта.')
doc.core_properties.title='Проектирование базы данных маркетплейса: введение и глава 1'
doc.core_properties.author='Шкель Антон Алексеевич'
doc.core_properties.subject='Курсовая работа по дисциплине «Базы данных и аналитические системы»'
settings=doc.settings.element
upd=OxmlElement('w:updateFields');upd.set(qn('w:val'),'true');settings.append(upd)
path=OUT/'Шкель_Антон_Введение_и_глава_1.docx';doc.save(path)
print(path)
print('Words:',sum(len(s.split()) for s in data['intro'])+sum(len(p.split()) for s in data['sections'] for p in s['paragraphs']))
