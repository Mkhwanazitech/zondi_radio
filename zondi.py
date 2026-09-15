from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO
from datetime import timedelta
import os, sqlite3, random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("SECRET_KEY", "ZONDI_FINAL")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
DB_PATH = 'zondi.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, phone TEXT, role TEXT, status TEXT DEFAULT 'offline', is_verified INTEGER DEFAULT 0, otp TEXT, address TEXT DEFAULT 'Not set')")
    c.execute("CREATE TABLE IF NOT EXISTS patrol_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, address TEXT, note TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, phone TEXT, address TEXT, type TEXT DEFAULT 'panic', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
init_db()

@app.route('/')
def home():
    if 'user' in session:
        r = session.get('role','client')
        if r == 'dev': return redirect('/dev')
        if r == 'patroller': return redirect('/patrol')
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page():
    if 'user' in session: return redirect('/')
    return render_template('login.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    otp = str(random.randint(100000, 999999))
    session['pending_otp'] = otp
    return jsonify(ok=True, mock_otp=otp)

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.get_json() or {}
    if d.get('otp','') != session.get('pending_otp'): return jsonify(ok=False, error="Invalid OTP"), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username,password,phone,role,is_verified,status) VALUES (?,?,?,?,?,?)", (d.get('username',''), d.get('password',''), d.get('phone',''), d.get('role','client'), 1, 'online'))
        conn.commit()
    except:
        conn.close()
        return jsonify(ok=False, error="Username exists"), 400
    conn.close()
    session['user'] = d.get('username','')
    session['role'] = d.get('role','client')
    session.permanent = True
    target = '/dashboard' if session['role']=='client' else '/'+session['role']
    return jsonify(ok=True, redirect=target)

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json() or {}
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (d.get('username',''),)).fetchone()
    if not row or row['password'] != d.get('password',''): 
        conn.close()
        return jsonify(ok=False, msg='wrong login'), 401
    conn.execute("UPDATE users SET status='online' WHERE username=?", (d.get('username',''),))
    conn.commit()
    conn.close()
    session['user'] = row['username']
    session['role'] = row['role']
    session.permanent = True
    target = '/dashboard' if row['role']=='client' else '/'+row['role']
    return jsonify(ok=True, redirect=target)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    reqs = conn.execute("SELECT * FROM patrol_requests WHERE username=? ORDER BY id DESC", (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, requests=reqs)

@app.route('/api/request-patrol', methods=['POST'])
def request_patrol():
    d = request.get_json() or {}
    conn = get_db()
    conn.execute("INSERT INTO patrol_requests (username,address,note) VALUES (?,?,?)", (session['user'], d.get('address',''), d.get('note','')))
    conn.commit()
    conn.close()
    socketio.emit('new_patrol_request', {'username': session['user']})
    return jsonify(ok=True)

@app.route('/api/panic', methods=['POST'])
def panic():
    conn = get_db()
    u = conn.execute("SELECT phone,address FROM users WHERE username=?", (session['user'],)).fetchone()
    conn.execute("INSERT INTO alerts (username,phone,address) VALUES (?,?,?)", (session['user'], u['phone'] if u else '', u['address'] if u else ''))
    conn.commit()
    conn.close()
    socketio.emit('panic_alert', {'username': session['user']}, broadcast=True)
    return jsonify(ok=True)

@app.route('/patrol')
def patrol_portal():
    if 'user' not in session: return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    reqs = conn.execute("SELECT * FROM patrol_requests ORDER BY id DESC").fetchall()
    alerts = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return render_template('patrol.html', user=user, requests=reqs, alerts=alerts)

@app.route('/api/accept-request/<int:req_id>', methods=['POST'])
def accept_request(req_id):
    conn = get_db()
    conn.execute("UPDATE patrol_requests SET status='accepted' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify(ok=True)

@app.route('/api/complete-request/<int:req_id>', methods=['POST'])
def complete_request(req_id):
    conn = get_db()
    conn.execute("UPDATE patrol_requests SET status='completed' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify(ok=True)

@app.route('/dev')
def dev_portal():
    return "<h1 style='font-family:sans-serif;padding:40px'>DEV portal coming next - <a href='/logout'>Logout</a></h1>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
