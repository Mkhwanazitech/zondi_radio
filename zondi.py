# ZONDI V7.1 FINAL - FIXED FOR YOUR SCREENSHOTS
from flask import Flask, request, jsonify, session, send_from_directory, render_template, redirect
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, random, re, time, uuid, sqlite3

app = Flask(__name__)
app.secret_key = "ZONDI_V7_1_FIXED_2026"
# ZONDI V7.1 FINAL - FIXED FOR YOUR SCREENSHOTS
from flask import Flask, request, jsonify, session, send_from_directory, render_template, redirect
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, random, re, time, uuid, sqlite3

app = Flask(__name__)
app.secret_key = "ZONDI_V7_1_FIXED_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DEV_PASSWORD = "Zondi@123"
DB_PATH = "zondi.db"
BACKUP_JSON = "users.json"
EVIDENCE_DIR = "static/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs("backups", exist_ok=True)

def init_db():
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, cell TEXT UNIQUE, cell_normalized TEXT UNIQUE, password_hash TEXT, role TEXT, email TEXT, verified INTEGER, created TEXT, last_login TEXT, online INTEGER DEFAULT 0, last_seen INTEGER DEFAULT 0, blocked_users TEXT DEFAULT '[]')")
    c.execute("CREATE TABLE IF NOT EXISTS otp_store (key TEXT PRIMARY KEY, otp TEXT, expiry INTEGER, username TEXT, cell TEXT, data TEXT, attempts INTEGER DEFAULT 0, type TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS locations (username TEXT PRIMARY KEY, lat REAL, lng REAL, updated_at INTEGER, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, sender TEXT, sender_role TEXT, type TEXT, text TEXT, chat_id TEXT, reply_to TEXT, file_url TEXT, file_name TEXT, edited INTEGER DEFAULT 0, deleted_for TEXT DEFAULT '[]', deleted_everyone INTEGER DEFAULT 0, reactions TEXT DEFAULT '{}', read_by TEXT DEFAULT '[]', pinned INTEGER DEFAULT 0, timestamp INTEGER, time_str TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS panic_alerts (id TEXT PRIMARY KEY, username TEXT, cell TEXT, lat REAL, lng REAL, status TEXT, timestamp INTEGER, time_str TEXT, accepted_by TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS groups (id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, icon TEXT, created_by TEXT, members TEXT DEFAULT '[]', timestamp INTEGER)")
    con.commit()
    # AUTO-CREATE YOUR 3 GROUPS FROM SCREENSHOTS IF NOT EXIST
    c.execute("SELECT COUNT(*) FROM groups")
    if c.fetchone()[0]==0:
        default_groups = [
            ("group_command", "Command", "🏛️ HQ Command", "🏛️", "system"),
            ("group_patrol", "Patrol Unit", "🚓 Patrol Unit", "🚓", "system"),
            ("group_tactical", "Tactical", "⚡ Tactical Response", "⚡", "system"),
            ("group_central", "ZONDI CENTRAL", "Main group", "🟢", "system"),
            ("emergency", "EMERGENCY", "Panic alerts", "🚨", "system"),
        ]
        for gid, name, desc, icon, by in default_groups:
            c.execute("INSERT OR IGNORE INTO groups (id,name,description,icon,created_by,members,timestamp) VALUES (?,?,?,?,?,?,?)", (gid, name, desc, icon, by, json.dumps([]), int(time.time())))
        con.commit()
    con.close()
init_db()

def db():
    con=sqlite3.connect(DB_PATH)
    con.row_factory=sqlite3.Row
    return con

def backup_users():
    try:
        con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users"); d={r['username']:dict(r) for r in cur.fetchall()}
        open(BACKUP_JSON,'w').write(json.dumps(d,indent=2)); con.close()
    except: pass

def normalize_cell(c): c=str(c).strip().replace(" ",""); return "0"+c[3:] if c.startswith("+27") else c
def validate_cell(c): return re.match(r'^(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})$', str(c).strip().replace(" ","")) is not None
def gen_otp(): return str(random.randint(100000,999999))
def gen_id(): return uuid.uuid4().hex[:8]
online_users={}
# ZONDI V7.1 FINAL - FIXED FOR YOUR SCREENSHOTS
from flask import Flask, request, jsonify, session, send_from_directory, render_template, redirect
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, random, re, time, uuid, sqlite3

app = Flask(__name__)
app.secret_key = "ZONDI_V7_1_FIXED_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DEV_PASSWORD = "Zondi@123"
DB_PATH = "zondi.db"
BACKUP_JSON = "users.json"
EVIDENCE_DIR = "static/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs("backups", exist_ok=True)

def init_db():
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, cell TEXT UNIQUE, cell_normalized TEXT UNIQUE, password_hash TEXT, role TEXT, email TEXT, verified INTEGER, created TEXT, last_login TEXT, online INTEGER DEFAULT 0, last_seen INTEGER DEFAULT 0, blocked_users TEXT DEFAULT '[]')")
    c.execute("CREATE TABLE IF NOT EXISTS otp_store (key TEXT PRIMARY KEY, otp TEXT, expiry INTEGER, username TEXT, cell TEXT, data TEXT, attempts INTEGER DEFAULT 0, type TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS locations (username TEXT PRIMARY KEY, lat REAL, lng REAL, updated_at INTEGER, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, sender TEXT, sender_role TEXT, type TEXT, text TEXT, chat_id TEXT, reply_to TEXT, file_url TEXT, file_name TEXT, edited INTEGER DEFAULT 0, deleted_for TEXT DEFAULT '[]', deleted_everyone INTEGER DEFAULT 0, reactions TEXT DEFAULT '{}', read_by TEXT DEFAULT '[]', pinned INTEGER DEFAULT 0, timestamp INTEGER, time_str TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS panic_alerts (id TEXT PRIMARY KEY, username TEXT, cell TEXT, lat REAL, lng REAL, status TEXT, timestamp INTEGER, time_str TEXT, accepted_by TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS groups (id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, icon TEXT, created_by TEXT, members TEXT DEFAULT '[]', timestamp INTEGER)")
    con.commit()
    # AUTO-CREATE YOUR 3 GROUPS FROM SCREENSHOTS IF NOT EXIST
    c.execute("SELECT COUNT(*) FROM groups")
    if c.fetchone()[0]==0:
        default_groups = [
            ("group_command", "Command", "🏛️ HQ Command", "🏛️", "system"),
            ("group_patrol", "Patrol Unit", "🚓 Patrol Unit", "🚓", "system"),
            ("group_tactical", "Tactical", "⚡ Tactical Response", "⚡", "system"),
            ("group_central", "ZONDI CENTRAL", "Main group", "🟢", "system"),
            ("emergency", "EMERGENCY", "Panic alerts", "🚨", "system"),
        ]
        for gid, name, desc, icon, by in default_groups:
            c.execute("INSERT OR IGNORE INTO groups (id,name,description,icon,created_by,members,timestamp) VALUES (?,?,?,?,?,?,?)", (gid, name, desc, icon, by, json.dumps([]), int(time.time())))
        con.commit()
    con.close()
init_db()

def db():
    con=sqlite3.connect(DB_PATH)
    con.row_factory=sqlite3.Row
    return con

def backup_users():
    try:
        con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users"); d={r['username']:dict(r) for r in cur.fetchall()}
        open(BACKUP_JSON,'w').write(json.dumps(d,indent=2)); con.close()
    except: pass

def normalize_cell(c): c=str(c).strip().replace(" ",""); return "0"+c[3:] if c.startswith("+27") else c
def validate_cell(c): return re.match(r'^(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})$', str(c).strip().replace(" ","")) is not None
def gen_otp(): return str(random.randint(100000,999999))
def gen_id(): return uuid.uuid4().hex[:8]
online_users={}

def find_user(login_id):
    con=db(); cur=con.cursor()
    ln=normalize_cell(login_id) if login_id.replace("+","").replace(" ","").isdigit() else login_id.strip()
    cur.execute("SELECT * FROM users WHERE username=? OR cell=? OR cell_normalized=?", (ln, login_id.strip(), ln))
    r=cur.fetchone(); con.close(); return dict(r) if r else None

