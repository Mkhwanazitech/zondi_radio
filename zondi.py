from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO
from datetime import timedelta
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ZONDI_V7_1_FIXED_2026")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
DEV_PASSWORD = os.environ.get("DEV_PASSWORD", "zondi@123")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def get_db():
    conn = sqlite3.connect('zondi.db')
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
            role TEXT NOT NULL,
            status TEXT DEFAULT 'offline'
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
    conn.commit()
    conn.close()
    print("DB ready")

init_db()

@app.route('/')
def home():
    if 'user' in session:
        role = session.get('role' , 'client')
        if role = 'dev':
            return redirect('/dev')
        if role = 'patroller':
            retun redirect('/patoller')
        if role = 'dashboard':
            return redirect('/dashboard')
    if session.get('dev_auth'):
        return redirect('/dev')
    return redirect('/login')
            
@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('api/login' , mothods =['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', ).strip()
    password = data.get('password', ).strip()
    if not username or not password:
        return jsonify({'ok': False, 'msg': 'Enter username and password'}) , 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username , password , role FROM user WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'ok': False, 'msg': 'user not found'}) , 404
    db_user, db_pass, db__role = row
    if db_pass !=password:
        return jsonify({'ok': False, 'msg': 'wrong password'}) , 401
    session['user'] = db_user
    session['role'] = db_role
    session.permanent = true
    return jsonify({'ok': True, 'role': db_role})
