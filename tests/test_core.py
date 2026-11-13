import sys, unittest,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiment import connect,history,recommend,split_by_time,TEST,END,ROOT
from server import checkout
class Core(unittest.TestCase):
 def test_sql_python_recommendation_agreement(self):
  with connect() as c:
   for user in [1,42,999]:
    result=c.execute((ROOT/'sql/recommendations.sql').read_text(),{'cutoff':TEST,'user_id':user,'min_pair':1}).fetchall()
    expected=recommend(history(c,TEST),user,'cooccurrence')
    self.assertEqual([r[0] for r in result],[r['product_id'] for r in expected])
 def test_real_model_ignores_future(self):
  from real_study import model,recommendations
  c=sqlite3.connect(':memory:');c.executescript("CREATE TABLE events(at,user,kind,item,transaction_id); INSERT INTO events VALUES(1,1,'transaction',7,'a'),(1,2,'transaction',7,'b'),(1,2,'transaction',8,'b');")
  before=recommendations(model(c,10),1,'cooccurrence',1)
  c.execute("INSERT INTO events VALUES(11,3,'transaction',99,'future')")
  after=model(c,10);self.assertEqual(before,recommendations(after,1,'cooccurrence',1));self.assertNotIn(99,after[4])
 def test_split_boundaries(self):
  a,b=split_by_time([{'at':TEST-1},{'at':TEST},{'at':END-1},{'at':END}],TEST,END)
  self.assertEqual([x['at'] for x in a],[TEST-1]);self.assertEqual([x['at'] for x in b],[TEST,END-1])
 def test_global_future_invariance(self):
  with connect() as c:
   before=recommend(history(c,TEST),1,'cooccurrence')
   try:
    c.execute("INSERT INTO customer_order VALUES(999999,2,NULL,?,'confirmed')",(TEST+1,))
    c.execute('INSERT INTO order_item VALUES(999999,1,1,20,100)')
    self.assertEqual(before,recommend(history(c,TEST),1,'cooccurrence'))
   finally:c.rollback()
 def test_session_boundary_30_minutes(self):
  c=sqlite3.connect(':memory:');c.executescript('CREATE TABLE user_session(session_id,user_id,started_at);CREATE TABLE event(event_id,session_id,event_type_id,product_id,occurred_at);CREATE TABLE raw_event(event_id,user_id,product_id,event_type_id,occurred_at);INSERT INTO raw_event VALUES(1,1,1,1,0),(2,1,1,1,1800),(3,1,1,1,3601),(4,2,1,1,1800);')
  c.executescript((ROOT/'sql/sessionize.sql').read_text());self.assertEqual(c.execute('SELECT session_id FROM event ORDER BY event_id').fetchall(),[(1,),(1,),(2,),(3,)])
 def test_fk_and_quantity(self):
  with connect() as c:
   for statement in ['INSERT INTO offer VALUES(999999,1,999999,100,1)','INSERT INTO order_item VALUES(1,99,1,0,100)','INSERT INTO cart_item VALUES(NULL,1,1)','INSERT INTO order_item VALUES(1,NULL,1,1,100)','INSERT INTO recommendation_item VALUES(NULL,1,1,1.0,\'popularity\',NULL)']:
    with self.assertRaises(sqlite3.IntegrityError):c.execute(statement)
   c.rollback()
 def test_temporal_recommendation_context(self):
  with connect() as c:
   with self.assertRaises(sqlite3.IntegrityError):c.execute('INSERT INTO event(session_id,event_type_id,product_id,occurred_at,run_id) VALUES(1,3,1,0,NULL)')
   c.rollback()
 def test_cold_start_no_duplicates(self):
  with connect() as c:
   r=recommend(history(c,TEST),999,'cooccurrence');self.assertEqual(len(r),10);self.assertEqual(len({x['product_id'] for x in r}),10);self.assertTrue(all(x['reason']=='popularity' for x in r))
 def test_historical_price(self):
  with connect() as c:
   before=c.execute('SELECT unit_price FROM order_item WHERE order_id=1').fetchall()
   c.execute('UPDATE offer SET current_price=current_price+10000 WHERE offer_id IN(SELECT offer_id FROM order_item WHERE order_id=1)')
   self.assertEqual(before,c.execute('SELECT unit_price FROM order_item WHERE order_id=1').fetchall());c.rollback()
 def test_funnel_order(self):
  with connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM funnel WHERE buy_at<=cart_at OR cart_at<=view_at').fetchone()[0],0)
 def test_checkout_server_prices(self):
  with connect() as c:
   result=checkout(c,999,[{'product_id':1,'quantity':2,'price':0}],2000000000)
   expected=c.execute('SELECT MIN(current_price)*2/100.0 FROM offer WHERE product_id=1').fetchone()[0]
   self.assertEqual(result['total'],expected);c.rollback()
 def test_atomic_checkout_rejection(self):
  with connect() as c:
   before=c.execute('SELECT COUNT(*) FROM customer_order').fetchone()[0]
   with self.assertRaises(ValueError):checkout(c,999,[{'product_id':1,'quantity':1},{'product_id':999999,'quantity':1}],2000000000)
   self.assertEqual(c.execute('SELECT COUNT(*) FROM customer_order').fetchone()[0],before);c.rollback()
if __name__=='__main__':unittest.main()
