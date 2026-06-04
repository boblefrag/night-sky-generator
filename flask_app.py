from datetime import datetime
import os
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, send_file
from generate_sky import generate_night_sky

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    # ZoneInfo pour gérer l'heure française (hiver/été auto)
    tz_paris = ZoneInfo("Europe/Paris")
    maintenant_paris = datetime.now(tz_paris)

    # Valeurs par défaut calées sur l'heure locale française
    params = {
        "lat": 48.8566,
        "lon": 2.3522,
        "date": maintenant_paris.strftime("%Y-%m-%d"),
        "time": maintenant_paris.strftime("%H:%M"),
        "image_url": None,
    }

    if request.method == "POST":
        params["lat"] = float(request.form.get("lat", params["lat"]))
        params["lon"] = float(request.form.get("lon", params["lon"]))
        params["date"] = request.form.get("date", params["date"])
        params["time"] = request.form.get("time", params["time"])

        # 1. On reconstruit la string locale saisie dans le formulaire
        local_date_str = f"{params['date']} {params['time']}:00"

        # 2. On la convertit en objet datetime "aware" avec le fuseau Paris
        naive_date = datetime.strptime(local_date_str, "%Y-%m-%d %H:%M:%S")
        date_paris = naive_date.replace(tzinfo=tz_paris)

        # 3. On passe cet objet datetime complet à ton script Skyfield
        output_file = "static/sky_output.png"

        if not os.path.exists("static"):
            os.makedirs("static")

        try:
            # MODIFICATION ICI : On passe l'objet datetime 'date_paris' au lieu de la string ISO
            generate_night_sky(params["lat"], params["lon"], date_paris, output_file)
            params["image_url"] = f"/{output_file}?{datetime.now().timestamp()}"
        except Exception as e:
            params["error"] = str(e)

    return render_template("index.html", **params)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=False)