def ai_dispatch(pdata):
    con=db(); cur=con.cursor(); mid=gen_id()
    cur.execute("SELECT username FROM locations WHERE role='patrol' ORDER BY updated_at DESC LIMIT 1"); r=cur.fetchone()
    nearest=r['username'] if r else "nearest unit"
    txt=f"🤖 ZONDI-AI: PANIC {pdata['username']} ({pdata['cell']}) at {pdata['lat']:.4f},{pdata['lng']:.4f}. {nearest} dispatched."
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(mid,"ZONDI-AI","ai","text",txt,"emergency",int(time.time()),datetime.now().strftime("%H:%M")))
    con.commit(); con.close()
    socketio.emit('new_message', {"id":mid,"sender":"ZONDI-AI","type":"text","text":txt,"chat_id":"emergency","timestamp":int(time.time())}, broadcast=True)

@app.route('/')
def idx():
    if 'user' in session: return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page(): return render_template('login.html')
@app.route('/register')
def reg_page(): return render_template('register.html')

# COMPATIBILITY FOR YOUR OLD URL /das
@app.route('/das')
def das_old():
    if 'user' not in session: return redirect('/login')
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    if request.args.get('json')=='1': return jsonify({"user":session['user'],"role":session['role'],"cell":session.get('cell','')})
    return render_template('client.html', user=session['user'], role=session['role'])

# AUTH
@app.route('/api/register', methods=['POST'])
def api_register():
    d=request.get_json() or request.form
    u=(d.get('username') or '').strip(); cr=(d.get('cell') or '').strip(); cn=normalize_cell(cr)
    pw=d.get('password') or ''; cf=d.get('confirm_password') or ''; role=(d.get('role') or 'client').lower()
    if len(u)<3: return jsonify({"ok":False,"error":"Username 3+"}),400
    if not validate_cell(cr): return jsonify({"ok":False,"error":"Invalid cell"}),400
    if len(pw)<6 or pw!=cf: return jsonify({"ok":False,"error":"Password mismatch/short"}),400
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users WHERE username=? OR cell_normalized=?", (u,cn))
    if cur.fetchone(): con.close(); return jsonify({"ok":False,"error":"Taken"}),400
    otp=gen_otp()
    cur.execute("INSERT OR REPLACE INTO otp_store (key,otp,expiry,username,cell,data,attempts,type) VALUES (?,?,?,?,?,?,?,?)",(cn,otp,int(time.time())+300,u,cn,json.dumps({"password_hash":generate_password_hash(pw),"role":role,"email":d.get('email',''),"cell_raw":cr}),0,"register"))
    con.commit(); con.close(); print(f"\n🔐 OTP {cn} {u} => {otp}\n"); return jsonify({"ok":True,"cell":cn,"dev_otp":otp})

@app.route('/api/verify-otp', methods=['POST'])
def api_verify():
    d=request.get_json() or request.form; cell=normalize_cell(d.get('cell') or ''); otp_in=(d.get('otp') or '').strip()
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=? AND type='register'",(cell,)); r=cur.fetchone()
    if not r or int(time.time())>r['expiry'] or r['otp']!=otp_in: con.close(); return jsonify({"ok":False,"error":"Invalid/expired OTP"}),400
    dj=json.loads(r['data'])
    cur.execute("INSERT INTO users (username,cell,cell_normalized,password_hash,role,email,verified,created,last_login,last_seen) VALUES (?,?,?,?,?,?,?,?,?,?)",(r['username'],dj['cell_raw'],cell,dj['password_hash'],dj['role'],dj['email'],1,datetime.now().isoformat(),int(time.time()),int(time.time())))
    cur.execute("DELETE FROM otp_store WHERE key=?",(cell,)); con.commit(); con.close(); backup_users(); return jsonify({"ok":True})

@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.get_json() or request.form; lid=(d.get('login') or d.get('username') or '').strip(); pw=d.get('password') or ''
    u=find_user(lid)
    if not u or not check_password_hash(u['password_hash'],pw): return jsonify({"ok":False,"error":"Invalid"}),401
    session['user']=u['username']; session['role']=u['role']; session['cell']=u['cell']; session.permanent=True
    con=db(); cur=con.cursor(); cur.execute("UPDATE users SET online=1, last_seen=? WHERE username=?",(int(time.time()),u['username'])); con.commit(); con.close()
    online_users[u['username']]={'role':u['role']};
    # AUTO-JOIN ALL GROUPS ON LOGIN - FIXES 0 MEMBERS BUG
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM groups"); groups=cur.fetchall()
    for g in groups:
        members=json.loads(g['members'] or '[]')
        if u['username'] not in members:
            members.append(u['username'])
            cur.execute("UPDATE groups SET members=? WHERE id=?",(json.dumps(members), g['id']))
    con.commit(); con.close()
    socketio.emit('user_status', {"username":u['username'],"status":"online"}, broadcast=True)
    return jsonify({"ok":True,"user":u['username'],"role":u['role']})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    d=request.get_json() or request.form; u=find_user((d.get('login') or '').strip())
    if not u: return jsonify({"ok":False,"error":"Not found"}),404
    otp=gen_otp(); key=u['cell_normalized']+"_reset"
    con=db(); cur=con.cursor(); cur.execute("INSERT OR REPLACE INTO otp_store (key,otp,expiry,username,cell,attempts,type) VALUES (?,?,?,?,?,?,?)",(key,otp,int(time.time())+300,u['username'],u['cell_normalized'],0,"reset")); con.commit(); con.close()
    session['reset_key']=key; print(f"\n🔐 RESET {u['cell_normalized']} => {otp}\n"); return jsonify({"ok":True,"dev_otp":otp,"cell":u['cell_normalized']})

@app.route('/api/verify-reset', methods=['POST'])
def vreset():
    d=request.get_json() or request.form; key=session.get('reset_key') or normalize_cell(d.get('cell') or '')+"_reset"
    otp_in=(d.get('otp') or '').strip(); np=d.get('new_password') or ''; cp=d.get('confirm_password') or ''
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=? AND type='reset'",(key,)); r=cur.fetchone()
    if not r or r['otp']!=otp_in: con.close(); return jsonify({"ok":False,"error":"Wrong OTP"}),400
    if np!=cp or len(np)<6: con.close(); return jsonify({"ok":False,"error":"Short/mismatch"}),400
    cur.execute("UPDATE users SET password_hash=? WHERE username=?",(generate_password_hash(np), r['username'])); cur.execute("DELETE FROM otp_store WHERE key=?",(key,)); con.commit(); con.close(); backup_users(); return jsonify({"ok":True})

@app.route('/api/resend-otp', methods=['POST'])
def resend():
    d=request.get_json() or request.form; cell=normalize_cell(d.get('cell') or ''); con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=?",(cell,)); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),400
    new=gen_otp(); cur.execute("UPDATE otp_store SET otp=?, expiry=? WHERE key=?",(new,int(time.time())+300,cell)); con.commit(); con.close(); return jsonify({"ok":True,"dev_otp":new})

