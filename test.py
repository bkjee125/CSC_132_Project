from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///heaterbuddie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Helper to check login
def is_logged_in():
    return 'user_id' in session

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if User.query.filter_by(username=u).first():
            flash('User exists')
        else:
            pw_hash = generate_password_hash(p)
            user = User(username=u, password=pw_hash)
            db.session.add(user)
            db.session.commit()
            flash('Account created')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Bad login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/temp')
def api_temp():
    if not is_logged_in():
        return jsonify({'error': 'not logged in'}), 401
    try:
        r = requests.get('http://esp32.local/temperature')
        return jsonify(r.json())
    except:
        return jsonify({'error': 'fail'}), 500

@app.route('/api/weather')
def api_weather():
    if not is_logged_in():
        return jsonify({'error': 'not logged in'}), 401
    key = 'your-openweather-api-key'
    city = 'YourCity'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=imperial&appid={key}'
    data = requests.get(url).json()
    return jsonify({'temp': data['main']['temp'], 'desc': data['weather'][0]['description']})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
