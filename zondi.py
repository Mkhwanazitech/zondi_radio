from flask import Flask , render_template , request , jsonify , redirect
from flask_socketio import socketIO
from datetime import timedeLta
import os

app = Flask(_name_)
app.secret_key = os.environ.get("SECRET_KEY" , "ZONDI_V7_1_FIXED_2026")
app.config("PERMANENT_SESSION_LIFETIME") = timedeLta(days=30)
DEV_PASSWORD = os.environ.get("DEV_PASSWORD" , "zondi@123")
socketio = socketIO(app, cors_allowed_origins= , async_mode='threading')

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
    return redirect('/login)
            