@app.route('/api/update_location', methods=['POST'])
def updateloc():
    d=request.get_json() or request.form; user=session.get('user') or d.get('username')
    if not user: return jsonify({"ok":False}),401
    lat=float(d.get('lat') or 0); lng=float(d.get('lng') or 0)
    con=db(); cur=con.cursor(); cur.execute("INSERT OR REPLACE INTO locations (username,lat,lng,updated_at,role) VALUES (?,?,?,?,?)",(user,lat,lng,int(time.time()),session.get('role','client'))); con.commit(); con.close()
    socketio.emit('location_update', {"username":user,"lat":lat,"lng":lng,"role":session.get('role')}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/locations')
def locs(): con=db(); cur=con.cursor(); cur.execute("SELECT * FROM locations"); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

@app.route('/api/trigger_panic', methods=['POST'])
def panic():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json() or {}; lat=float(d.get('lat') or 0); lng=float(d.get('lng') or 0)
    con=db(); cur=con.cursor()
    if lat==0: cur.execute("SELECT lat,lng FROM locations WHERE username=?",(session['user'],)); r=cur.fetchone(); lat=r['lat'] if r else -25.9; lng=r['lng'] if r else 29.2
    pid=gen_id(); cur.execute("INSERT INTO panic_alerts (id,username,cell,lat,lng,status,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(pid,session['user'],session.get('cell',''),lat,lng,"pending",int(time.time()),datetime.now().strftime("%H:%M:%S")))
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(gen_id(),session['user'],session.get('role'),"panic",f"🚨 PANIC {session['user']}","emergency",int(time.time()),datetime.now().strftime("%H:%M:%S")))
    con.commit(); con.close(); pdata={"id":pid,"username":session['user'],"cell":session.get('cell',''),"lat":lat,"lng":lng,"status":"pending"}
    socketio.emit('panic_alert', pdata, broadcast=True); ai_dispatch(pdata); return jsonify({"ok":True,"panic":pdata})

@app.route('/api/emergencies')
def emergencies(): con=db(); cur=con.cursor(); cur.execute("SELECT * FROM panic_alerts ORDER BY timestamp DESC LIMIT 50"); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

# GROUP LOGIC - FIXES YOUR Gg Gu BUG
@app.route('/api/groups')
def get_groups():
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM groups ORDER BY timestamp DESC"); groups=[]
    for g in cur.fetchall():
        gd=dict(g); members=json.loads(gd['members'] or '[]')
        cur.execute("SELECT COUNT(*) as c FROM messages WHERE chat_id=? AND deleted_everyone=0",(gd['id'],)); msg_count=cur.fetchone()['c']
        cur.execute("SELECT text FROM messages WHERE chat_id=? ORDER BY timestamp DESC LIMIT 1",(gd['id'],)); last=cur.fetchone()
        gd['member_count']=len(members); gd['members']=members; gd['msg_count']=msg_count; gd['last_message']=last['text'] if last else "No messages yet"
        groups.append(gd)
    con.close(); return jsonify(groups)

@app.route('/api/create_group', methods=['POST'])
def create_group():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); name=(d.get('name') or '').strip(); desc=(d.get('description') or '').strip(); icon=d.get('icon') or "💬"
    if len(name)<2: return jsonify({"ok":False,"error":"Name 2+ chars"}),400
    gid="group_"+re.sub(r'[^a-z0-9]+','_',name.lower())+"_"+gen_id()
    con=db(); cur=con.cursor()
    try:
        cur.execute("INSERT INTO groups (id,name,description,icon,created_by,members,timestamp) VALUES (?,?,?,?,?,?,?)",(gid,name,desc,icon,session['user'],json.dumps([session['user']]),int(time.time())))
        con.commit(); con.close()
        socketio.emit('group_created', {"id":gid,"name":name,"description":desc,"icon":icon}, broadcast=True)
        return jsonify({"ok":True,"group":{"id":gid,"name":name}})
    except sqlite3.IntegrityError:
        con.close(); return jsonify({"ok":False,"error":"Group name exists"}),400

@app.route('/api/send_text', methods=['POST'])
def send_text():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); text=(d.get('text') or '').strip(); chat_id=d.get('chat_id') or 'group_central'; reply_to=d.get('reply_to')
    if not text: return jsonify({"ok":False}),400
    mid=gen_id(); con=db(); cur=con.cursor()
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,reply_to,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"text",text,chat_id,reply_to,int(time.time()),datetime.now().strftime("%H:%M")))
    con.commit(); con.close(); msg={"id":mid,"sender":session['user'],"sender_role":session['role'],"type":"text","text":text,"chat_id":chat_id,"reply_to":reply_to,"timestamp":int(time.time()),"time_str":datetime.now().strftime("%H:%M")}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True,"message":msg})

@app.route('/api/send_voicenote', methods=['POST'])
def send_vn():
    if 'user' not in session: return jsonify({"ok":False}),401
    chat_id=request.form.get('chat_id') or 'group_central'; f=request.files.get('audio')
    if not f: return jsonify({"ok":False}),400
    fname=f"VN_{session['user']}_{int(time.time())}.webm"; f.save(os.path.join(EVIDENCE_DIR,fname)); mid=gen_id()
    con=db(); cur=con.cursor(); cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"voicenote","🎤 Voice note",chat_id,f"/evidence/{fname}",int(time.time()),datetime.now().strftime("%H:%M"))); con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"voicenote","chat_id":chat_id,"file_url":f"/evidence/{fname}","timestamp":int(time.time())}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True})

@app.route('/api/upload_file', methods=['POST'])
def upfile():
    if 'user' not in session: return jsonify({"ok":False}),401
    f=request.files.get('file'); chat_id=request.form.get('chat_id') or 'group_central'
    if not f: return jsonify({"ok":False}),400
    fname=f"{int(time.time())}_{secure_filename(f.filename)}"; f.save(os.path.join(EVIDENCE_DIR,fname)); mid=gen_id()
    con=db(); cur=con.cursor(); cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"file",f.filename,chat_id,f"/evidence/{fname}",int(time.time()),datetime.now().strftime("%H:%M"))); con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"file","chat_id":chat_id,"file_url":f"/evidence/{fname}","text":f.filename}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True})

@app.route('/api/messages')
def get_msgs():
    chat_id=request.args.get('chat_id') or 'group_central'
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE chat_id=? AND deleted_everyone=0 ORDER BY timestamp ASC LIMIT 200",(chat_id,)); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

@app.route('/api/edit_message', methods=['POST'])
def edit_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); nt=(d.get('text') or '').strip()
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE id=? AND sender=?",(mid,session['user'])); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),403
    cur.execute("UPDATE messages SET text=?, edited=1 WHERE id=?",(nt,mid)); con.commit(); con.close(); socketio.emit('message_edited', {"id":mid,"text":nt}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/delete_message', methods=['POST'])
def del_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); mode=d.get('mode') or 'me'; con=db(); cur=con.cursor()
    if mode=='everyone': cur.execute("UPDATE messages SET deleted_everyone=1 WHERE id=?",(mid,))
    else: cur.execute("UPDATE messages SET deleted_for=? WHERE id=?",(json.dumps([session['user']]),mid))
    con.commit(); con.close(); socketio.emit('message_deleted', {"id":mid}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/react', methods=['POST'])
def react():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); emoji=d.get('emoji') or '❤️'; con=db(); cur=con.cursor(); cur.execute("SELECT reactions FROM messages WHERE id=?",(mid,)); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),404
    reacts=json.loads(r['reactions'] or '{}'); reacts.setdefault(emoji,[]);
    if session['user'] in reacts[emoji]: reacts[emoji].remove(session['user'])
    else: reacts[emoji].append(session['user'])
    cur.execute("UPDATE messages SET reactions=? WHERE id=?",(js WHERE chat_id=? ORDER BY timestamp DESC LIMIT 1",(gd['id'],)); last=cur.fetchone()
        gd['member_count']=len(members); gd['members']=members; gd['msg_count']=msg_count; gd['last_message']=last['text'] if last else "No messages yet"
        groups.append(gd)
    con.close(); return jsonify(groups)

@app.route('/api/create_group', methods=['POST'])
def create_group():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); name=(d.get('name') or '').strip(); desc=(d.get('description') or '').strip(); icon=d.get('icon') or "💬"
    if len(name)<2: return jsonify({"ok":False,"error":"Name 2+ chars"}),400
    gid="group_"+re.sub(r'[^a-z0-9]+','_',name.lower())+"_"+gen_id()
    con=db(); cur=con.cursor()
    try:
        cur.execute("INSERT INTO groups (id,name,description,icon,created_by,members,timestamp) VALUES (?,?,?,?,?,?,?)",(gid,name,desc,icon,session['user'],json.dumps([session['user']]),int(time.time())))
        con.commit(); con.close()
        socketio.emit('group_created', {"id":gid,"name":name,"description":desc,"icon":icon}, broadcast=True)
        return jsonify({"ok":True,"group":{"id":gid,"name":name}})
    except sqlite3.IntegrityError:
        con.close(); return jsonify({"ok":False,"error":"Group name exists"}),400

@app.route('/api/send_text', methods=['POST'])
def send_text():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); text=(d.get('text') or '').strip(); chat_id=d.get('chat_id') or 'group_central'; reply_to=d.get('reply_to')
    if not text: return jsonify({"ok":False}),400
    mid=gen_id(); con=db(); cur=con.cursor()
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,reply_to,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"text",text,chat_id,reply_to,int(time.time()),datetime.now().strftime("%H:%M")))
    con.commit(); con.close(); msg={"id":mid,"sender":session['user'],"sender_role":session['role'],"type":"text","text":text,"chat_id":chat_id,"reply_to":reply_to,"timestamp":int(time.time()),"time_str":datetime.now().strftime("%H:%M")}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True,"message":msg})

