import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import Star, load, wgs84, utc
from skyfield.data import hipparcos
from skyfield.projections import build_stereographic_projection

def generate_night_sky(latitude, longitude, date_str=None, output_file='night_sky.png'):
    # Load ephemeris and star catalog
    eph = load('de421.bsp')
    with load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)

    ts = load.timescale()
    if date_str:
        t = ts.from_iso8601(date_str)
    else:
        from skyfield import almanac
        from datetime import datetime, timezone, timedelta
        
        # Current date
        now = datetime.now(timezone.utc)
        t0 = ts.from_datetime(now.replace(hour=0, minute=0, second=0, microsecond=0))
        t1 = ts.from_datetime(t0.utc_datetime() + timedelta(days=1))
        # Find astronomical twilight (Sun at -18 degrees)
        earth = eph['earth']
        sun = eph['sun']
        location = wgs84.latlon(latitude, longitude)

        # Astronomical twilight is when the sun is 18 degrees below horizon
        f = almanac.risings_and_settings(eph, sun, location, horizon_degrees=-18)
        times, events = almanac.find_discrete(t0, t1, f)

        # We want the setting (event 0) of the sun at -18 degrees
        t = None
        if len(times) > 0:
            for i in range(len(times)):
                if events[i] == 0: # Sun goes below -18 degrees
                    t = times[i]
                    break

        if t is None:
            # Fallback for summer in high latitudes or if no event found
            t = ts.from_datetime(now.replace(hour=22, minute=0, second=0, microsecond=0))

        # Observer location
        earth = eph['earth']

    observer = earth + wgs84.latlon(latitude, longitude)
    obs_at_t = observer.at(t)
    
    # Filter stars: magnitude < 4.5 for more clarity
    bright_stars = df[df['magnitude'] <= 4.5]
    star_positions = Star.from_dataframe(bright_stars)
    
    # Calculate positions
    astrometric = obs_at_t.observe(star_positions)
    altitude, azimuth, distance = astrometric.apparent().altaz()

    # Planets and Moon
    bodies = {
        'Mercure': eph['mercury'],
        'Vénus': eph['venus'],
        'Mars': eph['mars'],
        'Jupiter': eph['jupiter barycenter'],
        'Saturne': eph['saturn barycenter'],
        'Lune': eph['moon']
    }

    planet_positions = {}
    for name, body in bodies.items():
        astrometric_p = obs_at_t.observe(body)
        alt, az, d = astrometric_p.apparent().altaz()
        if alt.degrees > 0: # Only visible
            planet_positions[name] = (alt.degrees, az.degrees)

    # --- Messier Objects ---
    messier_objects = {
        'M13 (Amas Hercule)': Star(ra_hours=(16, 41, 41.6), dec_degrees=(36, 27, 40)),
        'M31 (Andromède)': Star(ra_hours=(0, 42, 44.3), dec_degrees=(41, 16, 8)),
        'M51 (Tourbillon)': Star(ra_hours=(13, 29, 52.4), dec_degrees=(47, 11, 40)),
        'M57 (Lyre)': Star(ra_hours=(18, 53, 35.1), dec_degrees=(33, 1, 45)),
        'M81 (Bode)': Star(ra_hours=(9, 55, 33.2), dec_degrees=(69, 3, 55)),
        'M8 (Lagune)': Star(ra_hours=(18, 3, 37), dec_degrees=(-24, 23, 12)),
        'M27 (Haltère)': Star(ra_hours=(19, 59, 36.3), dec_degrees=(22, 43, 16)),
        'M44 (Crèche)': Star(ra_hours=(8, 40, 24), dec_degrees=(19, 41, 0))
    }

    messier_positions = {}
    for name, star in messier_objects.items():
        astrometric_m = obs_at_t.observe(star)
        alt, az, d = astrometric_m.apparent().altaz()
        if alt.degrees > 15: # Seulement si bien visible
            messier_positions[name] = (alt.degrees, az.degrees)

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={'projection': 'polar'})

    theta = np.deg2rad(azimuth.degrees)
    r = 90 - altitude.degrees
    mask = altitude.degrees > 0
    sizes = (5.5 - bright_stars['magnitude'][mask]) ** 2 * 3

    # --- Constellations ---
    import json
    import os
    const_file = 'constellations.json'
    if os.path.exists(const_file):
        with open(const_file, 'r') as f:
            const_data = json.load(f)
        fr_names = {
            'Ursa Major': 'Grande Ourse', 'Ursa Minor': 'Petite Ourse', 'Cassiopeia': 'Cassiopée',
            'Orion': 'Orion', 'Leo': 'Lion', 'Cygnus': 'Cygne', 'Lyra': 'Lyre', 'Aquila': 'Aigle',
            'Scorpius': 'Scorpion', 'Sagittarius': 'Sagittaire', 'Boötes': 'Bouvier', 'Virgo': 'Vierge',
            'Gemini': 'Gémeaux', 'Taurus': 'Taureau', 'Canis Major': 'Grand Chien', 'Pegasus': 'Pégase',
            'Andromeda': 'Andromède', 'Cepheus': 'Céphée', 'Draco': 'Dragon', 'Hercules': 'Hercule',
            'Corona Borealis': 'Couronne Boréale'
        }
        all_hip_ids = set()
        for const in const_data.get('constellations', []):
            for line in const.get('lines', []):
                for hip in line:
                    if hip in df.index: all_hip_ids.add(hip)
        hip_list = list(all_hip_ids)
        stars_to_calc = Star.from_dataframe(df.loc[hip_list])
        astrometric_const = obs_at_t.observe(stars_to_calc)
        alt_c, az_c, _ = astrometric_const.apparent().altaz()
        hip_map = {hip: (np.deg2rad(az_c.degrees[i]), 90 - alt_c.degrees[i]) 
                  for i, hip in enumerate(hip_list) if alt_c.degrees[i] > 0}
        for constellation in const_data.get('constellations', []):
            lines, native_name = constellation.get('lines', []), constellation.get('common_name', {}).get('native', '')
            name, x_list, y_list = fr_names.get(native_name, native_name), [], []
            for line in lines:
                for i in range(len(line) - 1):
                    if line[i] in hip_map and line[i+1] in hip_map:
                        t1, r1 = hip_map[line[i]]
                        t2, r2 = hip_map[line[i+1]]
                        ax.plot([t1, t2], [r1, r2], color='black', alpha=0.15, linewidth=0.7)
                        x_list.extend([t1, t2]); y_list.extend([r1, r2])
            if x_list and name:
                avg_theta, avg_r = np.mean(x_list), np.mean(y_list)
                if avg_r < 85:
                    ax.text(avg_theta, avg_r, name, color='black', alpha=0.4, fontsize=8, ha='center', style='italic')

    # Draw stars
    ax.scatter(theta[mask], r[mask], s=sizes, color='black', alpha=1.0, edgecolors='none', zorder=2)

    # Draw Messier Objects
    for name, (alt, az) in messier_positions.items():
        m_theta, m_r = np.deg2rad(az), 90 - alt
        ax.scatter(m_theta, m_r, s=60, facecolors='none', edgecolors='blue', marker='o', linestyle='--', alpha=0.6)
        ax.text(m_theta, m_r + 2, name, color='blue', fontsize=7, alpha=0.8, ha='center')

    # Draw planets
    for name, (alt, az) in planet_positions.items():
        p_theta, p_r = np.deg2rad(az), 90 - alt
        ax.scatter(p_theta, p_r, s=150, color='black', edgecolors='white', zorder=10)
        ax.text(p_theta, p_r + 4, name, color='black', fontsize=12, fontweight='bold', ha='center', 
                bbox=dict(facecolor='white', alpha=0.7, lw=0))

    # Formatting
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(1) # CCW: North=0, East=Left
    ax.set_ylim(0, 90); ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels(['NORD', 'EST', 'SUD', 'OUEST'], color='black', fontsize=14, fontweight='bold')
    ax.set_facecolor('white')
    ax.grid(color='black', alpha=0.1, linestyle=':')
    ax.spines['polar'].set_visible(False)
    
    plt.title(f'CARTE DU CIEL (Atlas Noir sur Blanc) - {t.utc_strftime("%Y-%m-%d %H:%M UTC")}', color='black', pad=40, fontsize=18)
    plt.savefig(output_file, facecolor='white', bbox_inches='tight', dpi=150)
    print(f"Image générée en mode Atlas : {output_file}")

if __name__ == "__main__":
    generate_night_sky(48.8566, 2.3522)
