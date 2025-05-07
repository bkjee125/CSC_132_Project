from flask import (
    Flask, render_template, redirect, url_for,
    request, jsonify, session, flash, get_flashed_messages
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json

# ---------------------------------------
# Application Setup & Configuration
# ---------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SECRET_KEY'] = 'dev_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///heater.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
db = SQLAlchemy(app)

latest_temp = None  # you can hook this up to your sensor-reading thread

# ---------------------------------------
# Database Models
# ---------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Heater(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _target_temp = db.Column(db.Text, nullable=True)
    current_temperature = db.Column(db.Float, default=0)
    status = db.Column(db.String(10), default="off")
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("UTC")))
    updated_at = db.Column(db.DateTime,
                           default=datetime.now(ZoneInfo("UTC")),
                           onupdate=datetime.now(ZoneInfo("UTC")))

    @property
    def target_temperature(self):
        return float(json.loads(self._target_temp)) if self._target_temp else None

    @target_temperature.setter
    def target_temperature(self, temp):
        self._target_temp = json.dumps(temp)

    def to_dict(self):
        return {
            "id": self.id,
            "target_temperature": self.target_temperature,
            "current_temperature": self.current_temperature,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": (self.updated_at.isoformat()
                           if self.updated_at else None)
        }

with app.app_context():
    db.create_all()

# ---------------------------------------
# Authentication Routes
# ---------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email    = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('signup.html')

        if User.query.filter((User.username == username) |
                             (User.email == email)).first():
            flash('Username or email already taken.', 'error')
            return render_template('signup.html')

        pw_hash = generate_password_hash(password)
        new_user = User(username=username, email=email,
                        password_hash=pw_hash)
        db.session.add(new_user)
        db.session.commit()

        session.permanent = True
        session['user_id'] = new_user.id
        return redirect(url_for('index'))

    # clear any stray flashes on GET
    _ = get_flashed_messages(with_categories=True)
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return render_template('login.html')

    # clear any stray flashes on GET
    _ = get_flashed_messages(with_categories=True)
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------------------------
# Main Routes
# ---------------------------------------
@app.route('/')
def root():
    if 'user_id' not in session:
        return redirect(url_for('signup'))
    return redirect(url_for('index'))

@app.route('/control')
def index():
    return render_template('index.html')

# ---------------------------------------
# Existing API Routes
# ---------------------------------------
@app.route('/api/temperature')
def api_temp():
    temp = latest_temp if latest_temp is not None else None
    return jsonify({"temperature": round(temp, 1)
                    if temp is not None else None})

@app.route('/api/power', methods=['POST'])
def api_power():
    data = request.get_json() or {}
    state = data.get('state')
    # placeholder: wire this up to serial/Bluetooth if you wish
    return ('', 204)

@app.route('/init', methods=['POST'])
def init_heater():
    data = request.get_json() or {}
    heater = Heater()
    heater.target_temperature = data.get('target_temperature', 0)
    heater.status = data.get('status', 'off')
    db.session.add(heater)
    db.session.commit()
    return jsonify({"heater": heater.to_dict()})

@app.route('/list')
def list_heaters():
    heaters = [h.to_dict() for h in Heater.query.all()]
    return jsonify(heaters)

@app.route('/set', methods=['POST'])
def set_heater():
    data = request.get_json() or {}
    heater = Heater.query.get(data.get('id'))
    if 'target_temperature' in data:
        heater.target_temperature = data['target_temperature']
    if 'status' in data:
        heater.status = data['status']
    db.session.commit()
    return jsonify({"heater": heater.to_dict()})

@app.route('/status')
def heater_status():
    heater = Heater.query.get(request.args.get('id'))
    return jsonify({"heater": heater.to_dict()})

@app.route('/update_current', methods=['POST'])
def update_current_temperature():
    data = request.get_json() or {}
    heater = Heater.query.get(data.get('id'))
    heater.current_temperature = data.get('current_temperature')
    db.session.commit()
    return jsonify({"heater": heater.to_dict()})

# ---------------------------------------
# New: ESP32 Wi-Fi Control Endpoints
# ---------------------------------------
ESP32_IP = "192.168.1.42"  # change to your ESP32's actual IP

@app.route('/api/heater/<action>', methods=['POST'])
def api_heater(action):
    if action in ('on', 'off'):
        url = f"http://{ESP32_IP}/{action}"
        resp = requests.post(url)
    elif action == 'set':
        val = request.get_json().get('value')
        url = f"http://{ESP32_IP}/set"
        resp = requests.post(url, params={"temp": val})
    else:
        return jsonify({"error": "Unknown action"}), 400

    try:
        return jsonify(resp.json()), resp.status_code
    except ValueError:
        return jsonify({"status": action}), resp.status_code

# ---------------------------------------
# Run Application
# ---------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000, use_reloader=False)