@app.route('/api/send_voicenote', methods=['POST'])
def send_vn():
    if 'user' not in session: return jsonify({"ok":False}),401
    chat_id=request.form.get('chat_id') or 'group_central'; f=request.files.get('audio')
    if not f: return jsonify({"ok":False}),400
    fname=f"VN_{session['user']}_{int(time.time())}.webm"; f.save(os.path.join(EVIDENCE_DIR,fname)); mid=gen_id()
    con=db(); cur=con.cursor(); cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"voicenote","🎤 Voice note",chat_id,f"/evidence/{fname}",int(time.time()),datetime.now().strftime("%H:%M"))); con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"voicenote","chat_id":chat_id,"file_url":f"/evidence/{fname}","timestamp":int(time.time())}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True})

@app.route('/api/upload_file', methods=['POST'])
def upfile():
    if 'user' not in session: return jsonify({"ok":False}),401
    f=request.files.get('file'); chat_id=request.form.get('chat_id') or 'group_central'
    if not f: return jsonify({"ok":False}),400
    fname=f"{int(time.time())}_{secure_filename(f.filename)}"; f.save(os.path.join(EVIDENCE_DIR,fname)); mid=gen_id()
    con=db(); cur=con.cursor(); cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"file",f.filename,chat_id,f"/evidence/{fname}",int(time.time()),datetime.now().strftime("%H:%M"))); con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"file","chat_id":chat_id,"file_url":f"/evidence/{fname}","text":f.filename}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True})

@app.route('/api/messages')
def get_msgs():
    chat_id=request.args.get('chat_id') or 'group_central'
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE chat_id=? AND deleted_everyone=0 ORDER BY timestamp ASC LIMIT 200",(chat_id,)); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

@app.route('/api/edit_message', methods=['POST'])
def edit_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); nt=(d.get('text') or '').strip()
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE id=? AND sender=?",(mid,session['user'])); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),403
    cur.execute("UPDATE messages SET text=?, edited=1 WHERE id=?",(nt,mid)); con.commit(); con.close(); socketio.emit('message_edited', {"id":mid,"text":nt}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/delete_message', methods=['POST'])
def del_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); mode=d.get('mode') or 'me'; con=db(); cur=con.cursor()
    if mode=='everyone': cur.execute("UPDATE messages SET deleted_everyone=1 WHERE id=?",(mid,))
    else: cur.execute("UPDATE messages SET deleted_for=? WHERE id=?",(json.dumps([session['user']]),mid))
    con.commit(); con.close(); socketio.emit('message_deleted', {"id":mid}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/react', methods=['POST'])
def react():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); emoji=d.get('emoji') or '❤️'; con=db(); cur=con.cursor(); cur.execute("SELECT reactions FROM messages WHERE id=?",(mid,)); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),404
    reacts=json.loads(r['reactions'] or '{}'); reacts.setdefault(emoji,[]);
    if session['user'] in reacts[emoji]: reacts[emoji].remove(session['user'])
    else: reacts[emoji].append(session['user'])
    cur.execute("UPDATE messages SET reactions=? WHERE id=?",(json.dumps(reacts),mid)); con.commit(); con.close()
    socketio.emit('message_reacted', {"id":mid,"reactions":reacts}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/typing', methods=['POST'])
def typing():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); socketio.emit('user_typing', {"chat_id":d.get('chat_id') or 'group_central',"user":session['user'],"typing":bool(d.get('typing'))}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/search')
def search():
    q=(request.args.get('q') or '').lower(); con=db(); cur=con.cursor()
    cur.execute("SELECT username, cell, role FROM users WHERE LOWER(username) LIKE? OR LOWER(cell) LIKE?",(f"%{q}%",f"%{q}%")); users=[dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM messages WHERE LOWER(text) LIKE? AND deleted_everyone=0 LIMIT 20",(f"%{q}%",)); msgs=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify({"users":users,"messages":msgs})

@app.route('/api/online')
def online(): con=db(); cur=con.cursor(); cur.execute("SELECT username, role, last_seen FROM users"); rows=[dict(r) for r in cur.fetchall()]; con.close(); [r.update({"is_online":r['username'] in online_users}) for r in rows]; return jsonify(rows)

@app.route('/evidence/<path:filename>')
def serve_ev(filename): return send_from_directory(EVIDENCE_DIR, filename)

@app.route('/dev', methods=['GET','POST'])
def dev():
    if request.method=='POST' and request.form.get('password')==DEV_PASSWORD: session['dev_auth']=True
    if not session.get('dev_auth'): return '<form method="POST"><h2>DEV Zondi@123</h2><input name="password" type="password"><button>Login</button></form>'
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users"); users=[dict(r) for r in cur.fetchall()]; cur.execute("SELECT * FROM otp_store"); otps=[dict(r) for r in cur.fetchall()]; cur.execute("SELECT * FROM groups"); groups=[dict(r) for r in cur.fetchall()]; con.close()
    return jsonify({"dev":"OK","users":users,"otp_store":otps,"groups":groups,"online":list(online_users.keys())})

@app.route('/logout')
def logout():
    if session.get('user') in online_users: del online_users[session['user']]
    session.clear(); return redirect('/login')

@socketio.on('connect')
def sc():
    if session.get('user'): online_users[session['user']]={"sid":request.sid}; socketio.emit('user_status', {"username":session['user'],"status":"online"}, broadcast=True)

@socketio.on('disconnect')
def sd():
    u=session.get('user');
    if u and u in online_users: del online_users[u]
    socketio.emit('user_status', {"username":u,"status":"offline"}, broadcast=True)

if __name__=='__main__':
    print("🚨 ZONDI V7.1 FIXED - Command/Patrol/Tactical + WhatsApp")
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT',5000)))'] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DEV_PASSWORD = "Zondi@123"
DB_PATH = "zondi.db"
BACKUP_JSON = "users.json"
EVIDENCE_DIR = "static/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs("backups", exist_ok=True)

def init_db():
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, cell TEXT UNIQUE, cell_normalized TEXT UNIQUE, password_hash TEXT, role TEXT, email TEXT, verified INTEGER, created TEXT, last_login TEXT, online INTEGER DEFAULT 0, last_seen INTEGER DEFAULT 0, blocked_users TEXT DEFAULT '[]')")
    c.execute("CREATE TABLE IF NOT EXISTS otp_store (key TEXT PRIMARY KEY, otp TEXT, expiry INTEGER, username TEXT, cell TEXT, data TEXT, attempts INTEGER DEFAULT 0, type TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS locations (username TEXT PRIMARY KEY, lat REAL, lng REAL, updated_at INTEGER, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, sender TEXT, sender_role TEXT, type TEXT, text TEXT, chat_id TEXT, reply_to TEXT, file_url TEXT, file_name TEXT, edited INTEGER DEFAULT 0, deleted_for TEXT DEFAULT '[]', deleted_everyone INTEGER DEFAULT 0, reactions TEXT DEFAULT '{}', read_by TEXT DEFAULT '[]', pinned INTEGER DEFAULT 0, timestamp INTEGER, time_str TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS panic_alerts (id TEXT PRIMARY KEY, username TEXT, cell TEXT, lat REAL, lng REAL, status TEXT, timestamp INTEGER, time_str TEXT, accepted_by TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS groups (id TEXT PRIMARY KEY, name TEXT UNIQUE, description TEXT, icon TEXT, created_by TEXT, members TEXT DEFAULT '[]', timestamp INTEGER)")
    con.commit()
    # AUTO-CREATE YOUR 3 GROUPS FROM SCREENSHOTS IF NOT EXIST
    c.execute("SELECT COUNT(*) FROM groups")
    if c.fetchone()[0]==0:
        default_groups = [
            ("group_command", "Command", "🏛️ HQ Command", "🏛️", "system"),
            ("group_patrol", "Patrol Unit", "🚓 Patrol Unit", "🚓", "system"),
            ("group_tactical", "Tactical", "⚡ Tactical Response", "⚡", "system"),
            ("group_central", "ZONDI CENTRAL", "Main group", "🟢", "system"),
            ("emergency", "EMERGENCY", "Panic alerts", "🚨", "system"),
        ]
        for gid, name, desc, icon, by in default_groups:
            c.execute("INSERT OR IGNORE INTO groups (id,name,description,icon,created_by,members,timestamp) VALUES (?,?,?,?,?,?,?)", (gid, name, desc, icon, by, json.dumps([]), int(time.time())))
        con.commit()
    con.close()
