import json
from experiment import connect,WEB,START,END
with connect() as c:
 d=json.loads((WEB/'data.json').read_text(encoding='utf-8'))
 d['analytics']=c.execute("SELECT date(f.view_at,'unixepoch'),p.category_id,COUNT(*),COUNT(cart_at),COUNT(buy_at) FROM funnel f JOIN product p USING(product_id) WHERE f.view_at>=? AND f.view_at<? GROUP BY 1,2",(START,END)).fetchall()
 d['order_activity']=c.execute("SELECT DISTINCT date(o.ordered_at,'unixepoch'),p.category_id,o.user_id,o.order_id FROM customer_order o JOIN order_item i USING(order_id) JOIN offer f USING(offer_id) JOIN product p USING(product_id) WHERE o.status='confirmed' AND o.ordered_at>=? AND o.ordered_at<?",(START,END)).fetchall()
 (WEB/'data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Exported control analytics filters')
