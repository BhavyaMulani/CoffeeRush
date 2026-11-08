#!/usr/bin/env python3
"""Coffee Rush: Anime Edition - shared local community game server.
Python 3.10+ standard library only. A demo-classroom implementation; not a hosted
production loyalty platform or a replacement for POS/member verification.
"""
import hashlib, hmac, http.cookies, http.server, json, mimetypes, os, pathlib, re
import secrets, sqlite3, threading, time, urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent
STATIC = ROOT / 'public'
DB = pathlib.Path(os.environ.get('COFFEE_RUSH_DB', str(ROOT / 'coffee_rush.sqlite3')))
HOST = os.environ.get('COFFEE_RUSH_HOST', '127.0.0.1')
PORT = int(os.environ.get('COFFEE_RUSH_PORT', '8765'))
STAFF_PIN = os.environ.get('COFFEE_RUSH_STAFF_PIN', '')
SECURE_COOKIES = os.environ.get('COFFEE_RUSH_HTTPS', '0') == '1'
TORONTO = ZoneInfo('America/Toronto')
LOCK = threading.RLock()
RECIPE_FIELDS = ['base', 'temp', 'milk', 'syrup', 'topping']
INGREDIENTS = {'base':['Espresso','Latte','Cappuccino','Mocha'], 'temp':['Hot','Iced','Blended'], 'milk':['None','Whole','Oat','Almond'], 'syrup':['None','Vanilla','Caramel','Hazelnut'], 'topping':['None','Cold foam','Whipped cream','Cinnamon']}
CHARS = [
 {'id':'kaien','name':'Kaien','alias':'The Starlight Guardian','color':'#8ed5e6','hair':'#dceaff','skin':'#f2c7ab','coat':'#253b60','style':'spiky','story':['I watched over a city of stars, but I could not protect every wish.','Tonight I am learning that even guardians need somewhere to rest.'],'farewell':'Maybe the brightest promises are the ones we share.','drink':'Starlight Iced Latte','recipe':['Latte','Iced','Oat','Vanilla','Cold foam']},
 {'id':'rumi','name':'Rumi','alias':'The Horizon Chaser','color':'#ffa487','hair':'#bb5d43','skin':'#f4c3a0','coat':'#7b3736','style':'swept','story':['I sailed beyond the last page of my map to find a treasure nobody believed in.','The best part was not the treasure. It was the friends who sailed beside me.'],'farewell':'The next island can wait. This story deserves a little time.','drink':'Caramel Cloud Frappé','recipe':['Mocha','Blended','Whole','Caramel','Whipped cream']},
 {'id':'renji','name':'Renji','alias':'The Wayward Blade','color':'#93abc9','hair':'#354564','skin':'#dca98d','coat':'#48505f','style':'layered','story':['I have crossed a hundred roads searching for the person I promised to become.','I always take the wrong turn. Sometimes it leads me to the right people.'],'farewell':'I may be lost, but I know why I travel.','drink':'Wanderer Double Espresso','recipe':['Espresso','Hot','None','None','None']},
 {'id':'sora','name':'Sora','alias':'The Sky Librarian','color':'#d3b3ff','hair':'#b69ad9','skin':'#f0c5b5','coat':'#5a5489','style':'long','story':['I collect unwritten stories from rooftops at sunset.','Every forgotten dream becomes a constellation in my secret library.'],'farewell':'Tonight this café gets a chapter of its own.','drink':'Cinnamon Crown Cappuccino','recipe':['Cappuccino','Hot','Almond','Hazelnut','Cinnamon']},
 {'id':'mika','name':'Mika','alias':'The Neon Inventor','color':'#c5e4a4','hair':'#d9b46f','skin':'#eec7a4','coat':'#53715d','style':'tufted','story':['I invented a machine to replay yesterday, but it only showed my mistakes.','So I rebuilt it to remind me that tomorrow can be different.'],'farewell':'My next experiment is a fresh start in a cup.','drink':'Neon Iced Mocha','recipe':['Mocha','Iced','Whole','None','Whipped cream']},
 {'id':'yori','name':'Yori','alias':'The Moonlit Musician','color':'#cba1e8','hair':'#4a3769','skin':'#e5b5a0','coat':'#503052','style':'long','story':['Every song I write is a letter I never managed to send.','I leave a quiet space in each melody for an answer I may hear someday.'],'farewell':'Maybe the last note is the first line of a new story.','drink':'Moonlight Vanilla Latte','recipe':['Latte','Hot','Oat','Vanilla','Cold foam']},
]
CH_BY_ID = {c['id']:c for c in CHARS}
REWARDS = [
 {'id':'syrup','icon':'🍯','name':'Syrup upgrade','cost':10,'description':'One free flavour syrup upgrade (demo voucher).'},
 {'id':'shot','icon':'☕','name':'Extra espresso shot','cost':15,'description':'One extra espresso shot (demo voucher).'},
 {'id':'cookie','icon':'🍪','name':'Cookie with a drink','cost':25,'description':'One cookie with beverage purchase (demo voucher).'},
 {'id':'discount','icon':'🎟️','name':'10% off one drink','cost':40,'description':'Discount on one eligible beverage (demo voucher).'},
]
BADGES = [('first','🌱','First Chapter'),('fivehundred','⚡','Rush Regular'),('perfect','⭐','Perfect Pour'),('three','🏅','Café Regular'),('champion','👑','Rush Champion')]


