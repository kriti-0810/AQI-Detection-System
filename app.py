from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
from datetime import datetime
import secrets
from helpers import get_aqi_class, get_aqi_description, get_health_implications

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aqi_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Register helper functions with Jinja2
app.jinja_env.globals.update(
    get_aqi_class=get_aqi_class,
    get_aqi_description=get_aqi_description,
    get_health_implications=get_health_implications
)

# API Keys - Replace with your actual keys
OPENWEATHER_API_KEY = "fca4dde723c55eb26debb24f4459b19e"
WAQI_API_KEY = "0fb93c8d6a82a20e386c4e41cf9ec59a277796e3"

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    cities = db.relationship('SavedCity', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SavedCity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    alert_threshold = db.Column(db.Integer, default=100)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    saved_cities = SavedCity.query.filter_by(user_id=current_user.id).all()
    city_data = []
    
    for city in saved_cities:
        aqi_data = get_aqi_data(city.city_name)
        if aqi_data:
            city_data.append({
                'id': city.id,
                'name': city.city_name,
                'aqi': aqi_data.get('aqi', 'N/A'),
                'alert_threshold': city.alert_threshold
            })
    
    return render_template('dashboard.html', cities=city_data)

@app.route('/add_city', methods=['POST'])
@login_required
def add_city():
    city_name = request.form.get('city_name')
    alert_threshold = request.form.get('alert_threshold', 100)

    if SavedCity.query.filter_by(user_id=current_user.id, city_name=city_name).first():
        flash('City already in your list.')
        return redirect(url_for('dashboard'))

    aqi_data = get_aqi_data(city_name)
    if not aqi_data:
        flash('City not found or no AQI data available.')
        return redirect(url_for('dashboard'))

    new_city = SavedCity(
        city_name=city_name,
        user_id=current_user.id,
        alert_threshold=alert_threshold
    )

    db.session.add(new_city)
    db.session.commit()

    flash(f'{city_name} added to your monitoring list.')
    return redirect(url_for('dashboard'))

@app.route('/remove_city/<int:city_id>', methods=['POST'])
@login_required
def remove_city(city_id):
    city = SavedCity.query.filter_by(id=city_id, user_id=current_user.id).first()

    if not city:
        flash('City not found.')
        return redirect(url_for('dashboard'))

    db.session.delete(city)
    db.session.commit()

    flash(f'{city.city_name} removed from your monitoring list.')
    return redirect(url_for('dashboard'))

@app.route('/update_threshold/<int:city_id>', methods=['POST'])
@login_required
def update_threshold(city_id):
    city = SavedCity.query.filter_by(id=city_id, user_id=current_user.id).first()

    if not city:
        flash('City not found.')
        return redirect(url_for('dashboard'))

    city.alert_threshold = request.form.get('alert_threshold', 100)
    db.session.commit()

    flash(f'Alert threshold updated for {city.city_name}.')
    return redirect(url_for('dashboard'))

@app.route('/city/<city_name>')
def city_detail(city_name):
    aqi_data = get_aqi_data(city_name)

    if not aqi_data:
        flash('City not found or no AQI data available.')
        return redirect(url_for('index'))

    return render_template('city_detail.html', city=city_name, data=aqi_data)

@app.route('/search_city', methods=['GET', 'POST'])
def search_city():
    if request.method == 'POST':
        city_name = request.form.get('city_name')
        if not city_name:
            flash("Please enter a city name.")
            return redirect(url_for('search_city'))

        aqi_data = get_aqi_data(city_name)
        if not aqi_data:
            flash("City not found or no AQI data available.")
            return redirect(url_for('search_city'))

        return render_template('city_detail.html', city=city_name, data=aqi_data)

    return render_template('search.html')


@app.route('/compare')
@login_required
def compare():
    saved_cities = SavedCity.query.filter_by(user_id=current_user.id).all()
    return render_template('compare.html', cities=saved_cities)

@app.route('/get_aqi_data/<city_name>')
def get_aqi_data_route(city_name):
    data = get_aqi_data(city_name)
    return jsonify(data)

@app.route('/check_alerts')
@login_required
def check_alerts():
    saved_cities = SavedCity.query.filter_by(user_id=current_user.id).all()
    alerts = []

    for city in saved_cities:
        aqi_data = get_aqi_data(city.city_name)
        if aqi_data and 'aqi' in aqi_data and int(aqi_data['aqi']) > city.alert_threshold:
            alerts.append({
                'city': city.city_name,
                'aqi': aqi_data['aqi'],
                'threshold': city.alert_threshold
            })

    return jsonify(alerts)

@app.route('/heatmap')
def heatmap():
    return render_template('heatmap.html')

# Helper Functions
def get_aqi_data(city_name):
    try:
        url = f"https://api.waqi.info/feed/{city_name}/?token={WAQI_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data['status'] == 'ok':
            return {
                'aqi': data['data']['aqi'],
                'station': data['data']['city']['name'],
                'time': data['data']['time']['s'],
                'iaqi': data['data']['iaqi'],
                'dominentpol': data['data'].get('dominentpol', 'Unknown')
            }
        return None
    except Exception as e:
        print(f"Error fetching AQI data: {e}")
        return None

def get_geo_data(city_name):
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if data:
            return {
                'lat': data[0]['lat'],
                'lon': data[0]['lon'],
                'name': data[0]['name'],
                'country': data[0]['country']
            }
        return None
    except Exception as e:
        print(f"Error fetching geo data: {e}")
        return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
