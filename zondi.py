# ZONDI V7 FINAL - WHATSAPP EDITION - WHOLE SCRIPT
# Features: Auth OTP, Location 30sec, Panic + AI, WhatsApp Group+Private, Edit/Delete/Reply, Reactions, Read, Typing, Online, Search, Pin, Block, Evidence, Dev Zondi@123, Never Lose Data

from flask import Flask, request, jsonify, session, send_from_directory, render_template, redirect
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, random, re, time, uuid, sqlite3

app = Flask(__name__)
app.secret_key = "ZONDI_V7_FINAL_NEVER_LOSE_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DEV_PASSWORD = "Zondi@123"
DB_PATH = "zondi.db"
BACKUP_JSON = "users.json"
EVIDENCE_DIR = "static/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs("backups", exist_ok=True)
os.makedirs("templates", exist_ok=True)

def init_db():
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, cell TEXT UNIQUE, cell_normalized TEXT UNIQUE,
        password_hash TEXT, role TEXT, email TEXT, verified INTEGER,
        created TEXT, last_login TEXT, online INTEGER DEFAULT 0,
        last_seen INTEGER DEFAULT 0, blocked_users TEXT DEFAULT '[]', muted_users TEXT DEFAULT '[]'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS otp_store (
        key TEXT PRIMARY KEY, otp TEXT, expiry INTEGER, username TEXT,
        cell TEXT, data TEXT, attempts INTEGER DEFAULT 0, type TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS locations (
        username TEXT PRIMARY KEY, lat REAL, lng REAL, updated_at INTEGER, role TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY, sender TEXT, sender_role TEXT, type TEXT, text TEXT,
        chat_id TEXT, reply_to TEXT, file_url TEXT, file_name TEXT,
        edited INTEGER DEFAULT 0, deleted_for TEXT DEFAULT '[]',
        deleted_everyone INTEGER DEFAULT 0, reactions TEXT DEFAULT '{}',
        read_by TEXT DEFAULT '[]', delivered_to TEXT DEFAULT '[]',
        pinned INTEGER DEFAULT 0, timestamp INTEGER, time_str TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS panic_alerts (
        id TEXT PRIMARY KEY, username TEXT, cell TEXT, lat REAL, lng REAL,
        status TEXT, timestamp INTEGER, time_str TEXT, accepted_by TEXT
    )""")
    con.commit(); con.close()

init_db()

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def backup_users():
    try:
        con = db(); cur = con.cursor()
        cur.execute("SELECT * FROM users")
        users_dict = {r['username']: dict(r) for r in cur.fetchall()}
        with open(BACKUP_JSON,'w') as f: json.dump(users_dict, f, indent=2)
        daily = f"backups/users_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(daily,'w') as f: json.dump(users_dict, f, indent=2)
        con.close()
    except Exception as e:
        print("Backup error", e)

def normalize_cell(cell):
    cell = str(cell).strip().replace(" ","")
    if cell.startswith("+27"): return "0"+cell[3:]
    return cell

def validate_cell(cell):
    return re.match(r'^(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})$', str(cell).strip().replace(" ","")) is not None

def gen_otp(): return str(random.randint(100000,999999))
def gen_id(): return uuid.uuid4().hex[:12]

online_users = {}

def find_user(login_id):
    con = db(); cur = con.cursor()
    login_norm = normalize_cell(login_id) if login_id.replace("+","").replace(" ","").isdigit() else login_id.strip()
    cur.execute("SELECT * FROM users WHERE username=? OR cell=? OR cell_normalized=?", (login_norm, login_id.strip(), login_norm))
    row = cur.fetchone(); con.close()
    return dict(row) if row else None

def ai_dispatch(panic_data):
    con = db(); cur = con.cursor()
    cur.execute("SELECT username FROM locations WHERE role='patrol' ORDER BY updated_at DESC LIMIT 1")
    r = cur.fetchone()
    nearest = r['username'] if r else "nearest unit"
    mid = gen_id()
    text = f"🤖 ZONDI-AI: PANIC {panic_data['username']} ({panic_data['cell']}) at {panic_data['lat']:.4f},{panic_data['lng']:.4f}. {nearest} dispatched. ETA 4 mins."
    cur.execute("INSERT INTO messages (id,sender,sender_role,type,text,chat_id,timestamp,time_str) VALUES (?,?,?,?,?,?,?,?)",
                (mid, "ZONDI-AI", "ai", "text", text, "group_central", int(time.time()), datetime.now().strftime("%H:%M")))
    con.commit(); con.close()
    socketio.emit('new_message', {"id":mid,"sender":"ZONDI-AI","sender_role":"ai","type":"text","text":text,"chat_id":"group_central","timestamp":int(time.time()),"time_str":datetime.now().strftime("%H:%M")}, broadcast=True)

# PAGES
@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    # API for JS to get user info
    if request.args.get('json')=='1':
        return jsonify({"user":session['user'],"role":session['role'],"cell":session.get('cell','')})
    return render_template('client.html', user=session['user'], role=session['role'])

# API AUTH
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or request.form
    username = (data.get('username') or '').strip()
    cell_raw = (data.get('cell') or '').strip()
    cell_norm = normalize_cell(cell_raw)
    pw = data.get('password') or ''; conf = data.get('confirm_password') or ''
    role = (data.get('role') or 'client').lower()
    if len(username)<3: return jsonify({"ok":False,"error":"Username 3+ chars"}),400
    if not validate_cell(cell_raw): return jsonify({"ok":False,"error":"Invalid SA cell"}),400
    if len(pw)<6: return jsonify({"ok":False,"error":"Password 6+ chars"}),400
    if pw!=conf: return jsonify({"ok":False,"error":"Passwords mismatch"}),400
    if role not in ['client','patrol','dev']: role='client'
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=? OR cell_normalized=?", (username, cell_norm))
    if cur.fetchone(): con.close(); return jsonify({"ok":False,"error":"Username or cell taken"}),400
    otp = gen_otp()
    cur.execute("INSERT OR REPLACE INTO otp_store (key,otp,expiry,username,cell,data,attempts,type) VALUES (?,?,?,?,?,?,?,?)",
                (cell_norm, otp, int(time.time())+300, username, cell_norm, json.dumps({"password_hash":generate_password_hash(pw),"role":role,"email":data.get('email',''),"cell_raw":cell_raw}), 0, "register"))
    con.commit(); con.close()
    print(f"\n🔐 OTP REGISTER {cell_norm} ({username}) => {otp}\n")
    return jsonify({"ok":True,"cell":cell_norm,"dev_otp":otp})

@app.route('/api/verify-otp', methods=['POST'])
def api_verify_otp():
    data = request.get_json() or request.form
    cell = normalize_cell(data.get('cell') or ''); otp_in = (data.get('otp') or '').strip()
    con = db(); cur = con.cursor()
    cur.execute("SELECT * FROM otp_store WHERE key=? AND type='register'", (cell,))
    row = cur.fetchone()
    if not row: con.close(); return jsonify({"ok":False,"error":"OTP expired"}),400
    if int(time.time())>row['expiry']: cur.execute("DELETE FROM otp_store WHERE key=?", (cell,)); con.commit(); con.close(); return jsonify({"ok":False,"error":"OTP expired"}),400
    if row['attempts']>=5: cur.execute("DELETE FROM otp_store WHERE key=?", (cell,)); con.commit(); con.close(); return jsonify({"ok":False,"error":"Too many tries"}),400
    if otp_in!=row['otp']: cur.execute("UPDATE otp_store SET attempts=attempts+1 WHERE key=?", (cell,)); con.commit(); con.close(); return jsonify({"ok":False,"error":"Wrong OTP"}),400
    data_json = json.loads(row['data'])
    cur.execute("INSERT INTO users (username,cell,cell_normalized,password_hash,role,email,verified,created,last_login,last_seen) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (row['username'], data_json['cell_raw'], cell, data_json['password_hash'], data_json['role'], data_json['email'], 1, datetime.now().isoformat(), int(time.time()), int(time.time())))
    cur.execute("DELETE FROM otp_store WHERE key=?", (cell,)); con.commit(); con.close()
    backup_users()
    return jsonify({"ok":True,"message":f"{row['username']} verified"})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    login_id = (data.get('login') or data.get('username') or data.get('cell') or '').strip()
    pw = data.get('password') or ''
    user = find_user(login_id)
    if not user or not check_password_hash(user['password_hash'], pw): return jsonify({"ok":False,"error":"Invalid login"}),401
    session['user']=user['username']; session['role']=user['role']; session['cell']=user['cell']; session.permanent=True
    con=db(); cur=con.cursor(); cur.execute("UPDATE users SET last_login=?, last_seen=?, online=1 WHERE username=?", (int(time.time()), int(time.time()), user['username'])); con.commit(); con.close()
    online_users[user['username']] = {"role":user['role'],"last_seen":int(time.time())}
    socketio.emit('user_status', {"username":user['username'],"status":"online"}, broadcast=True)
    return jsonify({"ok":True,"user":user['username'],"role":user['role']})

@app.route('/api/forgot', methods=['POST'])
def api_forgot():
    data = request.get_json() or request.form
    login_id = (data.get('login') or data.get('username') or data.get('cell') or '').strip()
    user = find_user(login_id)
    if not user: return jsonify({"ok":False,"error":"User not found"}),404
    otp = gen_otp(); key = user['cell_normalized']+"_reset"
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
