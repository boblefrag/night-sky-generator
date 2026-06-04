import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import Star, load, wgs84
import os
import json


def load_hipparcos_manual(filename, mag_limit=5.0):
    """Charge le catalogue Hipparcos sans Pandas (évite Illegal Instruction sur vieux CPU)."""
    hip_ids = []
    magnitudes = []
    ra_degrees = []
    dec_degrees = []

    with open(filename, "r") as f:
        for line in f:
            # Format Hipparcos hip_main.dat (pipe separated)
            # Col 1: HIP ID, Col 5: Vmag, Col 8: RAdeg, Col 9: DEdeg
            parts = line.split("|")
            if len(parts) < 10:
                continue
            try:
                mag_str = parts[5].strip()
                if not mag_str:
                    continue
                mag = float(mag_str)
                if mag <= mag_limit:
                    # On extrait tout d'abord pour être sûr que ça ne crash pas au milieu
                    hip_id = int(parts[1].strip())
                    ra = float(parts[8].strip())
                    dec = float(parts[9].strip())

                    # On n'ajoute que si tout est passé
                    hip_ids.append(hip_id)
                    magnitudes.append(mag)
                    ra_degrees.append(ra)
                    dec_degrees.append(dec)
            except (ValueError, IndexError):
                continue

    return {
        "ids": np.array(hip_ids),
        "mag": np.array(magnitudes),
        "ra": np.array(ra_degrees),
        "dec": np.array(dec_degrees),
    }


def generate_night_sky(latitude, longitude, date_str=None, output_file="night_sky.png"):
    eph = load("de421.bsp")
    ts = load.timescale()

    # Chargement manuel du catalogue
    stars_data = load_hipparcos_manual("hip_main.dat", mag_limit=6.5)

    if date_str:
        from datetime import datetime, timezone

        # Parsing manuel pour compatibilité maximale
        try:
            clean_date = date_str.replace("Z", "").split(".")[
                0
            ]  # On enlève Z et microsecondes
            dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
            t = ts.from_datetime(dt.replace(tzinfo=timezone.utc))
        except ValueError:
            t = ts.from_datetime(datetime.now(timezone.utc))
    else:
        from datetime import datetime, timezone

        t = ts.from_datetime(datetime.now(timezone.utc))

    observer = eph["earth"] + wgs84.latlon(latitude, longitude)
    obs_at_t = observer.at(t)

    # Étoiles brillantes pour l'affichage (mag < 4.5)
    mask = stars_data["mag"] <= 4.5
    bright_stars = Star(
        ra_hours=stars_data["ra"][mask] / 15.0, dec_degrees=stars_data["dec"][mask]
    )
    astrometric = obs_at_t.observe(bright_stars)
    altitude, azimuth, _ = astrometric.apparent().altaz()

    # Planètes
    bodies = {
        "Lune": eph["moon"],
        "Vénus": eph["venus"],
        "Mars": eph["mars"],
        "Jupiter": eph["jupiter barycenter"],
        "Saturne": eph["saturn barycenter"],
    }
    planet_positions = {}
    for name, body in bodies.items():
        alt, az, _ = obs_at_t.observe(body).apparent().altaz()
        if alt.degrees > 0:
            planet_positions[name] = (alt.degrees, az.degrees)

    # Objets Messier
    messier_objects = {
        "M31 (Andromède)": Star(ra_hours=(0, 42, 44.3), dec_degrees=(41, 16, 8)),
        "M44 (Crèche)": Star(ra_hours=(8, 40, 24), dec_degrees=(19, 41, 0)),
        "M13 (Hercule)": Star(ra_hours=(16, 41, 41.6), dec_degrees=(36, 27, 40)),
    }
    messier_positions = {}
    for name, star in messier_objects.items():
        alt, az, _ = obs_at_t.observe(star).apparent().altaz()
        if alt.degrees > 15:
            messier_positions[name] = (alt.degrees, az.degrees)

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

    # Constellations
    if os.path.exists("constellations.json"):
        with open("constellations.json", "r") as f:
            const_data = json.load(f)

        # On calcule les positions de TOUTES les étoiles nécessaires aux constellations
        all_hip_ids = set()
        for const in const_data.get("constellations", []):
            for line in const.get("lines", []):
                for hip in line:
                    all_hip_ids.add(hip)

        # On retrouve les coordonnées RA/Dec pour ces IDs dans notre dictionnaire manuel
        hip_to_idx = {hip: i for i, hip in enumerate(stars_data["ids"])}
        needed_ids = [hip for hip in all_hip_ids if hip in hip_to_idx]
        indices = [hip_to_idx[hip] for hip in needed_ids]

        if indices:
            const_stars = Star(
                ra_hours=stars_data["ra"][indices] / 15.0,git pus
                dec_degrees=stars_data["dec"][indices],
            )
            alt_c, az_c, _ = obs_at_t.observe(const_stars).apparent().altaz()
            hip_map = {
                needed_ids[i]: (np.deg2rad(az_c.degrees[i]), 90 - alt_c.degrees[i])
                for i in range(len(needed_ids))
                if alt_c.degrees[i] > 0
            }

            for constellation in const_data.get("constellations", []):
                for line in constellation.get("lines", []):
                    for i in range(len(line) - 1):
                        if line[i] in hip_map and line[i + 1] in hip_map:
                            t1, r1 = hip_map[line[i]]
                            t2, r2 = hip_map[line[i + 1]]
                            ax.plot(
                                [t1, t2],
                                [r1, r2],
                                color="black",
                                alpha=0.15,
                                linewidth=0.7,
                            )

    # Étoiles
    theta = np.deg2rad(azimuth.degrees)
    r = 90 - altitude.degrees
    m = altitude.degrees > 0
    sizes = (5.5 - stars_data["mag"][mask][m]) ** 2 * 3
    ax.scatter(
        theta[m], r[m], s=sizes, color="black", alpha=1.0, edgecolors="none", zorder=2
    )

    # Objets Messier et Planètes
    for name, (alt, az) in messier_positions.items():
        ax.scatter(
            np.deg2rad(az),
            90 - alt,
            s=60,
            facecolors="none",
            edgecolors="blue",
            linestyle="--",
            alpha=0.6,
        )
    for name, (alt, az) in planet_positions.items():
        p_t, p_r = np.deg2rad(az), 90 - alt
        ax.scatter(p_t, p_r, s=150, color="black", edgecolors="white", zorder=10)
        ax.text(
            p_t,
            p_r + 4,
            name,
            color="black",
            fontsize=10,
            fontweight="bold",
            ha="center",
        )

    # Style
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)
    ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels(
        ["NORD", "EST", "SUD", "OUEST"], color="black", fontsize=14, fontweight="bold"
    )
    ax.grid(color="black", alpha=0.1, linestyle=":")
    ax.spines["polar"].set_visible(False)

    plt.title(
        f"CARTE DU CIEL - {t.utc_strftime('%Y-%m-%d %H:%M UTC')}",
        color="black",
        pad=40,
        fontsize=18,
    )
    plt.savefig(output_file, facecolor="white", bbox_inches="tight", dpi=150)
    plt.close()


if __name__ == "__main__":
    generate_night_sky(48.8566, 2.3522)
