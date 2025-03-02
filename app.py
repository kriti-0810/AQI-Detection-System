import requests
from flask import Flask, render_template, request, jsonify
from config import API_KEY


app = Flask(__name__)

def get_weather(city):
    """Fetch weather data for a given city."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    return data

def get_aqi(lat, lon):
    """Fetch AQI data for given latitude and longitude."""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/weather', methods=['POST'])
def weather():
    city = request.json['city']
    weather_data = get_weather(city)

    if weather_data.get('cod') != 200:
        return jsonify({'error': 'City not found'})

    lat = weather_data['coord']['lat']
    lon = weather_data['coord']['lon']

    aqi_data = get_aqi(lat, lon)

    if 'list' not in aqi_data:
        return jsonify({'error': 'AQI data not available'})

    aqi = aqi_data['list'][0]['main']['aqi']

    aqi_description = {
        1: "Good 😊",
        2: "Fair 🙂",
        3: "Moderate 😐",
        4: "Poor 😟",
        5: "Very Poor 😷"
    }

    weather_info = {
        'city': weather_data['name'],
        'temperature': weather_data['main']['temp'],
        'humidity': weather_data['main']['humidity'],
        'description': weather_data['weather'][0]['description'],
        'icon': f"http://openweathermap.org/img/wn/{weather_data['weather'][0]['icon']}.png",
        'aqi': aqi,
        'aqi_status': aqi_description.get(aqi, "Unknown")
    }

    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True)
