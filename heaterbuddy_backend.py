from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import requests
from requests.exceptions import RequestException

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.update(
    SECRET_KEY='dev_secret_key',
    SQLALCHEMY_DATABASE_URI='sqlite:///heater.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PERMANENT_SESSION_LIFETIME=timedelta(days=30)
)
db = SQLAlchemy(app)

# ←── Your ESP32’s IP ────────────────────────────────────────────────
ESP32_IP   = '172.20.10.12'
ESP32_BASE = f'http://{ESP32_IP}'

# ←── Hard-coded OpenWeatherMap key ─────────────────────────────────────

# ── Models ───────────────────────────────────────────────────────────────
class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Heater(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    target_temp  = db.Column(db.Float, default=60.0)
    current_temp = db.Column(db.Float, default=0.0)
    is_on        = db.Column(db.Boolean, default=False)
    def to_dict(self):
        return {
            'current': self.current_temp,
            'target':  self.target_temp,
            'is_on':   self.is_on
        }

with app.app_context():
    db.create_all()
    if not Heater.query.first():
        db.session.add(Heater())
        db.session.commit()

# ── Authentication ────────────────────────────────────────────────────────
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username'].strip()
        e = request.form['email'].strip()
        p = request.form['password']
        if not (u and e and p):
            flash('All fields required', 'error')
        elif User.query.filter((User.username==u)|(User.email==e)).first():
            flash('Username or email taken', 'error')
        else:
            user = User(
                username=u,
                email=e,
                password_hash=generate_password_hash(p)
            )
            db.session.add(user)
            db.session.commit()
            session.permanent = True
            session['user_id'] = user.id
            return redirect(url_for('control'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password']
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password_hash, p):
            session.permanent = True
            session['user_id'] = user.id
            return redirect(url_for('control'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Main Pages ────────────────────────────────────────────────────────────
@app.route('/')
def root():
    return redirect(url_for('control') if session.get('user_id') else url_for('login'))

@app.route('/control')
def control():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('index.html')

# ── Auth Helper ───────────────────────────────────────────────────────────
def require_auth():
    if not session.get('user_id'):
        return jsonify({'error':'Unauthorized'}), 401

# ── Heater Control API ─────────────────────────────────────────────────────
@app.route('/api/heater/on', methods=['POST'])
def heater_on():
    err = require_auth()
    if err: return err
    h = Heater.query.first()
    try:
        r = requests.get(f'{ESP32_BASE}/on', timeout=2)
        r.raise_for_status()
        h.is_on = True; db.session.commit()
        return jsonify(r.json())
    except RequestException as e:
        app.logger.error(f"ESP32 /on failed: {e}")
        return jsonify({'error':'ESP32 unreachable'}), 502

@app.route('/api/heater/off', methods=['POST'])
def heater_off():
    err = require_auth()
    if err: return err
    h = Heater.query.first()
    try:
        r = requests.get(f'{ESP32_BASE}/off', timeout=2)
        r.raise_for_status()
        h.is_on = False; db.session.commit()
        return jsonify(r.json())
    except RequestException as e:
        app.logger.error(f"ESP32 /off failed: {e}")
        return jsonify({'error':'ESP32 unreachable'}), 502

@app.route('/api/heater/set', methods=['POST'])
def heater_set():
    err = require_auth()
    if err: return err
    data = request.get_json(silent=True) or {}
    if 'target' not in data:
        return jsonify({'error':'Missing "target"'}), 400
    tgt = float(data['target'])
    h = Heater.query.first()
    try:
        r = requests.get(f'{ESP32_BASE}/set?target={tgt}', timeout=2)
        r.raise_for_status()
        h.target_temp = tgt; db.session.commit()
        return jsonify(r.json())
    except RequestException as e:
        app.logger.error(f"ESP32 /set failed: {e}")
        return jsonify({'error':'ESP32 unreachable'}), 502

@app.route('/api/heater/temp', methods=['GET'])
def heater_temp():
    err = require_auth()
    if err: return err
    return jsonify(Heater.query.first().to_dict())

@app.route('/api/heater/update', methods=['POST'])
def heater_update():
    data = request.get_json(force=True) or {}
    app.logger.info(f"Update payload: {data}")
    if 'current' not in data:
        return jsonify({'error':'Missing "current"'}), 400
    h = Heater.query.first()
    h.current_temp = float(data['current'])
    db.session.commit()
    return jsonify({'updated': h.current_temp})

# ── Weather Proxy ────────────────────────────────────────────────────────────
@app.route('/api/weather')
def api_weather():
    """Fetch current weather from wttr.in (no API key needed)."""
    city = "Ruston"  # change as desired
    url = f"https://wttr.in/{city}?format=j1"
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        data = r.json()
        # wttr.in puts the current condition under 'current_condition'
        cond = data['current_condition'][0]
        temp = float(cond['temp_F'])
        desc = cond['weatherDesc'][0]['value']
        return jsonify({"temp": temp, "desc": desc})
    except Exception as e:
        app.logger.error("wttr.in fetch failed", exc_info=True)
        return jsonify({"temp": None, "desc": None}), 502

# ── Run Server ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