def db_conn():
 c=sqlite3.connect(DB, timeout=15)
 c.row_factory=sqlite3.Row
 c.execute('PRAGMA busy_timeout=15000')
 c.execute('PRAGMA foreign_keys=ON')
 return c


def init_db():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with db_conn() as c:
  c.executescript('''
  CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL, pass_salt TEXT NOT NULL,
    pass_hash TEXT NOT NULL, points INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL);
  CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name ON users(name COLLATE NOCASE);
  CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id));
  CREATE TABLE IF NOT EXISTS rounds(id TEXT PRIMARY KEY, user_id TEXT NOT NULL, guests TEXT NOT NULL,
    current INTEGER NOT NULL DEFAULT 0, phase TEXT NOT NULL DEFAULT 'story', score INTEGER NOT NULL DEFAULT 0,
    perfect INTEGER NOT NULL DEFAULT 0, streak INTEGER NOT NULL DEFAULT 0, started REAL NOT NULL DEFAULT 0,
    seconds INTEGER NOT NULL DEFAULT 30, ranked INTEGER NOT NULL DEFAULT 1,
    created REAL NOT NULL, finished INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id));
  CREATE TABLE IF NOT EXISTS scores(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
    score INTEGER NOT NULL, perfect INTEGER NOT NULL, played REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id));
  CREATE TABLE IF NOT EXISTS points_earned(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
    day TEXT NOT NULL, amount INTEGER NOT NULL, round_id TEXT UNIQUE NOT NULL);
  CREATE TABLE IF NOT EXISTS vouchers(id TEXT PRIMARY KEY, user_id TEXT NOT NULL, reward_id TEXT NOT NULL,
    reward_name TEXT NOT NULL, cost INTEGER NOT NULL, created REAL NOT NULL, used REAL,
    FOREIGN KEY(user_id) REFERENCES users(id));
  ''')


def public_char(c):
 return {k:v for k,v in c.items() if k!='recipe'} | {'recipe':dict(zip(RECIPE_FIELDS,c['recipe']))}


def user_payload(c,user_id):
 u=c.execute('SELECT id,name,points FROM users WHERE id=?',(user_id,)).fetchone()
 if not u:return None
 played=c.execute('SELECT COUNT(*) n FROM scores WHERE user_id=?',(user_id,)).fetchone()['n']
 badges=['first'] if played else []
 if c.execute('SELECT 1 FROM scores WHERE user_id=? AND score>=500 LIMIT 1',(user_id,)).fetchone():badges.append('fivehundred')
 if c.execute('SELECT 1 FROM scores WHERE user_id=? AND perfect=5 LIMIT 1',(user_id,)).fetchone():badges.append('perfect')
 if played>=3:badges.append('three')
 if c.execute('SELECT 1 FROM scores WHERE user_id=? AND score>=700 LIMIT 1',(user_id,)).fetchone():badges.append('champion')
 vouchers=[dict(v) for v in c.execute('SELECT id,reward_name,cost,created,used FROM vouchers WHERE user_id=? ORDER BY created DESC LIMIT 12',(user_id,))]
 return {'id':u['id'],'name':u['name'],'points':u['points'],'played':played,'badges':badges,'vouchers':vouchers}


def cutoff(period):
 now=datetime.now(TORONTO)
 if period=='weekly':
  start=now.replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=now.weekday())
 elif period=='monthly':start=now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
 elif period=='all':return 0
 else:raise ValueError('Unknown period')
 return start.timestamp()