init_db()

def db():
    con=sqlite3.connect(DB_PATH)
    con.row_factory=sqlite3.Row
    return con

def backup_users():
    try:
        con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users"); d={r['username']:dict(r) for r in cur.fetchall()}
        open(BACKUP_JSON,'w').write(json.dumps(d,indent=2)); con.close()
    except: pass

def normalize_cell(c): c=str(c).strip().replace(" ",""); return "0"+c[3:] if c.startswith("+27") else c
def validate_cell(c): return re.match(r'^(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})$', str(c).strip().replace(" ","")) is not None
def gen_otp(): return str(random.randint(100000,999999))
def gen_id(): return uuid.uuid4().hex[:8]
online_users={}

def find_user(login_id):
    con=db(); cur=con.cursor()
    ln=normalize_cell(login_id) if login_id.replace("+","").replace(" ","").isdigit() else login_id.strip()
    cur.execute("SELECT * FROM users WHERE username=? OR cell=? OR cell_normalized=?", (ln, login_id.strip(), ln))
    r=cur.fetchone(); con.close(); return dict(r) if r else None

def ai_dispatch(pdata):
    con=db(); cur=con.cursor(); mid=gen_id()
    cur.execute("SELECT username FROM locations WHERE role='patrol' ORDER BY updated_at DESC LIMIT 1"); r=cur.fetchone()
    nearest=r['username'] if r else "nearest unit"
    txt=f"🤖 ZONDI-AI: PANIC {pdata['username']} ({pdata['cell']}) at {pdata['lat']:.4f},{pdata['lng']:.4f}. {nearest} dispatched."
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(mid,"ZONDI-AI","ai","text",txt,"emergency",int(time.time()),datetime.now().strftime("%H:%M")))
    con.commit(); con.close()
    socketio.emit('new_message', {"id":mid,"sender":"ZONDI-AI","type":"text","text":txt,"chat_id":"emergency","timestamp":int(time.time())}, broadcast=True)

@app.route('/')
def idx():
    if 'user' in session: return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page(): return render_template('login.html')
@app.route('/register')
def reg_page(): return render_template('register.html')

# COMPATIBILITY FOR YOUR OLD URL /das
@app.route('/das')
def das_old():
    if 'user' not in session: return redirect('/login')
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    if request.args.get('json')=='1': return jsonify({"user":session['user'],"role":session['role'],"cell":session.get('cell','')})
    return render_template('client.html', user=session['user'], role=session['role'])

# AUTH
@app.route('/api/register', methods=['POST'])
def api_register():
    d=request.get_json() or request.form
    u=(d.get('username') or '').strip(); cr=(d.get('cell') or '').strip(); cn=normalize_cell(cr)
    pw=d.get('password') or ''; cf=d.get('confirm_password') or ''; role=(d.get('role') or 'client').lower()
    if len(u)<3: return jsonify({"ok":False,"error":"Username 3+"}),400
    if not validate_cell(cr): return jsonify({"ok":False,"error":"Invalid cell"}),400
    if len(pw)<6 or pw!=cf: return jsonify({"ok":False,"error":"Password mismatch/short"}),400
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users WHERE username=? OR cell_normalized=?", (u,cn))
    if cur.fetchone(): con.close(); return jsonify({"ok":False,"error":"Taken"}),400
    otp=gen_otp()
    cur.execute("INSERT OR REPLACE INTO otp_store (key,otp,expiry,username,cell,data,attempts,type) VALUES (?,?,?,?,?,?,?,?)",(cn,otp,int(time.time())+300,u,cn,json.dumps({"password_hash":generate_password_hash(pw),"role":role,"email":d.get('email',''),"cell_raw":cr}),0,"register"))
    con.commit(); con.close(); print(f"\n🔐 OTP {cn} {u} => {otp}\n"); return jsonify({"ok":True,"cell":cn,"dev_otp":otp})

@app.route('/api/verify-otp', methods=['POST'])
def api_verify():
    d=request.get_json() or request.form; cell=normalize_cell(d.get('cell') or ''); otp_in=(d.get('otp') or '').strip()
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=? AND type='register'",(cell,)); r=cur.fetchone()
    if not r or int(time.time())>r['expiry'] or r['otp']!=otp_in: con.close(); return jsonify({"ok":False,"error":"Invalid/expired OTP"}),400
    dj=json.loads(r['data'])
    cur.execute("INSERT INTO users (username,cell,cell_normalized,password_hash,role,email,verified,created,last_login,last_seen) VALUES (?,?,?,?,?,?,?,?,?,?)",(r['username'],dj['cell_raw'],cell,dj['password_hash'],dj['role'],dj['email'],1,datetime.now().isoformat(),int(time.time()),int(time.time())))
    cur.execute("DELETE FROM otp_store WHERE key=?",(cell,)); con.commit(); con.close(); backup_users(); return jsonify({"ok":True})

@app.route('/api/login', methods=['POST'])
def api_login():
    d=request.get_json() or request.form; lid=(d.get('login') or d.get('username') or '').strip(); pw=d.get('password') or ''
    u=find_user(lid)
    if not u or not check_password_hash(u['password_hash'],pw): return jsonify({"ok":False,"error":"Invalid"}),401
    session['user']=u['username']; session['role']=u['role']; session['cell']=u['cell']; session.permanent=True
    con=db(); cur=con.cursor(); cur.execute("UPDATE users SET online=1, last_seen=? WHERE username=?",(int(time.time()),u['username'])); con.commit(); con.close()
    online_users[u['username']]={'role':u['role']};
    # AUTO-JOIN ALL GROUPS ON LOGIN - FIXES 0 MEMBERS BUG
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM groups"); groups=cur.fetchall()
    for g in groups:
        members=json.loads(g['members'] or '[]')
        if u['username'] not in members:
            members.append(u['username'])
            cur.execute("UPDATE groups SET members=? WHERE id=?",(json.dumps(members), g['id']))
    con.commit(); con.close()
    socketio.emit('user_status', {"username":u['username'],"status":"online"}, broadcast=True)
    return jsonify({"ok":True,"user":u['username'],"role":u['role']})

@app.route('/api/forgot', methods=['POST'])
def forgot():
    d=request.get_json() or request.form; u=find_user((d.get('login') or '').strip())
    if not u: return jsonify({"ok":False,"error":"Not found"}),404
    otp=gen_otp(); key=u['cell_normalized']+"_reset"
    con=db(); cur=con.cursor(); cur.execute("INSERT OR REPLACE INTO otp_store (key,otp,expiry,username,cell,attempts,type) VALUES (?,?,?,?,?,?,?)",(key,otp,int(time.time())+300,u['username'],u['cell_normalized'],0,"reset")); con.commit(); con.close()
    session['reset_key']=key; print(f"\n🔐 RESET {u['cell_normalized']} => {otp}\n"); return jsonify({"ok":True,"dev_otp":otp,"cell":u['cell_normalized']})

@app.route('/api/verify-reset', methods=['POST'])
def vreset():
    d=request.get_json() or request.form; key=session.get('reset_key') or normalize_cell(d.get('cell') or '')+"_reset"
    otp_in=(d.get('otp') or '').strip(); np=d.get('new_password') or ''; cp=d.get('confirm_password') or ''
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=? AND type='reset'",(key,)); r=cur.fetchone()
    if not r or r['otp']!=otp_in: con.close(); return jsonify({"ok":False,"error":"Wrong OTP"}),400
    if np!=cp or len(np)<6: con.close(); return jsonify({"ok":False,"error":"Short/mismatch"}),400
    cur.execute("UPDATE users SET password_hash=? WHERE username=?",(generate_password_hash(np), r['username'])); cur.execute("DELETE FROM otp_store WHERE key=?",(key,)); con.commit(); con.close(); backup_users(); return jsonify({"ok":True})

@app.route('/api/resend-otp', methods=['POST'])
def resend():
    d=request.get_json() or request.form; cell=normalize_cell(d.get('cell') or ''); con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=?",(cell,)); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),400
    new=gen_otp(); cur.execute("UPDATE otp_store SET otp=?, expiry=? WHERE key=?",(new,int(time.time())+300,cell)); con.commit(); con.close(); return jsonify({"ok":True,"dev_otp":new})

