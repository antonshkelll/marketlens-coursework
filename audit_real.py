import json,sqlite3
from real_study import TEST,END,DATA,model
c=sqlite3.connect(DATA/'retailrocket.sqlite')
a={
 'test_visitors':c.execute('SELECT COUNT(DISTINCT user) FROM events WHERE at>=? AND at<?',(TEST,END)).fetchone()[0],
 'test_purchasers':c.execute("SELECT COUNT(DISTINCT user) FROM events WHERE kind='transaction' AND at>=? AND at<?",(TEST,END)).fetchone()[0],
 'test_transaction_rows':c.execute("SELECT COUNT(*) FROM events WHERE kind='transaction' AND at>=? AND at<?",(TEST,END)).fetchone()[0],
 'training_purchasers':len(model(c,TEST)[0])}
r=json.loads((DATA/'real_results.json').read_text(encoding='utf-8'));r['diagnostics']=a;(DATA/'real_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(a)
