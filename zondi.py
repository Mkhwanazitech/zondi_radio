from flask import Flask, render_template, request, redirect, session, jsonify, g
from flask_socketio import SocketIO, emit
from datetime import timedelta, datetime
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
            otp TEXT,
            address TEXT DEFAULT 'Not set'
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patrol_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            address TEXT,
            note TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            type TEXT DEFAULT 'panic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try: cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except: pass
    try: cur.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    except: pass
    try: cur.execute("ALTER TABLE users ADD COLUMN otp TEXT")
    except: pass
    try: cur.execute("ALTER TABLE users ADD COLUMN address TEXT DEFAULT 'Not set'")
    except: pass

    conn.commit()
    conn.close()
    print("DB ready")

init_db()

@app.route('/')
def home():
    if 'user' in session:
        role = session.get('role', 'client')
        if role == 'dev': return redirect('/dev')
        if role == 'patroller': return redirect('/patrol')
        return redirect('/dashboard')
    if session.get('dev_auth'): return redirect('/dev')
    return redirect('/login')
            
@app.route('/login')
def login_page():
    if 'user' in session: return redirect('/')
    return render_template('login.html')

# --- AUTH LOGIC (KEPT) ---
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
    print(f"[MOCK OTP]
