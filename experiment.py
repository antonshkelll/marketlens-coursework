"""Reproduce the synthetic dataset, temporal experiment and static demo exports.
Python 3.11+, standard library only. All timestamps are UTC; prices are kopeks.
"""
import collections, datetime as dt, hashlib, json, math, platform, random, sqlite3, statistics, sys, time
from pathlib import Path
ROOT=Path(__file__).parent
DATA=ROOT/'data'; WEB=ROOT/'docs'; DB=DATA/'marketlens.sqlite'
SEED=13112026
def stamp(day):return int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())
START=stamp('2026-09-01'); VALID=stamp('2026-10-11'); TEST=stamp('2026-10-21'); END=stamp('2026-10-31')
def connect(path=DB):
 c=sqlite3.connect(path,timeout=15);c.execute('PRAGMA foreign_keys=ON');c.create_function('sqrt',1,math.sqrt);return c
def split_by_time(rows,cutoff,end):
 train=[r for r in rows if r['at']<cutoff];test=[r for r in rows if cutoff<=r['at']<end]
 assert all(r['at']<cutoff for r in train) and all(cutoff<=r['at']<end for r in test)
 return train,test
def prepare():
 DATA.mkdir(exist_ok=True);WEB.mkdir(exist_ok=True)
 if DB.exists():DB.unlink() # Only this generated file, never arbitrary database paths.
 c=connect();c.executescript((ROOT/'sql/schema.sql').read_text())
 rng=random.Random(SEED)
 names=['Рабочее место','Аудио','Свет','Аксессуары','Путешествия','Дом']
 kinds=[['Клавиатура','Мышь','Монитор','Подставка'],['Наушники','Колонка','Микрофон','ЦАП'],['Лампа','Светильник','Подсветка','Торшер'],['Хаб','Кабель','Зарядка','Держатель'],['Рюкзак','Термос','Органайзер','Пауэрбанк'],['Часы','Увлажнитель','Весы','Розетка']]
 for k,n in enumerate(names,1):c.execute('INSERT INTO category VALUES(?,?)',(k,n))
 for s,n in enumerate(['North Studio','Forma Store','Mono Supply'],1):c.execute('INSERT INTO seller VALUES(?,?)',(s,n))
 for p in range(1,121):
  cat=(p-1)//20;name=kinds[cat][(p-1)%4]+' '+['Air','Core','Plus','Mini','Pro'][(p-1)//4%5]
  c.execute('INSERT INTO product VALUES(?,?,?)',(p,cat+1,name))
  for s in range(1,4):c.execute('INSERT INTO offer VALUES(?,?,?,?,1)',((p-1)*3+s,s,p,(900+(p*173)%14000+s*60)*100))
 for u in range(1,361):c.execute('INSERT INTO app_user VALUES(?,?)',(u,START-86400))
 c.executemany('INSERT INTO event_type VALUES(?,?)',[(1,'view'),(2,'cart'),(3,'recommendation_click')])
 c.execute('CREATE TEMP TABLE raw_event(event_id INTEGER,user_id INTEGER,product_id INTEGER,event_type_id INTEGER,occurred_at INTEGER)')
 eid=0;orders=[]
 for u in range(1,361):
  pref=u%6
  for day in range(60):
   if rng.random()>.43:continue
   at=START+day*86400+((u*17+day*7)%16+4)*3600
   cat=pref if rng.random()<.8 else rng.randrange(6)
   anchor=cat*20+1+((u//6)%5)*4
   products=set([anchor,anchor+1]) if rng.random()<.72 else set(rng.sample(range(cat*20+1,cat*20+21),2))
   products.add(rng.randrange(1,121))
   chosen=[]
   for idx,p in enumerate(sorted(products)):
    eid+=1;c.execute('INSERT INTO raw_event VALUES(?,?,?,?,?)',(eid,u,p,1,at+idx*120))
    if rng.random()<.77:
     eid+=1;c.execute('INSERT INTO raw_event VALUES(?,?,?,?,?)',(eid,u,p,2,at+idx*120+40));chosen.append((p-1)*3+1+rng.randrange(3))
   if chosen:orders.append((u,at+900,chosen,'confirmed' if rng.random()<.7 else 'cancelled'))
 c.executescript((ROOT/'sql/sessionize.sql').read_text())
 for oid,(u,at,offers,status) in enumerate(orders,1):
  sid=c.execute('SELECT session_id FROM user_session WHERE user_id=? AND started_at BETWEEN ? AND ?',(u,at-1800,at)).fetchone()[0]
  c.execute('INSERT INTO customer_order VALUES(?,?,?,?,?)',(oid,u,sid,at,status))
  for line,f in enumerate(offers,1):
   price=c.execute('SELECT current_price FROM offer WHERE offer_id=?',(f,)).fetchone()[0]
   c.execute('INSERT INTO order_item VALUES(?,?,?,?,?)',(oid,line,f,1,price))
 c.executescript((ROOT/'sql/analytics.sql').read_text());c.commit();return c
def history(c,cutoff):
 rows=c.execute('SELECT order_id,user_id,product_id,ordered_at FROM order_product WHERE ordered_at<? ORDER BY order_id,product_id',(cutoff,)).fetchall()
 baskets=collections.defaultdict(set);users=collections.defaultdict(set)
 for oid,u,p,t in rows:baskets[oid].add(p);users[u].add(p)
 pop=collections.Counter(p for b in baskets.values() for p in b);pair=collections.Counter()
 for b in baskets.values():
  for a in b:
   for p in b:
    if a!=p:pair[a,p]+=1
 return users,pop,pair
def recommend(model,user,strategy,k=10,min_pair=1):
 users,pop,pairs=model;seen=users.get(user,set());scores=collections.Counter();sources={}
 if strategy=='cooccurrence':
  for a in sorted(seen):
   for p in range(1,121):
    n=pairs[a,p]
    if p not in seen and n>=min_pair:
     value=n/math.sqrt(pop[a]*pop[p]);scores[p]+=value
     if p not in sources or value>sources[p][1]:sources[p]=(a,value)
 ranked=sorted(scores,key=lambda p:(-scores[p],p))
 ranked += [p for p in sorted(range(1,121),key=lambda p:(-pop[p],p)) if p not in seen and p not in scores]
 return [{'product_id':p,'score':round(scores[p] if p in scores else float(pop[p]),8),'source':sources.get(p,(None,0))[0],'reason':'cooccurrence' if p in scores else 'popularity'} for p in ranked[:k]]
def evaluate(c,cutoff,end,strategy,min_pair=1):
 model=history(c,cutoff);truth=collections.defaultdict(set)
 for u,p in c.execute('SELECT DISTINCT user_id,product_id FROM order_product WHERE ordered_at>=? AND ordered_at<?',(cutoff,end)):
  if p not in model[0].get(u,set()):truth[u].add(p)
 precision=[];recall=[];covered=set()
 for u in range(1,361):
  result={r['product_id'] for r in recommend(model,u,strategy,min_pair=min_pair)};covered |=result
  if truth[u]:
   hits=len(result&truth[u]);precision.append(hits/10);recall.append(hits/len(truth[u]))
 return {'precision_at_10':statistics.mean(precision),'recall_at_10':statistics.mean(recall),'coverage':len(covered)/120,'eligible_users':len(precision),'population':360,'catalog_size':120}
def benchmark(c):
 query='SELECT COUNT(*) FROM event WHERE session_id=? AND occurred_at>=?'
 args=(200,START);before_plan=c.execute('EXPLAIN QUERY PLAN '+query,args).fetchall()
 def run():
  for _ in range(3):c.execute(query,args).fetchone()
  ts=[]
  for _ in range(31):
   t=time.perf_counter_ns();answer=c.execute(query,args).fetchone()[0];ts.append((time.perf_counter_ns()-t)/1e6)
  return statistics.median(ts),answer
 before,answer=run();c.execute('CREATE INDEX event_session_time ON event(session_id,occurred_at)');after,result=run();assert answer==result
 return {'query':query,'parameters':args,'before_ms':before,'after_ms':after,'speedup':before/after,'repeats':31,'warmups':3,'answer':answer,'before_plan':before_plan,'after_plan':c.execute('EXPLAIN QUERY PLAN '+query,args).fetchall()}
def export(c,results):
 products=[dict(zip(['id','category','name','price','seller'],r)) for r in c.execute('SELECT p.product_id,p.category_id,p.product_name,MIN(f.current_price),MIN(f.seller_id) FROM product p JOIN offer f USING(product_id) GROUP BY p.product_id')]
 model=history(c,TEST)
 profiles={str(u):{'history':sorted(model[0].get(u,set())),'recommendations':recommend(model,u,'cooccurrence',min_pair=results['selected_min_pair'])} for u in list(range(1,361))+[999]}
 f=c.execute('SELECT COUNT(*),COUNT(cart_at),COUNT(buy_at) FROM funnel').fetchone()
 buyers=c.execute("SELECT COUNT(*) FROM(SELECT user_id,COUNT(*) n FROM customer_order WHERE status='confirmed' GROUP BY user_id)").fetchone()[0]
 repeat=c.execute("SELECT COUNT(*) FROM(SELECT user_id FROM customer_order WHERE status='confirmed' GROUP BY user_id HAVING COUNT(*)>=2)").fetchone()[0]
 counts={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['app_user','product','offer','customer_order','order_item','user_session','event']}
 daily=[dict(zip(['date','orders','revenue'],r)) for r in c.execute("SELECT date(o.ordered_at,'unixepoch'),COUNT(DISTINCT o.order_id),SUM(i.quantity*i.unit_price)/100.0 FROM customer_order o JOIN order_item i USING(order_id) WHERE status='confirmed' GROUP BY 1 ORDER BY 1")]
 analytics=c.execute("SELECT date(f.view_at,'unixepoch'),p.category_id,COUNT(*),COUNT(cart_at),COUNT(buy_at) FROM funnel f JOIN product p USING(product_id) WHERE f.view_at>=? AND f.view_at<? GROUP BY 1,2",(START,END)).fetchall()
 order_activity=c.execute("SELECT DISTINCT date(o.ordered_at,'unixepoch'),p.category_id,o.user_id,o.order_id FROM customer_order o JOIN order_item i USING(order_id) JOIN offer f USING(offer_id) JOIN product p USING(product_id) WHERE o.status='confirmed' AND o.ordered_at>=? AND o.ordered_at<?",(START,END)).fetchall()
 payload={'products':products,'categories':['Рабочее место','Аудио','Свет','Аксессуары','Путешествия','Дом'],'profiles':profiles,'results':results,'funnel':{'views':f[0],'carts':f[1],'orders':f[2],'conversion':f[2]/f[0]},'counts':counts,'repeat_share':repeat/buyers,'daily':daily,'analytics':analytics,'order_activity':order_activity}
 if (DATA/'real_results.json').exists():payload['real_results']=json.loads((DATA/'real_results.json').read_text(encoding='utf-8'))
 (WEB/'data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 results.update({'counts':counts,'funnel':payload['funnel'],'repeat_share':payload['repeat_share']})
def main():
 c=prepare();valid={str(n):evaluate(c,VALID,TEST,'cooccurrence',n) for n in [1,3,5]}
 best=max([1,3,5],key=lambda n:(valid[str(n)]['recall_at_10'],-n))
 r={'seed':SEED,'train_end':'2026-10-11T00:00:00Z','test_start':'2026-10-21T00:00:00Z','test_end':'2026-10-31T00:00:00Z','selected_min_pair':best,'validation':valid,'test':{s:evaluate(c,TEST,END,s,best) for s in ['popularity','cooccurrence']},'benchmark':benchmark(c),'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'system':platform.platform()},'synthetic':True}
 records=[{'at':r[0]} for r in c.execute('SELECT DISTINCT ordered_at FROM customer_order')];train,test=split_by_time(records,TEST,END)
 r['split_audit']={'train_max':max(r['at'] for r in train),'test_min':min(r['at'] for r in test),'cutoff':TEST,'overlap':0}
 export(c,r);r['database_sha256']=hashlib.sha256(DB.read_bytes()).hexdigest();(DATA/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2));c.close()
if __name__=='__main__':main()
