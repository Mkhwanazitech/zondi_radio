from flask import Flask, render_template, request, redirect, session, jsonify, g
from flask_socketio import SocketIO
from datetime import timedelta
import os
import sqlite3
import random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ZONDI_V7_1_FIXED_2026")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
DEV_PASSWORD = os.environ.get("DEV_PASSWORD", "zondi@123")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DB_PATH = 'zondi.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'offline',
            is_verified INTEGER DEFAULT 0,
            otp TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_by TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            group_id INTEGER,
            username TEXT,
            PRIMARY KEY (group_id, username)
        )
    """)
    # Try add new columns if old DB exists
    try:
        cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except: pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    except: pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN otp TEXT")
    except: pass

    conn.commit()
    conn.close()
    print("DB ready")

init_db()

@app.route('/')
def home():
    if 'user' in session:
        role = session.get('role', 'client')
        if role == 'dev':
            return redirect('/dev')
        if role == 'patroller':
            return redirect('/patrol')
        return redirect('/dashboard')
    if session.get('dev_auth'):
        return redirect('/dev')
    return redirect('/login')
            
@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect('/')
    return render_template('login.html')

# --- NEW AUTH LOGIC (BLACK & GOLD + MOCK OTP) ---

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    phone = data.get('phone','').strip()
    if not username or not phone:
        return jsonify(ok=False, error="Username & phone required"), 400
    
    otp = str(random.randint(100000, 999999))
    session['pending_otp'] = otp
    session['pending_user'] = data
    
    print(f"[MOCK OTP] {username} {phone} -> {otp}")
    return jsonify(ok=True, mock_otp=otp)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    phone = data.get('phone','').strip()
    role = data.get('role','client').strip().lower()
    otp_input = data.get('otp','').strip()

    if not all([username, password, phone, otp_input]):
        return jsonify(ok=False, error="All fields + OTP required"), 400
    if role not in ['client','patroller','dev']:
        return jsonify(ok=False, error="Invalid portal"), 400
    if otp_input != session.get('pending_otp'):
        return jsonify(ok=False, error="Invalid OTP"), 400

    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password, phone, role, is_verified, status, otp) VALUES (?,?,?,?,?,?,?)",
                   (username, password, phone, role, 1, 'online', otp_input))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify(ok=False, error="Username or phone already exists"), 400
    conn.close()

    session.permanent = True
    session['user'] = username
    session['role'] = role
    session.pop('pending_otp', None)

    target = '/dashboard' if role == 'client' else f"/{role}"
    return jsonify(ok=True, role=role, redirect=target)

# --- YOUR LOGIN UPGRADED ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'ok': False, 'msg': 'Enter username and password'}), 400
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password, role, is_verified FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'ok': False, 'msg': 'user not found'}), 404
    
    db_user, db_pass, db_role, is_verified = row['username'], row['password'], row['role'], row['is_verified']
    
    if db_pass != password:
        conn.close()
        return jsonify({'ok': False, 'msg': 'wrong password'}), 401

    # Update status
    cur.execute("UPDATE users SET status='online' WHERE username=?", (username,))
    conn.commit()
    conn.close()
    
    session['user'] = db_user
    session['role'] = db_role
    session.permanent = True
    if db_role == 'dev':
        session['dev_auth'] = True

    target = '/dashboard' if db_role == 'client' else f"/{db_role}"
    return jsonify({'ok': True, 'role': db_role, 'redirect': target})

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return f"<h1 style='background:black;color:gold;padding:20px'>CLIENT PORTAL - Welcome {session['user']}</h1><a href='/logout'>Logout</a><p>Created by mkhwanazitech.com</p>"

@app.route('/patrol')
def patrol_portal():
    if 'user' not in session:
        return redirect('/login')
    return f"<h1 style='background:black;color:gold;padding:20px'>PATROLLER PORTAL - {session['user']} on duty</h1><a href='/logout'>Logout</a>"

@app.route('/dev')
def dev_portal():
    if session.get('role') != 'dev' and not session.get('dev_auth'):
        return redirect('/login')
    return f"<h1>DEV PORTAL - {session.get('user','DEV')}</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    if 'user' in session:
        try:
            conn = get_db()
            conn.execute("UPDATE users SET status='offline' WHERE username=?", (session['user'],))
            conn.commit()
            conn.close()
        except: pass
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
