"""Retailrocket study: 50k pre-cutoff-active visitors, no synthetic events.
Raw source is downloaded from the publisher's Kaggle dataset, not committed.
"""
import csv,collections,datetime as dt,hashlib,heapq,io,json,math,sqlite3,statistics,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).parent;DATA=ROOT/'data';RAW=DATA/'raw';URL='https://www.kaggle.com/api/v1/datasets/download/retailrocket/ecommerce-dataset/events.csv'
def ts(s):return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()*1000)
VALID=ts('2015-08-01');TEST=ts('2015-08-25');END=ts('2015-09-19')
def rows(path):
 with zipfile.ZipFile(path) as z:
  with z.open('events.csv') as stream:
   yield from csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8'))
def model(c,cutoff):
 baskets=collections.defaultdict(set);seen=collections.defaultdict(set);catalog=set()
 for (p,) in c.execute('SELECT DISTINCT item FROM events WHERE at<?',(cutoff,)):catalog.add(p)
 for u,p,oid in c.execute("SELECT user,item,transaction_id FROM events WHERE kind='transaction' AND at<?",(cutoff,)):
  baskets[u,oid].add(p);seen[u].add(p)
 pop=collections.Counter();pairs=collections.Counter()
 for b in baskets.values():
  pop.update(b)
  for a in b:
   for p in b:
    if a!=p:pairs[a,p]+=1
 adjacency=collections.defaultdict(list)
 for (a,p),n in pairs.items():adjacency[a].append((p,n,n/math.sqrt(pop[a]*pop[p])))
 ranked=sorted(catalog,key=lambda p:(-pop[p],p))
 return seen,pop,adjacency,ranked,catalog
def recommendations(m,u,strategy,threshold):
 seen,pop,adj,ranked,catalog=m;known=seen.get(u,set());scores=collections.Counter()
 if strategy=='cooccurrence':
  for a in sorted(known):
   for p,n,score in adj[a]:
    if p not in known and n>=threshold:scores[p]+=score
 result=sorted(scores,key=lambda p:(-scores[p],p))[:10]
 for p in ranked:
  if len(result)>=10:break
  if p not in known and p not in result:result.append(p)
 return set(result)
def evaluate(c,m,cutoff,end,strategy,threshold,users):
 truth=collections.defaultdict(set)
 for u,p in c.execute("SELECT DISTINCT user,item FROM events WHERE kind='transaction' AND at>=? AND at<?",(cutoff,end)):
  if p in m[4] and p not in m[0].get(u,set()):truth[u].add(p)
 precision=[];recall=[];covered=set();cache={}
 for u in users:
  key=frozenset(m[0].get(u,set()))
  if key not in cache:cache[key]=recommendations(m,u,strategy,threshold)
  rec=cache[key];covered|=rec
  if truth[u]:
   n=len(rec&truth[u]);precision.append(n/10);recall.append(n/len(truth[u]))
 return {'precision_at_10':statistics.mean(precision) if precision else None,'recall_at_10':statistics.mean(recall) if recall else None,'coverage':len(covered)/len(m[4]),'eligible_users':len(precision),'population':len(users),'catalog_size':len(m[4]),'covered_items':len(covered),'cold_start_users':sum(u not in m[0] for u in users)}
def main():
 RAW.mkdir(parents=True,exist_ok=True);z=RAW/'events.csv.zip'
 if not z.exists():
  print('Downloading publisher events archive...',flush=True)
  with urllib.request.urlopen(URL,timeout=90) as response,z.open('wb') as dest:
   while chunk:=response.read(1024*1024):dest.write(chunk)
 counts=collections.Counter();total=0;min_at=10**20;max_at=0
 for r in rows(z):
  total+=1;t=int(r['timestamp']);min_at=min(min_at,t);max_at=max(max_at,t)
  if t<VALID:counts[int(r['visitorid'])]+=1
 eligible=[u for u,n in counts.items() if n>=3]
 users=heapq.nsmallest(50000,eligible,key=lambda u:hashlib.sha256(f'13112026:{u}'.encode()).digest());cohort=set(users)
 print('Cohort',len(users),'eligible',len(eligible),flush=True)
 db=DATA/'retailrocket.sqlite'
 if db.exists():db.unlink()
 c=sqlite3.connect(db);c.execute('CREATE TABLE events(at INTEGER,user INTEGER,kind TEXT,item INTEGER,transaction_id TEXT)')
 batch=[]
 for r in rows(z):
  u=int(r['visitorid'])
  if u in cohort:
   batch.append((int(r['timestamp']),u,r['event'],int(r['itemid']),r['transactionid']))
   if len(batch)==10000:c.executemany('INSERT INTO events VALUES(?,?,?,?,?)',batch);batch=[]
 c.executemany('INSERT INTO events VALUES(?,?,?,?,?)',batch);c.execute('CREATE INDEX kind_time ON events(kind,at)');c.execute('CREATE INDEX time_user ON events(at,user)');c.commit()
 validation_model=model(c,VALID);valid={str(n):evaluate(c,validation_model,VALID,TEST,'cooccurrence',n,users) for n in [1,3,5]}
 best=max([1,3,5],key=lambda n:(valid[str(n)]['recall_at_10'] or 0,-n));test_model=model(c,TEST)
 results={'source_url':'https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset','download_url':URL,'accessed':'13.11.2026','license':'CC BY-NC-SA 4.0','raw_archive_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'raw_rows':total,'raw_min_ms':min_at,'raw_max_ms':max_at,'precutoff_eligible':len(eligible),'users':len(users),'sample_rule':'At least 3 events before 2015-08-01 UTC; smallest 50000 SHA256(13112026:visitorid). No future activity used.','events':c.execute('SELECT COUNT(*) FROM events').fetchone()[0],'items':c.execute('SELECT COUNT(DISTINCT item) FROM events').fetchone()[0],'event_types':dict(c.execute('SELECT kind,COUNT(*) FROM events GROUP BY kind')),'valid_cutoff':VALID,'test_cutoff':TEST,'test_end':END,'validation':valid,'selected_min_pair':best,'test':{s:evaluate(c,test_model,TEST,END,s,best,users) for s in ['popularity','cooccurrence']},'synthetic':False,'catalog_rule':'Items observed in selected cohort before prediction cutoff; actual sellability unknown.','limitations':['Cohort overrepresents pre-cutoff active visitors.','Price, quantity, seller, readable item names and exposure logs are not inferred.','Identifiers are visitors, not verified persons; timestamps are historical 2015.','Metrics apply only to users with novel purchases of pre-cutoff-known items.']}
 results['diagnostics']={'test_visitors':c.execute('SELECT COUNT(DISTINCT user) FROM events WHERE at>=? AND at<?',(TEST,END)).fetchone()[0],'test_purchasers':c.execute("SELECT COUNT(DISTINCT user) FROM events WHERE kind='transaction' AND at>=? AND at<?",(TEST,END)).fetchone()[0],'test_transaction_rows':c.execute("SELECT COUNT(*) FROM events WHERE kind='transaction' AND at>=? AND at<?",(TEST,END)).fetchone()[0],'training_purchasers':len(test_model[0])}
 (DATA/'real_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');(DATA/'cohort_ids.csv').write_text('visitorid\n'+'\n'.join(map(str,sorted(users))),encoding='utf-8')
 demo=json.loads((ROOT/'docs/data.json').read_text(encoding='utf-8'));demo['real_results']=results;(ROOT/'docs/data.json').write_text(json.dumps(demo,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print(json.dumps(results,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
