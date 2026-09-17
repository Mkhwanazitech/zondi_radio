import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO
from datetime import timedelta
import os, sqlite3, random, time

app = Flask(__name__, template_folder='templates')
app.secret_key = "ZONDI_FINAL"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
DB_PATH = 'zondi.db'

live_clients = {} # NEVER cleared unless server restart - so map never loses location

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, phone TEXT, role TEXT, status TEXT DEFAULT 'offline', lat REAL, lng REAL, last_seen REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, lat REAL, lng REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()
init_db()

def normalize_role(r):
    r=(r or 'client').lower()
    if 'patrol' in r: return 'patroller','/patrol'
    if 'dev' in r: return 'dev','/dev'
    return 'client','/dashboard'

@app.route('/')
def home(): return redirect('/login')

@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    otp=str(random.randint(100000,999999))
    session['pending_otp']=otp
    return jsonify(ok=True, mock_otp=otp)

@app.route('/api/register', methods=['POST'])
def reg():
    d=request.get_json() or {}
    if d.get('otp','')!=session.get('pending_otp'): return jsonify(ok=False,error="Invalid OTP"),400
    role,target=normalize_role(d.get('role'))
    conn=get_db()
    try:
        conn.execute("INSERT INTO users (username,password,phone,role) VALUES (?,?,?,?)",(d.get('username'),d.get('password'),d.get('phone'),role))
        conn.commit()
    except: conn.close(); return jsonify(ok=False,error="User exists"),400
    conn.close()
    session['user']=d.get('username'); session['role']=role; session.permanent=True
    return jsonify(ok=True,redirect=target)

@app.route('/api/login', methods=['POST'])
def log():
    d=request.get_json() or {}
    conn=get_db(); row=conn.execute("SELECT * FROM users WHERE username=? AND password=?",(d.get('username'),d.get('password'))).fetchone()
    conn.close()
    if not row: return jsonify(ok=False,msg='wrong'),401
    session['user']=row['username']; session['role']=row['role']; session.permanent=True
    _,target=normalize_role(row['role'])
    return jsonify(ok=True,redirect=target)

@app.route('/dashboard')
def dash():
    if 'user' not in session: return redirect('/login')
    return render_template('dashboard.html', user={'username':session['user']})

@app.route('/patrol')
def patrol():
    if 'user' not in session: return redirect('/login')
    conn=get_db(); users=conn.execute("SELECT username,lat,lng,last_seen FROM users WHERE role='client'").fetchall()
    alerts=conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return render_template('patrol.html', user={'username':session['user']}, clients=users, alerts=alerts, live=live_clients)

@socketio.on('update_location')
def upd(data):
    user=session.get('user') or data.get('username')
    lat,lng=data.get('lat'),data.get('lng')
    if not user or not lat: return
    live_clients[user]={'lat':lat,'lng':lng,'time':time.time()}
    conn=get_db()
    conn.execute("UPDATE users SET lat=?, lng=?, last_seen=?, status='online' WHERE username=?",(lat,lng,time.time(),user))
    conn.commit(); conn.close()
    socketio.emit('client_moved',{'username':user,'lat':lat,'lng':lng},broadcast=True)

@socketio.on('panic_alert')
def panic(data):
    user=session.get('user') or data.get('username')
    lat,lng=data.get('lat'),data.get('lng')
    conn=get_db()
    conn.execute("INSERT INTO alerts (username,lat,lng) VALUES (?,?,?)",(user,lat,lng))
    conn.commit(); conn.close()
    socketio.emit('panic_triggered',{'username':user,'lat':lat,'lng':lng},broadcast=True)

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__=='__main__': socketio.run(app,host='0.0.0.0',port=5000)
