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
    c.execute("CREATE TABLE IF NOT EXISTS users (...)")  # Omitted for brevity
    con.commit()
    con.close()

init_db()

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

@app.route('/')
def idx():
    if 'user' in session: return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json() or request.form
    lid = (d.get('login') or d.get('username') or '').strip()
    pw = d.get('password') or ''
    u = find_user(lid)
    if not u or not check_password_hash(u['password_hash'], pw):
        return jsonify({"ok":False,"error":"Invalid"}),401
    session['user'] = u['username']
    session['role'] = u['role']
    session['cell'] = u['cell']
    return jsonify({"ok":True,"user":u['username'],"role":u['role']})

@app.route('/api/create_group', methods=['POST'])
def create_group():
    if 'user' not in session: return jsonify({"ok":False}),401
    d = request.get_json(); name = (d.get('name') or '').strip();
    gid = "group_" + re.sub(r'[^a-z0-9]+','_',name.lower()) + "_" + gen_id()
    con = db(); cur = con.cursor()
    try:
        cur.execute("INSERT INTO groups (...)")
        con.commit();
    except sqlite3.IntegrityError:
        return jsonify({"ok":False,"error":"Group name exists"}),400
    return jsonify({"ok":True,"group":{"id":gid,"name":name}})

# ... (other existing endpoints)

if __name__ == '__main__':
    socketio.run(app, debug=True)@app.route('/login')
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
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
