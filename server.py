"""Local/single-host synthetic-data demonstration. No payments or personal data."""
import argparse,json,sqlite3,time
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from experiment import ROOT,WEB,connect,history,recommend
def session(c,user,now):
 c.execute('INSERT OR IGNORE INTO app_user VALUES(?,?)',(user,now))
 row=c.execute('SELECT s.session_id,MAX(COALESCE(e.occurred_at,s.started_at)) last_at FROM user_session s LEFT JOIN event e USING(session_id) WHERE s.user_id=? GROUP BY s.session_id ORDER BY last_at DESC LIMIT 1',(user,)).fetchone()
 if row and now-row[1]<=1800:return row[0]
 return c.execute('INSERT INTO user_session(user_id,started_at) VALUES(?,?) RETURNING session_id',(user,now)).fetchone()[0]
def checkout(c,user,items,now):
 if not items or len(items)>120:raise ValueError('Корзина должна содержать от 1 до 120 позиций')
 unique={}
 for item in items:
  p=int(item['product_id']);qty=int(item['quantity'])
  if p in unique or not 1<=qty<=20:raise ValueError('Некорректное количество или повтор товара')
  f=c.execute('SELECT offer_id,current_price FROM offer WHERE product_id=? AND is_active=1 ORDER BY current_price,offer_id LIMIT 1',(p,)).fetchone()
  if not f:raise ValueError('Товар недоступен')
  unique[p]=(f[0],f[1],qty)
 sid=session(c,user,now);cart=c.execute('INSERT INTO cart(user_id,created_at) VALUES(?,?) RETURNING cart_id',(user,now)).fetchone()[0]
 oid=c.execute("INSERT INTO customer_order(user_id,session_id,ordered_at,status) VALUES(?,?,?,'confirmed') RETURNING order_id",(user,sid,now)).fetchone()[0]
 for line,(p,(f,price,qty)) in enumerate(unique.items(),1):
  c.execute('INSERT INTO cart_item VALUES(?,?,?)',(cart,f,qty));c.execute('INSERT INTO order_item VALUES(?,?,?,?,?)',(oid,line,f,qty,price))
 return {'order_id':oid,'session_id':sid,'total':sum(price*qty for f,price,qty in unique.values())/100}
class Handler(SimpleHTTPRequestHandler):
 def reply(self,obj,status=200):
  body=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def do_GET(self):
  parsed=urlparse(self.path)
  if parsed.path=='/api/health':
   with connect() as c:c.execute('SELECT 1').fetchone()
   return self.reply({'ok':True})
  if parsed.path=='/api/recommend':
   try:
    user=int(parse_qs(parsed.query).get('user',['1'])[0]);assert 1<=user<=999
    now=int(time.time())
    with connect() as c:
     c.execute('BEGIN IMMEDIATE')
     now=max(now,c.execute('SELECT COALESCE(MAX(e.occurred_at),0)+1 FROM event e JOIN user_session s USING(session_id) WHERE s.user_id=?',(user,)).fetchone()[0])
     sid=session(c,user,now);model=history(c,now);items=recommend(model,user,'cooccurrence')
     run=c.execute("INSERT INTO recommendation_run(session_id,strategy_code,strategy_version,generated_at,history_cutoff) VALUES(?,'cooccurrence','1.0',?,?) RETURNING run_id",(sid,now,now)).fetchone()[0]
     for rank,r in enumerate(items,1):c.execute('INSERT INTO recommendation_item VALUES(?,?,?,?,?,?)',(run,r['product_id'],rank,r['score'],r['reason'],r['source']))
    return self.reply({'recommendations':items,'history':sorted(model[0].get(user,set())),'run_id':run,'session_id':sid})
   except (ValueError,AssertionError):return self.reply({'error':'Некорректный пользователь'},400)
  # Only public demo files; databases and source are outside this directory.
  return super().do_GET()
 def do_POST(self):
  origin=self.headers.get('Origin')
  if origin and (urlparse(origin).netloc!=self.headers.get('Host','') or urlparse(origin).scheme not in ('http','https')):return self.reply({'error':'Cross-origin write rejected'},403)
  if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':return self.reply({'error':'JSON body required'},415)
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=16384:raise ValueError('Некорректный размер запроса')
   obj=json.loads(self.rfile.read(length));user=int(obj['user_id']);now=int(time.time())
   if not 1<=user<=999:raise ValueError('Некорректный пользователь')
   with connect() as c:
    c.execute('BEGIN IMMEDIATE')
    now=max(now,c.execute('SELECT COALESCE(MAX(e.occurred_at),0)+1 FROM event e JOIN user_session s USING(session_id) WHERE s.user_id=?',(user,)).fetchone()[0])
    if self.path=='/api/checkout':result=checkout(c,user,obj['items'],now)
    elif self.path=='/api/event':
     sid=session(c,user,now);p=int(obj['product_id']);kind=int(obj['event_type'])
     if kind not in (1,2,3):raise ValueError('Неизвестный тип события')
     c.execute('INSERT INTO event(session_id,event_type_id,product_id,occurred_at,run_id) VALUES(?,?,?,?,?)',(sid,kind,p,now,obj.get('run_id') if kind==3 else None));result={'ok':True,'session_id':sid}
    else:return self.reply({'error':'Not found'},404)
   self.reply(result)
  except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:self.reply({'error':str(e)},400)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8000);a=p.parse_args()
 with connect() as c:c.execute('PRAGMA journal_mode=WAL')
 print(f'MarketLens: http://{a.host}:{a.port}',flush=True)
 ThreadingHTTPServer((a.host,a.port),partial(Handler,directory=str(WEB))).serve_forever()