@app.route('/api/update_location', methods=['POST'])
def updateloc():
    d=request.get_json() or request.form; user=session.get('user') or d.get('username')
    if not user: return jsonify({"ok":False}),401
    lat=float(d.get('lat') or 0); lng=float(d.get('lng') or 0)
    con=db(); cur=con.cursor(); cur.execute("INSERT OR REPLACE INTO locations (username,lat,lng,updated_at,role) VALUES (?,?,?,?,?)",(user,lat,lng,int(time.time()),session.get('role','client'))); con.commit(); con.close()
    socketio.emit('location_update', {"username":user,"lat":lat,"lng":lng,"role":session.get('role')}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/locations')
def locs(): con=db(); cur=con.cursor(); cur.execute("SELECT * FROM locations"); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

@app.route('/api/trigger_panic', methods=['POST'])
def panic():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json() or {}; lat=float(d.get('lat') or 0); lng=float(d.get('lng') or 0)
    con=db(); cur=con.cursor()
    if lat==0: cur.execute("SELECT lat,lng FROM locations WHERE username=?",(session['user'],)); r=cur.fetchone(); lat=r['lat'] if r else -25.9; lng=r['lng'] if r else 29.2
    pid=gen_id(); cur.execute("INSERT INTO panic_alerts (id,username,cell,lat,lng,status,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(pid,session['user'],session.get('cell',''),lat,lng,"pending",int(time.time()),datetime.now().strftime("%H:%M:%S")))
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(gen_id(),session['user'],session.get('role'),"panic",f"🚨 PANIC {session['user']}","emergency",int(time.time()),datetime.now().strftime("%H:%M:%S")))
    con.commit(); con.close(); pdata={"id":pid,"username":session['user'],"cell":session.get('cell',''),"lat":lat,"lng":lng,"status":"pending"}
    socketio.emit('panic_alert', pdata, broadcast=True); ai_dispatch(pdata); return jsonify({"ok":True,"panic":pdata})

@app.route('/api/emergencies')
def emergencies(): con=db(); cur=con.cursor(); cur.execute("SELECT * FROM panic_alerts ORDER BY timestamp DESC LIMIT 50"); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

# GROUP LOGIC - FIXES YOUR Gg Gu BUG
@app.route('/api/groups')
def get_groups():
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM groups ORDER BY timestamp DESC"); groups=[]
    for g in cur.fetchall():
        gd=dict(g); members=json.loads(gd['members'] or '[]')
        cur.execute("SELECT COUNT(*) as c FROM messages WHERE chat_id=? AND deleted_everyone=0",(gd['id'],)); msg_count=cur.fetchone()['c']
        cur.execute("SELECT text FROM messages WHERE chat_id=? ORDER BY timestamp DESC LIMIT 1",(gd['id'],)); last=cur.fetchone()
        gd['member_count']=len(members); gd['members']=members; gd['msg_count']=msg_count; gd['last_message']=last['text'] if last else "No messages yet"
        groups.append(gd)
    con.close(); return jsonify(groups)

@app.route('/api/create_group', methods=['POST'])
def create_group():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); name=(d.get('name') or '').strip(); desc=(d.get('description') or '').strip(); icon=d.get('icon') or "💬"
    if len(name)<2: return jsonify({"ok":False,"error":"Name 2+ chars"}),400
    gid="group_"+re.sub(r'[^a-z0-9]+','_',name.lower())+"_"+gen_id()
    con=db(); cur=con.cursor()
    try:
        cur.execute("INSERT INTO groups (id,name,description,icon,created_by,members,timestamp) VALUES (?,?,?,?,?,?,?)",(gid,name,desc,icon,session['user'],json.dumps([session['user']]),int(time.time())))
        con.commit(); con.close()
        socketio.emit('group_created', {"id":gid,"name":name,"description":desc,"icon":icon}, broadcast=True)
        return jsonify({"ok":True,"group":{"id":gid,"name":name}})
    except sqlite3.IntegrityError:
        con.close(); return jsonify({"ok":False,"error":"Group name exists"}),400

@app.route('/api/send_text', methods=['POST'])
def send_text():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); text=(d.get('text') or '').strip(); chat_id=d.get('chat_id') or 'group_central'; reply_to=d.get('reply_to')
    if not text: return jsonify({"ok":False}),400
    mid=gen_id(); con=db(); cur=con.cursor()
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,reply_to,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"text",text,chat_id,reply_to,int(time.time()),datetime.now().strftime("%H:%M")))
    con.commit(); con.close(); msg={"id":mid,"sender":session['user'],"sender_role":session['role'],"type":"text","text":text,"chat_id":chat_id,"reply_to":reply_to,"timestamp":int(time.time()),"time_str":datetime.now().strftime("%H:%M")}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True,"message":msg})

@app.route('/api/send_voicenote', methods=['POST'])
def send_vn():
    if 'user' not in session: return jsonify({"ok":False}),401
    chat_id=request.form.get('chat_id') or 'group_central'; f=request.files.get('audio')
    if not f: return jsonify({"ok":False}),400
    fname=f"VN_{session['user']}_{int(time.time())}.webm"; f.save(os.path.join(EVIDENCE_DIR,fname)); mid=gen_id()
    con=db(); cur=con.cursor(); cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"voicenote","🎤 Voice note",chat_id,f"/evidence/{fname}",int(time.time()),datetime.now().strftime("%H:%M"))); con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"voicenote","chat_id":chat_id,"file_url":f"/evidence/{fname}","timestamp":int(time.time())}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True})

@app.route('/api/upload_file', methods=['POST'])
def upfile():
    if 'user' not in session: return jsonify({"ok":False}),401
    f=request.files.get('file'); chat_id=request.form.get('chat_id') or 'group_central'
    if not f: return jsonify({"ok":False}),400
    fname=f"{int(time.time())}_{secure_filename(f.filename)}"; f.save(os.path.join(EVIDENCE_DIR,fname)); mid=gen_id()
    con=db(); cur=con.cursor(); cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",(mid,session['user'],session['role'],"file",f.filename,chat_id,f"/evidence/{fname}",int(time.time()),datetime.now().strftime("%H:%M"))); con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"file","chat_id":chat_id,"file_url":f"/evidence/{fname}","text":f.filename}
    socketio.emit('new_message', msg, broadcast=True); return jsonify({"ok":True})

@app.route('/api/messages')
def get_msgs():
    chat_id=request.args.get('chat_id') or 'group_central'
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE chat_id=? AND deleted_everyone=0 ORDER BY timestamp ASC LIMIT 200",(chat_id,)); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

@app.route('/api/edit_message', methods=['POST'])
def edit_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); nt=(d.get('text') or '').strip()
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE id=? AND sender=?",(mid,session['user'])); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),403
    cur.execute("UPDATE messages SET text=?, edited=1 WHERE id=?",(nt,mid)); con.commit(); con.close(); socketio.emit('message_edited', {"id":mid,"text":nt}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/delete_message', methods=['POST'])
def del_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); mode=d.get('mode') or 'me'; con=db(); cur=con.cursor()
    if mode=='everyone': cur.execute("UPDATE messages SET deleted_everyone=1 WHERE id=?",(mid,))
    else: cur.execute("UPDATE messages SET deleted_for=? WHERE id=?",(json.dumps([session['user']]),mid))
    con.commit(); con.close(); socketio.emit('message_deleted', {"id":mid}, broadcast=True); return jsonify({"ok":True})

