from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, json, random, re, time
from functools import wraps

app = Flask(__name__)
app.secret_key = "ZONDI_V7_STEP1_AUTH_OTP_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

USERS_FILE = "users.json"
OTP_FILE = "otp_store.json"

otp_store = {}
if os.path.exists(OTP_FILE):
    try:
        with open(OTP_FILE,'r') as f: otp_store = json.load(f)
    except: otp_store = {}

def save_otp():
    with open(OTP_FILE,'w') as f: json.dump(otp_store, f, indent=2)

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE,'r') as f: return json.load(f) or {}
    except: return {}

def save_users(u):
    with open(USERS_FILE,'w') as f: json.dump(u, f, indent=2)

def validate_cell(cell):
    return re.match(r'^(0[6-8][0-9]{8}|\+27[6-8][0-9]{8})$', cell.strip().replace(" ","")) is not None

def normalize_cell(cell):
    cell = cell.strip().replace(" ","")
    if cell.startswith("+27"): return "0"+cell[3:]
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
