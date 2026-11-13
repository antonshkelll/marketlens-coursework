"""HTTP security regressions use a temporary database; never alter demo orders."""
import json, tempfile, threading, unittest, http.client, sys
from pathlib import Path
from functools import partial
from contextlib import closing
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from experiment import connect, WEB
class HttpSecurity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.db=Path(cls.tmp.name)/'test.sqlite'
  with closing(connect()) as source,closing(connect(cls.db)) as dest:source.backup(dest)
  cls.mock=patch.object(server,'connect',lambda:connect(cls.db));cls.mock.start()
  class Quiet(server.Handler):
   def log_message(self,*args):pass
  cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(WEB)))
  cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.thread.join();cls.mock.stop();cls.tmp.cleanup()
 def request(self,path,method='GET',body=None,headers=None):
  c=http.client.HTTPConnection('127.0.0.1',self.http.server_port,timeout=15)
  payload=json.dumps(body) if body is not None else None
  h={'Content-Type':'application/json'};h.update(headers or {})
  c.request(method,path,body=payload,headers=h);r=c.getresponse();status=r.status;data=r.read();c.close();return status,data
 def test_get_recommend_cannot_write(self):
  with closing(connect(self.db)) as c:before=c.execute('select count(*) from recommendation_run').fetchone()[0]
  self.assertEqual(self.request('/api/recommend?user=1')[0],405)
  with closing(connect(self.db)) as c:self.assertEqual(before,c.execute('select count(*) from recommendation_run').fetchone()[0])
 def test_rebinding_host_rejected(self):
  for method in ['GET','POST']:
   self.assertEqual(self.request('/api/health',method,{'user_id':1} if method=='POST' else None,{'Host':'attacker.example'})[0],403)
 def test_cross_origin_and_malformed_origin_rejected(self):
  for origin in ['https://attacker.example','http://[']:
   self.assertEqual(self.request('/api/recommend','POST',{'user_id':1},{'Origin':origin})[0],403)
 def test_json_required(self):
  self.assertEqual(self.request('/api/recommend','POST',{'user_id':1},{'Content-Type':'text/plain'})[0],415)
 def test_malformed_payloads_rejected(self):
  for body in [[],{'user_id':True},{'user_id':1.5},{'user_id':1,'items':[[]]},{'user_id':1,'items':[{'product_id':1,'quantity':1.5}]}]:
   self.assertEqual(self.request('/api/checkout','POST',body)[0],400)
 def test_valid_recommendation_post(self):
  status,body=self.request('/api/recommend','POST',{'user_id':999});self.assertEqual(status,200);self.assertEqual(len(json.loads(body)['recommendations']),10)
 def test_javascript_mime_with_nosniff(self):
  c=http.client.HTTPConnection("127.0.0.1",self.http.server_port,timeout=15);c.request("GET","/app.js");r=c.getresponse();self.assertEqual(r.status,200);self.assertTrue(r.getheader("Content-Type").startswith("text/javascript"));self.assertEqual(r.getheader("X-Content-Type-Options"),"nosniff");r.read();c.close()
 def test_private_files_not_served(self):
  self.assertEqual(self.request('/../data/marketlens.sqlite')[0],404)
if __name__=='__main__':unittest.main()