@app.route('/api/react', methods=['POST'])
def react():
    if 'user' not in session: return jsonify({"ok":False}),401
    d=request.get_json(); mid=d.get('id'); emoji=d.get('emoji') or '❤️'; con=db(); cur=con.cursor(); cur.execute("SELECT reactions FROM messages WHERE id=?",(mid,)); r=cur.fetchone()
    if not r: con.close(); return jsonify({"ok":False}),404
    reacts=json.loads(r['reactions'] or '{}'); reacts.setdefault(emoji,[]);
    if session['user'] in reacts[emoji]: reacts[emoji].remove(session['user'])
    else: reacts[emoji].append(session['user'])
    cur.execute("UPDATE messages SET reactions=? WHERE id=?",(js']+"_reset"
    con=db(); cur=con.cursor()
    cur.execute("INSERT OR REPLACE INTO otp_store (key,otp,expiry,username,cell,attempts,type) VALUES (?,?,?,?,?,?,?)", (key, otp, int(time.time())+300, user['username'], user['cell_normalized'], 0, "reset"))
    con.commit(); con.close()
    print(f"\n🔐 RESET OTP {user['cell_normalized']} => {otp}\n")
    session['reset_key']=key
    return jsonify({"ok":True,"dev_otp":otp})

@app.route('/api/verify-reset', methods=['POST'])
def api_verify_reset():
    data = request.get_json() or request.form
    key = session.get('reset_key') or (normalize_cell(data.get('cell') or '')+"_reset")
    otp_in = (data.get('otp') or '').strip()
    new_pw = data.get('new_password') or ''; conf = data.get('confirm_password') or ''
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=? AND type='reset'", (key,)); row=cur.fetchone()
    if not row: con.close(); return jsonify({"ok":False,"error":"No reset session"}),400
    if otp_in!=row['otp']: con.close(); return jsonify({"ok":False,"error":"Wrong OTP"}),400
    if new_pw!=conf or len(new_pw)<6: con.close(); return jsonify({"ok":False,"error":"Password mismatch/short"}),400
    cur.execute("UPDATE users SET password_hash=? WHERE username=?", (generate_password_hash(new_pw), row['username']))
    cur.execute("DELETE FROM otp_store WHERE key=?", (key,)); con.commit(); con.close(); backup_users()
    return jsonify({"ok":True})

@app.route('/api/resend-otp', methods=['POST'])
def api_resend():
    data=request.get_json() or request.form; cell=normalize_cell(data.get('cell') or '')
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM otp_store WHERE key=?", (cell,)); row=cur.fetchone()
    if not row: con.close(); return jsonify({"ok":False,"error":"No OTP"}),400
    new=gen_otp(); cur.execute("UPDATE otp_store SET otp=?, expiry=?, attempts=0 WHERE key=?", (new, int(time.time())+300, cell)); con.commit(); con.close()
    print(f"\n🔐 RESEND OTP {cell} => {new}\n")
    return jsonify({"ok":True,"dev_otp":new})

@app.route('/api/update_location', methods=['POST'])
def update_loc():
    data=request.get_json() or request.form
    user = session.get('user') or data.get('username')
    if not user: return jsonify({"ok":False}),401
    lat=float(data.get('lat') or 0); lng=float(data.get('lng') or 0)
    con=db(); cur=con.cursor()
    cur.execute("INSERT OR REPLACE INTO locations (username,lat,lng,updated_at,role) VALUES (?,?,?,?,?)", (user, lat, lng, int(time.time()), session.get('role','client')))
    con.commit(); con.close()
    socketio.emit('location_update', {"username":user,"lat":lat,"lng":lng}, broadcast=True)
    return jsonify({"ok":True})

@app.route('/api/locations')
def get_locs():
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM locations"); rows=[dict(r) for r in cur.fetchall()]; con.close()
    return jsonify(rows)

@app.route('/api/trigger_panic', methods=['POST'])
def panic():
    if 'user' not in session: return jsonify({"ok":False}),401
    data=request.get_json() or {}; lat=float(data.get('lat') or 0); lng=float(data.get('lng') or 0)
    con=db(); cur=con.cursor()
    if lat==0:
        cur.execute("SELECT lat,lng FROM locations WHERE username=?", (session['user'],)); r=cur.fetchone()
        if r: lat=r['lat']; lng=r['lng']
    pid=gen_id()
    cur.execute("INSERT INTO panic_alerts (id,username,cell,lat,lng,status,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",
                (pid, session['user'], session.get('cell',''), lat, lng, "pending", int(time.time()), datetime.now().strftime("%H:%M:%S")))
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",
                (gen_id(), session['user'], session.get('role'), "panic", f"🚨 PANIC {session['user']} {session.get('cell','')}", "emergency", int(time.time()), datetime.now().strftime("%H:%M:%S")))
    con.commit(); con.close()
    pdata={"id":pid,"username":session['user'],"cell":session.get('cell',''),"lat":lat,"lng":lng,"status":"pending"}
    socketio.emit('panic_alert', pdata, broadcast=True)
    ai_dispatch(pdata)
    return jsonify({"ok":True,"panic":pdata})

@app.route('/api/emergencies')
def emergencies():
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM panic_alerts ORDER BY timestamp DESC LIMIT 50"); rows=[dict(r) for r in cur.fetchall()]; con.close(); return jsonify(rows)

@app.route('/api/send_text', methods=['POST'])
def send_text():
    if 'user' not in session: return jsonify({"ok":False}),401
    data=request.get_json(); text=(data.get('text') or '').strip(); chat_id=data.get('chat_id') or 'group_central'; reply_to=data.get('reply_to')
    if not text: return jsonify({"ok":False}),400
    mid=gen_id()
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,reply_to,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",
                (mid, session['user'], session['role'], "text", text, chat_id, reply_to, int(time.time()), datetime.now().strftime("%H:%M")))
    con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"sender_role":session['role'],"type":"text","text":text,"chat_id":chat_id,"reply_to":reply_to,"timestamp":int(time.time()),"time_str":datetime.now().strftime("%H:%M")}
    socketio.emit('new_message', msg, broadcast=True)
    return jsonify({"ok":True,"message":msg})

@app.route('/api/send_voicenote', methods=['POST'])
def send_vn():
    if 'user' not in session: return jsonify({"ok":False}),401
    chat_id=request.form.get('chat_id') or 'group_central'
    if 'audio' not in request.files: return jsonify({"ok":False}),400
    f=request.files['audio']; fname=f"VN_{session['user']}_{int(time.time())}.webm"; path=os.path.join(EVIDENCE_DIR, fname); f.save(path)
    mid=gen_id()
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",
                (mid, session['user'], session['role'], "voicenote", "🎤 Voice note", chat_id, f"/evidence/{fname}", int(time.time()), datetime.now().strftime("%H:%M")))
    con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"voicenote","chat_id":chat_id,"file_url":f"/evidence/{fname}","timestamp":int(time.time()),"time_str":datetime.now().strftime("%H:%M")}
    socketio.emit('new_message', msg, broadcast=True)
    return jsonify({"ok":True,"message":msg})

@app.route('/api/upload_file', methods=['POST'])
def upload_file():
    if 'user' not in session: return jsonify({"ok":False}),401
    if 'file' not in request.files: return jsonify({"ok":False}),400
    f=request.files['file']; chat_id=request.form.get('chat_id') or 'group_central'
    fname=f"{int(time.time())}_{secure_filename(f.filename)}"; path=os.path.join(EVIDENCE_DIR, fname); f.save(path)
    mid=gen_id()
    con=db(); cur=con.cursor()
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,file_url,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?,?)",
                (mid, session['user'], session['role'], "file", f.filename, chat_id, f"/evidence/{fname}", int(time.time()), datetime.now().strftime("%H:%M")))
    con.commit(); con.close()
    msg={"id":mid,"sender":session['user'],"type":"file","chat_id":chat_id,"file_url":f"/evidence/{fname}","text":f.filename,"timestamp":int(time.time())}
    socketio.emit('new_message', msg, broadcast=True)
    return jsonify({"ok":True,"message":msg})

@app.route('/api/messages')
def get_messages():
    chat_id=request.args.get('chat_id') or 'group_central'
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE chat_id=? AND deleted_everyone=0 ORDER BY timestamp ASC LIMIT 200", (chat_id,))
    rows=[dict(r) for r in cur.fetchall()]; con.close()
    return jsonify(rows)

@app.route('/api/edit_message', methods=['POST'])
def edit_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    data=request.get_json(); mid=data.get('id'); new_text=(data.get('text') or '').strip()
    con=db(); cur=con.cursor(); cur.execute("SELECT * FROM messages WHERE id=? AND sender=?", (mid, session['user'])); row=cur.fetchone()
    if not row: con.close(); return jsonify({"ok":False}),403
    cur.execute("UPDATE messages SET text=?, edited=1 WHERE id=?", (new_text, mid)); con.commit(); con.close()
    socketio.emit('message_edited', {"id":mid,"text":new_text}, broadcast=True)
    return jsonify({"ok":True})

