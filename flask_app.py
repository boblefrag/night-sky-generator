from flask import Flask, render_template, request, send_file
import os
from datetime import datetime
from generate_sky import generate_night_sky

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Valeurs par défaut
    params = {
        'lat': 48.8566,
        'lon': 2.3522,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M'),
        'image_url': None
    }

    if request.method == 'POST':
        params['lat'] = float(request.form.get('lat', params['lat']))
        params['lon'] = float(request.form.get('lon', params['lon']))
        params['date'] = request.form.get('date', params['date'])
        params['time'] = request.form.get('time', params['time'])
        
        # Format date pour Skyfield (ISO8601)
        date_str = f"{params['date']}T{params['time']}:00Z"
        output_file = 'static/sky_output.png'
        
        if not os.path.exists('static'):
            os.makedirs('static')
            
        try:
            generate_night_sky(params['lat'], params['lon'], date_str, output_file)
            params['image_url'] = f"/{output_file}?{datetime.now().timestamp()}"
        except Exception as e:
            params['error'] = str(e)

    return render_template('index.html', **params)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=False)