def leaderboard(c, period):
 rows=c.execute('''SELECT u.id,u.name,MAX(s.score) AS best,COUNT(s.id) plays
 FROM scores s JOIN users u ON u.id=s.user_id WHERE s.played>=?
 GROUP BY u.id,u.name ORDER BY best DESC,u.name COLLATE NOCASE LIMIT 100''',(cutoff(period),)).fetchall()
 return [{'id':r['id'],'name':r['name'],'score':r['best'],'plays':r['plays']} for r in rows]


class AppError(Exception):
 def __init__(self,msg,status=400):self.msg,self.status=msg,status


class Handler(http.server.BaseHTTPRequestHandler):
 server_version='CoffeeRush/1.0'
 def log_message(self, fmt, *args):
  print('[%s] %s'%(self.log_date_time_string(),fmt%args))
 def reply(self, obj, status=200, cookie=None):
  payload=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
  self.send_response(status)
  self.send_header('Content-Type','application/json; charset=utf-8')
  self.send_header('Content-Length',str(len(payload)))
  self.send_header('Cache-Control','no-store')
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('X-Frame-Options','DENY')
  self.send_header('Referrer-Policy','no-referrer')
  if cookie:self.send_header('Set-Cookie', cookie)
  self.end_headers();self.wfile.write(payload)
 def fail(self,error):self.reply({'error':error.msg},error.status)
 def route_path(self):return urllib.parse.urlsplit(self.path).path
 def cookie_header(self, token='',clear=False):
  opts=f"cr_session={token}; Path=/; HttpOnly; SameSite=Strict; "+('Secure; ' if SECURE_COOKIES else '')
  return opts+('Max-Age=0' if clear else 'Max-Age=604800')
 def current_user(self,c):
  raw=self.headers.get('Cookie','')
  cookies=http.cookies.SimpleCookie()
  try:cookies.load(raw)
  except http.cookies.CookieError:return None
  morsel=cookies.get('cr_session')
  if not morsel:return None
  token=morsel.value
  if not re.fullmatch(r'[a-f0-9]{64}',token):return None
  row=c.execute('SELECT user_id FROM sessions WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
  return row['user_id'] if row else None
 def auth(self,c):
  user_id=self.current_user(c)
  if user_id is None:raise AppError('Log in to continue.',401)
  return user_id
 def body(self):
  size=int(self.headers.get('Content-Length','0'))
  if size>16384:raise AppError('Request is too large.',413)
  try:data=json.loads(self.rfile.read(size).decode('utf-8')) if size else {}
  except (ValueError,UnicodeDecodeError):raise AppError('Invalid JSON.')
  if not isinstance(data,dict):raise AppError('Expected an object.')
  return data
 def do_GET(self):
  path=self.route_path()
  try:
   if path.startswith('/api/'):
    with db_conn() as c:
     if path=='/api/config':self.reply({'characters':[public_char(x) for x in CHARS],'ingredients':INGREDIENTS,'rewards':REWARDS,'badges':[{'id':i,'icon':e,'name':n} for i,e,n in BADGES]});return
     if path=='/api/me':
      uid=self.current_user(c);self.reply({'member':user_payload(c,uid) if uid else None});return
     if path=='/api/leaderboard':
      period=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('period',['weekly'])[0]
      self.reply({'period':period,'entries':leaderboard(c,period)});return
    raise AppError('API endpoint not found.',404)
   return self.serve_static(path)
  except AppError as e:self.fail(e)
  except (OSError,sqlite3.Error,ValueError) as e:print('SERVER ERROR',repr(e));self.reply({'error':'Server request failed.'},500)
 def serve_static(self,path):
  path=urllib.parse.unquote(path)
  if path=='/':path='/index.html'
  candidate=(STATIC/path.lstrip('/')).resolve()
  if not candidate.is_relative_to(STATIC.resolve()) or not candidate.is_file():raise AppError('File not found.',404)
  data=candidate.read_bytes();ctype=mimetypes.guess_type(str(candidate))[0] or 'application/octet-stream'
  self.send_response(200);self.send_header('Content-Type',ctype+('; charset=utf-8' if ctype.startswith('text/') or ctype=='application/javascript' else ''))
  self.send_header('Content-Length',str(len(data)))
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('X-Frame-Options','DENY')
  self.end_headers();self.wfile.write(data)
 def do_POST(self):
  path=self.route_path()
  try:
   if not path.startswith('/api/'):raise AppError('Endpoint not found.',404)
   origin=self.headers.get('Origin')
   host=self.headers.get('Host','')
   if origin and urllib.parse.urlsplit(origin).netloc!=host:raise AppError('Cross-site requests not allowed.',403)
   data=self.body()
   with LOCK:
    with db_conn() as c:
     c.execute('BEGIN IMMEDIATE')
     if path in ('/api/auth/register','/api/auth/login'):
      name=str(data.get('name','')).strip()
      pwd=data.get('password','')
      if not isinstance(pwd,str) or len(pwd)<8 or len(pwd)>128:raise AppError('Password must have 8–128 characters.')
      if not re.fullmatch(r'[A-Za-z0-9_]{3,18}',name):raise AppError('Nickname must be 3–18 letters, numbers or underscores.')
      u=c.execute('SELECT * FROM users WHERE name=? COLLATE NOCASE',(name,)).fetchone()
      if path.endswith('register'):
       if u:raise AppError('Nickname already taken. Sign in or choose another.',409)
       uid=secrets.token_hex(12);salt=secrets.token_hex(16)
       digest=hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(salt),220000).hex()
       c.execute('INSERT INTO users(id,name,pass_salt,pass_hash,created) VALUES(?,?,?,?,?)',(uid,name,salt,digest,time.time()))
      else:
       if not u:raise AppError('Incorrect nickname or password.',401)
       uid=u['id'];digest=hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(u['pass_salt']),220000).hex()
       if not hmac.compare_digest(digest,u['pass_hash']):raise AppError('Incorrect nickname or password.',401)
      token=secrets.token_hex(32)
      c.execute('INSERT INTO sessions(token_hash,user_id,expires) VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),uid,time.time()+604800))
      c.commit();self.reply({'member':user_payload(c,uid)},cookie=self.cookie_header(token));return
     if path=='/api/auth/logout':
      raw=self.headers.get('Cookie','');cookies=http.cookies.SimpleCookie();cookies.load(raw)
      if cookies.get('cr_session'):c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(cookies['cr_session'].value.encode()).hexdigest(),))
      c.commit();self.reply({'ok':True},cookie=self.cookie_header(clear=True));return
     if path=='/api/staff/redeem':
      pin=data.get('pin','');code=str(data.get('code','')).strip().upper()
      if not STAFF_PIN:raise AppError('Staff validation is not enabled. Set COFFEE_RUSH_STAFF_PIN.',503)
      if not isinstance(pin,str) or not hmac.compare_digest(pin,STAFF_PIN):raise AppError('Invalid staff PIN.',403)
      v=c.execute('SELECT * FROM vouchers WHERE id=?',(code,)).fetchone()
      if not v:raise AppError('No voucher with that code.',404)
      if v['used']:raise AppError('Voucher already used.',409)
      c.execute('UPDATE vouchers SET used=? WHERE id=? AND used IS NULL',(time.time(),code));c.commit()
      self.reply({'ok':True,'reward':v['reward_name'],'code':code,'status':'demo redemption only'});return
     uid=self.auth(c)
     if path=='/api/round/start':
      mode=data.get('mode','ranked');ranked=mode=='ranked'
      if mode not in ('ranked','practice'):raise AppError('Invalid mode.')
      seconds=30 if ranked else int(data.get('seconds',45))
      if seconds not in (25,30,45,60):raise AppError('Select a valid practice timer.')
      choices=[x['id'] for x in secrets.SystemRandom().sample(CHARS,5)]
      rid=secrets.token_hex(16)
      c.execute('INSERT INTO rounds(id,user_id,guests,seconds,ranked,created) VALUES(?,?,?,?,?,?)',(rid,uid,json.dumps(choices),seconds,int(ranked),time.time()))
      c.commit();self.reply({'roundId':rid,'guests':[public_char(CH_BY_ID[i]) for i in choices],'score':0,'perfect':0,'index':0,'seconds':seconds,'ranked':ranked});return
     if path.startswith('/api/round/'):
      rid=str(data.get('roundId',''))
      r=c.execute('SELECT * FROM rounds WHERE id=? AND user_id=?',(rid,uid)).fetchone()
      if not r or r['finished']:raise AppError('This round is no longer active.',404)
      if time.time()-r['created']>7200:raise AppError('This game session expired. Start again.',410)
      ids=json.loads(r['guests']);idx=r['current'];guest=CH_BY_ID[ids[idx]]
      duration=max(18,r['seconds']-idx*2)
      if path=='/api/round/ready':
       if r['phase']!='story':raise AppError('Not ready to start brewing.',409)
       c.execute("UPDATE rounds SET phase='brew',started=? WHERE id=?",(time.time(),rid));c.commit()
       self.reply({'duration':duration,'index':idx});return
      if path=='/api/round/serve':
       if r['phase']!='brew':raise AppError('This order was already submitted.',409)
       elapsed=max(0,time.time()-r['started']);expired=elapsed>=duration
       picks=data.get('picks',{})
       if not isinstance(picks,dict):raise AppError('Invalid ingredient selections.')
       if not expired:
        if set(picks)!=set(RECIPE_FIELDS):raise AppError('Select all five ingredients.')
        if any(picks[k] not in INGREDIENTS[k] for k in RECIPE_FIELDS):raise AppError('Invalid ingredient choice.')
       matches=0 if expired else sum(picks[k]==guest['recipe'][j] for j,k in enumerate(RECIPE_FIELDS))
       exact=matches==5;speed=round(50*max(0,duration-elapsed)/duration) if exact else 0
       combo=25 if exact and r['streak']>=1 else 0
       gain=100+speed+combo if exact else 20*matches
       streak=r['streak']+1 if exact else 0
       c.execute("UPDATE rounds SET phase='feedback',score=score+?,perfect=perfect+?,streak=? WHERE id=?",(gain,int(exact),streak,rid))
       c.commit();self.reply({'gain':gain,'speed':speed,'combo':combo,'exact':exact,'correctCount':matches,'expired':expired,'score':r['score']+gain,'perfect':r['perfect']+int(exact),'streak':streak});return
      if path=='/api/round/advance':
       if r['phase']!='feedback':raise AppError('Finish this order first.',409)
       if idx<4:
        c.execute("UPDATE rounds SET current=current+1,phase='story',started=0 WHERE id=?",(rid,));c.commit();self.reply({'done':False,'index':idx+1});return
       c.execute('UPDATE rounds SET finished=1 WHERE id=?',(rid,))
       earned=0;planned=0
       if r['ranked']:
        c.execute('INSERT INTO scores(user_id,score,perfect,played) VALUES(?,?,?,?)',(uid,r['score'],r['perfect'],time.time()))
        planned=5+(10 if r['score']>=500 else 0)+(5 if r['perfect']==5 else 0)
        day=datetime.now(TORONTO).strftime('%Y-%m-%d')
        already=c.execute('SELECT COALESCE(SUM(amount),0) n FROM points_earned WHERE user_id=? AND day=?',(uid,day)).fetchone()['n']
        earned=max(0,min(planned,30-already))
        c.execute('INSERT INTO points_earned(user_id,day,amount,round_id) VALUES(?,?,?,?)',(uid,day,earned,rid))
        c.execute('UPDATE users SET points=points+? WHERE id=?',(earned,uid))
       c.commit()
       board=leaderboard(c,'weekly') if r['ranked'] else []
       position=next((j+1 for j,x in enumerate(board) if x['id']==uid),None)
       self.reply({'done':True,'score':r['score'],'perfect':r['perfect'],'planned':planned,'earned':earned,'rank':position,'ranked':bool(r['ranked']),'member':user_payload(c,uid)});return
      raise AppError('Unknown round endpoint.',404)
     if path=='/api/rewards/redeem':
      reward=next((x for x in REWARDS if x['id']==data.get('rewardId')),None)
      if not reward:raise AppError('Unknown reward.',404)
      changed=c.execute('UPDATE users SET points=points-? WHERE id=? AND points>=?',(reward['cost'],uid,reward['cost'])).rowcount
      if not changed:raise AppError('Not enough loyalty points.',409)
      code='CR-'+secrets.token_hex(5).upper()
      c.execute('INSERT INTO vouchers(id,user_id,reward_id,reward_name,cost,created) VALUES(?,?,?,?,?,?)',(code,uid,reward['id'],reward['name'],reward['cost'],time.time()))
      c.commit();self.reply({'voucherCode':code,'reward':reward['name'],'member':user_payload(c,uid),'notice':'Demonstration voucher; not accepted by real cafés.'});return
     raise AppError('Unknown API endpoint.',404)
  except AppError as e:self.fail(e)
  except (ValueError,TypeError):self.reply({'error':'Invalid request.'},400)
  except (OSError,sqlite3.Error) as e:print('SERVER ERROR',repr(e));self.reply({'error':'Server request failed.'},500)


def main():
 init_db()
 print('✦ THE UNWRITTEN CAFÉ — Coffee Rush: Anime Edition')
 print(f'Game: http://127.0.0.1:{PORT}')
 if HOST=='0.0.0.0':print('LAN demo enabled; connect using your computer IPv4 address and port. Avoid public internet without HTTPS.')
 if not STAFF_PIN:print('Staff voucher validation disabled. Set COFFEE_RUSH_STAFF_PIN to enable it.')
 http.server.ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

if __name__=='__main__':main()