@app.route('/api/delete_message', methods=['POST'])
def del_msg():
    if 'user' not in session: return jsonify({"ok":False}),401
    data=request.get_json(); mid=data.get('id'); mode=data.get('mode') or 'me'
    con=db(); cur=con.cursor()
    if mode=='everyone': cur.execute("UPDATE messages SET deleted_everyone=1, text='🚫 Deleted' WHERE id=?", (mid,))
    else: cur.execute("UPDATE messages SET deleted_for=? WHERE id=?", (json.dumps([session['user']]), mid))
    con.commit(); con.close()
    socketio.emit('message_deleted', {"id":mid,"mode":mode}, broadcast=True)
    return jsonify({"ok":True})

@app.route('/api/react', methods=['POST'])
def react():
    if 'user' not in session: return jsonify({"ok":False}),401
    data=request.get_json(); mid=data.get('id'); emoji=data.get('emoji') or '❤️'
    con=db(); cur=con.cursor(); cur.execute("SELECT reactions FROM messages WHERE id=?", (mid,)); row=cur.fetchone()
    if not row: con.close(); return jsonify({"ok":False}),404
    reacts=json.loads(row['reactions'] or '{}')
    reacts.setdefault(emoji, [])
    if session['user'] in reacts[emoji]: reacts[emoji].remove(session['user'])
    else: reacts[emoji].append(session['user'])
    cur.execute("UPDATE messages SET reactions=? WHERE id=?", (json.dumps(reacts), mid)); con.commit(); con.close()
    socketio.emit('message_reacted', {"id":mid,"reactions":reacts}, broadcast=True)
    return jsonify({"ok":True})

@app.route('/api/read', methods=['POST'])
def read():
    if 'user' not in se    if cell.startswith("+27"): return "0"+cell[3:]
    return cell

def generate_otp(): return str(random.randint(100000,999999))

def find_user_by_login(login_id):
    users = load_users()
    login_id = normalize_cell(login_id) if login_id.replace("+","").replace(" ","").isdigit() else login_id.strip()
    if login_id in users: return login_id, users[login_id]
    for uname, udata in users.items():
        if normalize_cell(udata.get('cell','')) == login_id:
            return uname, udata
    return None,None

def login_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'user' not in session: return redirect('/login')
        return f(*args,**kwargs)
    return decorated

@app.route('/')
def home():
    if 'user' in session: return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='GET': return render_template('register.html')
    username = request.form.get('username','').strip()
    cell_raw = request.form.get('cell','').strip()
    cell = normalize_cell(cell_raw)
    password = request.form.get('password','')
    confirm = request.form.get('confirm_password','')
    role = request.form.get('role','client').lower()
    if len(username)<3: return render_template('register.html', error="Username 3+ chars", username=username, cell=cell_raw, role=role)
    if not validate_cell(cell_raw): return render_template('register.html', error="Invalid SA cell. Use 082... or +27...", username=username, cell=cell_raw, role=role)
    if len(password)<6: return render_template('register.html', error="Password 6+ chars", username=username, cell=cell_raw, role=role)
    if password!=confirm: return render_template('register.html', error="Passwords don't match", username=username, cell=cell_raw, role=role)
    if role not in ['client','patrol','dev']: role='client'
    users=load_users()
    if username in users: return render_template('register.html', error="Username taken", username=username, cell=cell_raw, role=role)
    for u,d in users.items():
        if normalize_cell(d.get('cell',''))==cell: return render_template('register.html', error="Cell already registered", username=username, cell=cell_raw, role=role)
    otp=generate_otp()
    otp_store[cell]={"otp":otp,"expiry":int(time.time())+300,"username":username,"cell":cell,"password_hash":generate_password_hash(password),"role":role,"email":request.form.get('email','').strip(),"attempts":0,"created":datetime.now().isoformat()}
    save_otp()
    print(f"\n\n🔐 [OTP FOR {cell} ({username})] => {otp} - Valid 5 mins\n\n")
    session['pending_cell']=cell
    return render_template('verify_otp.html', cell=cell, username=username, dev_otp=otp, message=f"OTP sent to {cell_raw} - DEV mode: {otp}")

@app.route('/verify-otp', methods=['GET','POST'])
def verify_otp():
    cell=request.args.get('cell') or session.get('pending_cell') or request.form.get('cell','')
    cell=normalize_cell(cell)
    if not cell: return redirect('/register')
    if request.method=='GET':
        data=otp_store.get(cell)
        if not data: return render_template('register.html', error="OTP expired - register again")
        return render_template('verify_otp.html', cell=cell, username=data['username'], dev_otp=data['otp'])
    entered=request.form.get('otp','').strip()
    cell=normalize_cell(request.form.get('cell',''))
    record=otp_store.get(cell)
    if not record: return render_template('verify_otp.html', error="OTP expired", cell=cell)
    if int(time.time())>record['expiry']:
        del otp_store[cell]; save_otp()
        return render_template('register.html', error="OTP expired - register again")
    record['attempts']+=1
    if record['attempts']>5:
        del otp_store[cell]; save_otp()
        return render_template('register.html', error="Too many tries")
    if entered!=record['otp']:
        save_otp()
        return render_template('verify_otp.html', error=f"Wrong OTP - {5-record['attempts']} left", cell=cell, username=record['username'], dev_otp=record['otp'])
    users=load_users()
    users[record['username']]={"username":record['username'],"cell":record['cell'],"password":record['password_hash'],"role":record['role'],"email":record.get('email',''),"verified":True,"created":record['created']}
    save_users(users)
    del otp_store[cell]; save_otp(); session.pop('pending_cell',None)
    return render_template('login.html', success=f"✅ {record['username']} verified! Login now")

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    cell=normalize_cell(request.form.get('cell',''))
    if cell not in otp_store: return jsonify({"ok":False,"error":"No pending OTP"})
    new_otp=generate_otp()
    otp_store[cell]['otp']=new_otp; otp_store[cell]['expiry']=int(time.time())+300; otp_store[cell]['attempts']=0; save_otp()
    print(f"\n\n🔐 [RESEND OTP FOR {cell}] => {new_otp}\n\n")
    return jsonify({"ok":True,"dev_otp":new_otp})

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='GET': return render_template('login.html')
    login_id=request.form.get('username','').strip(); pw=request.form.get('password','')
    uname,udata=find_user_by_login(login_id)
    if uname and check_password_hash(udata['password'],pw):
        session['user']=uname; session['role']=udata['role']; session['cell']=udata.get('cell',''); session.permanent=True
        return redirect('/dashboard')
    return render_template('login.html', error="❌ Invalid login")

@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method=='GET': return render_template('forgot.html')
    login_id=request.form.get('username','').strip()
    uname,udata=find_user_by_login(login_id)
    if not uname: return render_template('forgot.html', error="User not found")
    otp=generate_otp(); cell=normalize_cell(udata.get('cell',''))
    otp_store[cell+"_reset"]={"otp":otp,"expiry":int(time.time())+300,"username":uname,"cell":cell,"attempts":0}; save_otp()
    print(f"\n\n🔐 [RESET OTP FOR {cell} ({uname})] => {otp}\n\n")
    session['reset_cell']=cell+"_reset"; session['reset_user']=uname
    return render_template('verify_reset.html', cell=cell, username=uname, dev_otp=otp)

@app.route('/verify-reset', methods=['POST'])
def verify_reset():
    reset_key=session.get('reset_cell','');
    if not reset_key: return redirect('/forgot')
    rec=otp_store.get(reset_key)
    if not rec: return redirect('/forgot')
    otp_e=request.form.get('otp','').strip(); new_pw=request.form.get('new_password',''); conf=request.form.get('confirm_password','')
    if otp_e!=rec['otp']: return render_template('verify_reset.html', error="Wrong OTP", cell=rec['cell'], username=rec['username'], dev_otp=rec['otp'])
    if new_pw!=conf or len(new_pw)<6: return render_template('verify_reset.html', error="Password mismatch / too short", cell=rec['cell'], username=rec['username'], dev_otp=rec['otp'])
    users=load_users(); users[rec['username']]['password']=generate_password_hash(new_pw); save_users(users)
    del otp_store[reset_key]; save_otp(); session.pop('reset_cell',None)
    return render_template('login.html', success="✅ Password reset! Login now")

@app.route('/dashboard')
@login_required
def dashboard():
    return f"<h1>✅ STEP 1 WORKS! Welcome {session['user']} | {session['role']} | {session['cell']}</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__=='__main__':
    print("🚨 ZONDI V7 STEP 1 - AUTH + OTP")
    app.run(host='0.0.0.0', port=5000, debug=True)
