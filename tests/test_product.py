"""Run from project root: python -m unittest discover -s tests -v"""
import http.cookiejar
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

class ProductSmokeTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory()
  sock=socket.socket();sock.bind(('127.0.0.1',0));cls.port=sock.getsockname()[1];sock.close()
  cls.base=f'http://127.0.0.1:{cls.port}'
  env=os.environ.copy();env.update(COFFEE_RUSH_PORT=str(cls.port),COFFEE_RUSH_DB=str(Path(cls.tmp.name)/'test.sqlite3'),COFFEE_RUSH_STAFF_PIN='a-unique-test-pin')
  cls.proc=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  for _ in range(80):
   try:
    urllib.request.urlopen(cls.base+'/api/config',timeout=.5)
    break
   except Exception:time.sleep(.1)
  else:raise RuntimeError('Test server did not start')
 @classmethod
 def tearDownClass(cls):
  cls.proc.terminate()
  try:cls.proc.wait(timeout=5)
  except subprocess.TimeoutExpired:cls.proc.kill()
  cls.tmp.cleanup()
 def make_client(self):return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def call(self,client,path,payload=None,expected_error=None):
  data=json.dumps(payload).encode() if payload is not None else None
  request=urllib.request.Request(self.base+path,data=data,headers={'Content-Type':'application/json'} if data else {})
  try:
   with client.open(request,timeout=5) as r:return json.loads(r.read())
  except urllib.error.HTTPError as error:
   if expected_error:
    self.assertEqual(error.code,expected_error)
    return json.loads(error.read())
   raise
 def finish_round(self,client,mode='ranked'):
  round=self.call(client,'/api/round/start',{'mode':mode,'seconds':60})
  for i,ch in enumerate(round['guests']):
   self.assertEqual(self.call(client,'/api/round/ready',{'roundId':round['roundId']})['index'],i)
   result=self.call(client,'/api/round/serve',{'roundId':round['roundId'],'picks':ch['recipe']})
   self.assertTrue(result['exact'])
   if i==0:
    # Anti-double-submit: the same order cannot be scored a second time.
    error=self.call(client,'/api/round/serve',{'roundId':round['roundId'],'picks':ch['recipe']},409)
    self.assertIn('already',error['error'])
   done=self.call(client,'/api/round/advance',{'roundId':round['roundId']})
  return done
 def test_account_game_rankings_rewards(self):
  a=self.make_client();b=self.make_client();anon=self.make_client()
  cfg=self.call(anon,'/api/config')
  self.assertEqual(len(cfg['characters']),6)
  self.assertEqual(len(cfg['rewards']),4)
  self.assertIsNone(self.call(anon,'/api/me')['member'])
  self.call(a,'/api/auth/register',{'name':'Playtest_A','password':'test-password-A'})
  self.call(b,'/api/auth/register',{'name':'Playtest_B','password':'test-password-B'})
  self.call(anon,'/api/auth/login',{'name':'Playtest_A','password':'wrongpassword'},401)
  self.call(anon,'/api/round/start',{'mode':'ranked'},401)
  first=self.finish_round(a)
  self.assertTrue(first['done'])
  self.assertEqual(first['perfect'],5)
  self.assertEqual(first['earned'],20)
  self.assertEqual(first['member']['points'],20)
  self.assertGreaterEqual(first['score'],700)
  another=self.finish_round(a)
  self.assertEqual(another['earned'],10) # 30/day ceiling
  third=self.finish_round(a)
  self.assertEqual(third['earned'],0)
  self.assertEqual(third['member']['points'],30)
  result_b=self.finish_round(b)
  self.assertEqual(result_b['earned'],20)
  leaders=self.call(anon,'/api/leaderboard?period=weekly')['entries']
  self.assertEqual(len(leaders),2)
  self.assertEqual({x['name'] for x in leaders},{'Playtest_A','Playtest_B'})
  practice=self.finish_round(b,'practice')
  self.assertFalse(practice['ranked'])
  self.assertEqual(practice['earned'],0)
  self.assertEqual(self.call(b,'/api/me')['member']['points'],20)
  voucher=self.call(a,'/api/rewards/redeem',{'rewardId':'syrup'})
  self.assertEqual(voucher['member']['points'],20)
  code=voucher['voucherCode']
  self.assertTrue(code.startswith('CR-'))
  self.call(anon,'/api/staff/redeem',{'pin':'wrong','code':code},403)
  success=self.call(anon,'/api/staff/redeem',{'pin':'a-unique-test-pin','code':code})
  self.assertTrue(success['ok'])
  self.call(anon,'/api/staff/redeem',{'pin':'a-unique-test-pin','code':code},409)
  self.call(a,'/api/auth/logout',{})
  self.assertIsNone(self.call(a,'/api/me')['member'])
  self.call(a,'/api/auth/login',{'name':'Playtest_A','password':'test-password-A'})
  self.assertEqual(self.call(a,'/api/me')['member']['points'],20)

if __name__=='__main__':unittest.main()
