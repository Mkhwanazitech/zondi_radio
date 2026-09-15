from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO
from datetime import timedelta
import os, sqlite3, random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ZONDI_V7_2_CLEAN")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DB_PATH = 'zondi.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, phone TEXT, role TEXT NOT NULL, status TEXT DEFAULT 'offline', is_verified INTEGER DEFAULT 0, otp TEXT, address TEXT DEFAULT 'Not set')")
    cur.execute("CREATE TABLE IF NOT EXISTS patrol_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, address TEXT, note TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cur.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, phone TEXT, address TEXT, type TEXT DEFAULT 'panic', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user' in session:
        r = session.get('role', 'client')
        if r == 'dev':
            return redirect('/dev')
        if r == 'patroller':
            return redirect('/patrol')
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    otp = str(random.randint(100000, 999999))
    session['pending_otp'] = otp
    return jsonify(ok=True, mock_otp=otp)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    phone = data.get('phone','').strip()
    role = data.get('role','client').strip().lower()
    otp_input = data.get('otp','').strip()
    if otp_input != session.get('pending_otp'):
        return jsonify(ok=False, error="Invalid OTP"), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username,password,phone,role,is_verified,status) VALUES (?,?,?,?,?,?)", (username,password,phone,role,1,'online'))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify(ok=False, error="Username exists"), 400
    conn.close()
    session.permanent = True
    session['user'] = username
    session['role'] = role
    target = '/dashboard' if role == 'client' else '/' + role
    return jsonify(ok=True, redirect=target)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row or row['password'] != password:
        conn.close()
        return jsonify(ok=False, msg='wrong login'), 401
    conn.execute("UPDATE users SET status='online' WHERE username=?", (username,))
    conn.commit()
    conn.close()
    session['user'] = row['username']
    session['role'] = row['role']
    session.permanent = True
    target = '/dashboard' if row['role'] == 'client' else '/' + row['role']
    return jsonify(ok=True, redirect=target)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    reqs = conn.execute("SELECT * FROM patrol_requests WHERE username=? ORDER BY id DESC", (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, requests=reqs)

@app.route('/api/request-patrol', methods=['POST'])
def request_patrol():
    data = request.get_json() or {}
    conn = get_db()
    conn.execute("INSERT INTO patrol_requests (username,address,note) VALUES (?,?,?)", (session['user'], data.get('address',''), data.get('note','')))
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
    if 'user' not in session:
        return redirect('/login')
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
    return "<h1>DEV COMING NEXT</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect('/')
    return render_template('login.html')

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    otp = str(random.randint(100000, 999999))
    session['pending_otp'] = otp
    return jsonify(ok=True, mock_otp=otp)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    phone = data.get('phone','').strip()
    role = data.get('role','client').strip().lower()
    otp_input = data.get('otp','').strip()
    if otp_input != session.get('pending_otp'):
        return jsonify(ok=False, error="Invalid OTP"), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username,password,phone,role,is_verified,status) VALUES (?,?,?,?,?,?)", (username,password,phone,role,1,'online'))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify(ok=False, error="Username exists"), 400
    conn.close()
    session.permanent = True
    session['user'] = username
    session['role'] = role
    target = '/dashboard' if role == 'client' else '/' + role
    return jsonify(ok=True, redirect=target)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row or row['password'] != password:
        conn.close()
        return jsonify(ok=False, msg='wrong login'), 401
    conn.execute("UPDATE users SET status='online' WHERE username=?", (username,))
    conn.commit()
    conn.close()
    session['user'] = row['username']
    session['role'] = row['role']
    session.permanent = True
    target = '/dashboard' if row['role'] == 'client' else '/' + row['role']
    return jsonify(ok=True, redirect=target)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    reqs = conn.execute("SELECT * FROM patrol_requests WHERE username=? ORDER BY id DESC", (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, requests=reqs)

@app.route('/api/request-patrol', methods=['POST'])
def request_patrol():
    data = request.get_json() or {}
    conn = get_db()
    conn.execute("INSERT INTO patrol_requests (username,address,note) VALUES (?,?,?)", (session['user'], data.get('address',''), data.get('note','')))
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
    if 'user' not in session:
        return redirect('/login')
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
    return "<h1>DEV COMING NEXT</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)        role = session.get('role', 'client')
        if role == 'dev':
            return redirect('/dev')
        if role == 'patroller':
            return redirect('/patrol')
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect('/')
    return render_template('login.html')

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
    print("MOCK OTP for " + username + " " + phone + " -> " + otp)
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
    if otp_input != session.get('pending_otp'):
        return jsonify(ok=False, error="Invalid OTP"), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password, phone, role, is_verified, status, otp) VALUES (?,?,?,?,?,?,?)", (username, password, phone, role, 1, 'online', otp_input))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify(ok=False, error="Username exists"), 400
    conn.close()
    session.permanent = True
    session['user'] = username
    session['role'] = role
    session.pop('pending_otp', None)
    target = '/dashboard' if role == 'client' else "/"+role
    return jsonify(ok=True, redirect=target)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row:
        conn.close()
        return jsonify(ok=False, msg='user not found'), 404
    if row['password'] != password:
        conn.close()
        return jsonify(ok=False, msg='wrong password'), 401
    conn.execute("UPDATE users SET status='online' WHERE username=?", (username,))
    conn.commit()
    conn.close()
    session['user'] = row['username']
    session['role'] = row['role']
    session.permanent = True
    target = '/dashboard' if row['role'] == 'client' else "/"+row['role']
    return jsonify(ok=True, redirect=target)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    reqs = conn.execute("SELECT * FROM patrol_requests WHERE username=? ORDER BY id DESC", (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, requests=reqs)

@app.route('/api/request-patrol', methods=['POST'])
def request_patrol():
    if 'user' not in session:
        return jsonify(ok=False), 401
    data = request.get_json() or {}
    address = data.get('address','')
    note = data.get('note','')
    conn = get_db()
    conn.execute("INSERT INTO patrol_requests (username, address, note) VALUES (?,?,?)", (session['user'], address, note))
    if address:
        conn.execute("UPDATE users SET address=? WHERE username=?", (address, session['user']))
    conn.commit()
    conn.close()
    socketio.emit('new_patrol_request', {'username': session['user']})
    return jsonify(ok=True)

@app.route('/api/panic', methods=['POST'])
def panic():
    if 'user' not in session:
        return jsonify(ok=False), 401
    conn = get_db()
    u = conn.execute("SELECT phone, address FROM users WHERE username=?", (session['user'],)).fetchone()
    conn.execute("INSERT INTO alerts (username, phone, address) VALUES (?,?,?)", (session['user'], u['phone'] if u else '', u['address'] if u else ''))
    conn.commit()
    conn.close()
    socketio.emit('panic_alert', {'username': session['user']}, broadcast=True)
    return jsonify(ok=True)

# ======== UPDATED PATROLLER PORTAL =========
@app.route('/patrol')
def patrol_portal():
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'patroller':
        return redirect('/')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    requests_all = conn.execute("SELECT * FROM patrol_requests ORDER BY id DESC").fetchall()
    alerts_all = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return render_template('patrol.html', user=user, requests=requests_all, alerts=alerts_all)

@app.route('/api/accept-request/<int:req_id>', methods=['POST'])
def accept_request(req_id):
    if 'user' not in session:
        return jsonify(ok=False), 401
    conn = get_db()
    conn.execute("UPDATE patrol_requests SET status='accepted' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    socketio.emit('request_accepted', {'id': req_id}, broadcast=True)
    return jsonify(ok=True)

@app.route('/api/complete-request/<int:req_id>', methods=['POST'])
def complete_request(req_id):
    if 'user' not in session:
        return jsonify(ok=False), 401
    conn = get_db()
    conn.execute("UPDATE patrol_requests SET status='completed' WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    return jsonify(ok=True)

@app.route('/dev')
def dev_portal():
    return "<h1>DEV PORTAL COMING NEXT</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@socketio.on('connect')
def on_connect():
    print("User connected")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)        role = session.get('role', 'client')
        if role == 'dev':
            return redirect('/dev')
        if role == 'patroller':
            return redirect('/patrol')
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect('/')
    return render_template('login.html')

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
    print("MOCK OTP for " + username + " " + phone + " -> " + otp)
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
    if otp_input != session.get('pending_otp'):
        return jsonify(ok=False, error="Invalid OTP"), 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password, phone, role, is_verified, status, otp) VALUES (?,?,?,?,?,?,?)", (username, password, phone, role, 1, 'online', otp_input))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify(ok=False, error="Username exists"), 400
    conn.close()
    session.permanent = True
    session['user'] = username
    session['role'] = role
    session.pop('pending_otp', None)
    target = '/dashboard' if role == 'client' else "/"+role
    return jsonify(ok=True, redirect=target)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row:
        conn.close()
        return jsonify(ok=False, msg='user not found'), 404
    if row['password'] != password:
        conn.close()
        return jsonify(ok=False, msg='wrong password'), 401
    conn.execute("UPDATE users SET status='online' WHERE username=?", (username,))
    conn.commit()
    conn.close()
    session['user'] = row['username']
    session['role'] = row['role']
    session.permanent = True
    target = '/dashboard' if row['role'] == 'client' else "/"+row['role']
    return jsonify(ok=True, redirect=target)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    reqs = conn.execute("SELECT * FROM patrol_requests WHERE username=? ORDER BY id DESC", (session['user'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, requests=reqs)

@app.route('/api/request-patrol', methods=['POST'])
def request_patrol():
    if 'user' not in session:
        return jsonify(ok=False), 401
    data = request.get_json() or {}
    address = data.get('address','')
    note = data.get('note','')
    conn = get_db()
    conn.execute("INSERT INTO patrol_requests (username, address, note) VALUES (?,?,?)", (session['user'], address, note))
    if address:
        conn.execute("UPDATE users SET address=? WHERE username=?", (address, session['user']))
    conn.commit()
    conn.close()
    socketio.emit('new_patrol_request', {'username': session['user']})
    return jsonify(ok=True)

@app.route('/api/panic', methods=['POST'])
def panic():
    if 'user' not in session:
        return jsonify(ok=False), 401
    conn = get_db()
    u = conn.execute("SELECT phone, address FROM users WHERE username=?", (session['user'],)).fetchone()
    conn.execute("INSERT INTO alerts (username, phone, address) VALUES (?,?,?)", (session['user'], u['phone'] if u else '', u['address'] if u else ''))
    conn.commit()
    conn.close()
    socketio.emit('panic_alert', {'username': session['user']}, broadcast=True)
    return jsonify(ok=True)

@app.route('/patrol')
def patrol_portal():
    return "<h1 style='background:black;color:gold;padding:20px'>PATROLLER PORTAL COMING NEXT - Created by mkhwanazitech.com</h1><a href='/logout'>Logout</a>"

@app.route('/dev')
def dev_portal():
    return "<h1>DEV PORTAL COMING NEXT</h1><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@socketio.on('connect')
def on_connect():
    print("User connected")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
