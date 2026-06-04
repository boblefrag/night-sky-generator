import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos
from datetime import datetime, timezone
import json
import os

# --- Page Config ---
st.set_page_config(page_title="Night Sky Generator", page_icon="🌌", layout="wide")

st.title("🌌 Night Sky Generator")
st.markdown("Générez votre carte du ciel personnalisée en temps réel.")

# --- Sidebar / Controls ---
with st.sidebar:
    st.header("Configuration")
    lat = st.number_input("Latitude", value=48.8566, format="%.4f")
    lon = st.number_input("Longitude", value=2.3522, format="%.4f")
    date_val = st.date_input("Date", value=datetime.now())
    time_val = st.time_input("Heure (UTC)", value=datetime.now(timezone.utc).time())
    
    mag_limit = st.slider("Magnitude limite (clarté)", 2.0, 6.0, 4.5, 0.1)
    show_messier = st.checkbox("Afficher les objets Messier", value=True)
    style = st.selectbox("Style", ["Atlas (Blanc)", "Deep Space (Noir)"])

# --- Core Logic (Optimized for Streamlit) ---
@st.cache_resource
def load_data():
    eph = load('de421.bsp')
    ts = load.timescale()
    with load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)
    
    # Load constellations
    const_data = {}
    if os.path.exists('constellations.json'):
        with open('constellations.json', 'r') as f:
            const_data = json.load(f)
            
    return eph, ts, df, const_data

eph, ts, df, const_data = load_data()

def get_sky_map(latitude, longitude, dt, magnitude_limit, show_m, style_choice):
    t = ts.from_datetime(dt.replace(tzinfo=timezone.utc))
    earth = eph['earth']
    observer = earth + wgs84.latlon(latitude, longitude)
    obs_at_t = observer.at(t)
    
    # Filter stars
    bright_stars = df[df['magnitude'] <= magnitude_limit]
    star_positions = Star.from_dataframe(bright_stars)
    astrometric = obs_at_t.observe(star_positions)
    altitude, azimuth, _ = astrometric.apparent().altaz()
    mask = altitude.degrees > 0

    # Colors and Style
    bg_color = 'white' if style_choice == "Atlas (Blanc)" else '#050a14'
    text_color = 'black' if style_choice == "Atlas (Blanc)" else 'white'
    line_color = 'black' if style_choice == "Atlas (Blanc)" else '#1e3a5f'
    star_color = 'black' if style_choice == "Atlas (Blanc)" else 'white'

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    # Draw constellations
    if const_data:
        fr_names = {'Ursa Major': 'Grande Ourse', 'Ursa Minor': 'Petite Ourse', 'Cassiopeia': 'Cassiopée', 'Orion': 'Orion', 'Leo': 'Lion', 'Cygnus': 'Cygne', 'Lyra': 'Lyre', 'Aquila': 'Aigle', 'Scorpius': 'Scorpion', 'Sagittarius': 'Sagittaire', 'Boötes': 'Bouvier', 'Virgo': 'Vierge', 'Gemini': 'Gémeaux', 'Taurus': 'Taureau', 'Canis Major': 'Grand Chien', 'Pegasus': 'Pégase', 'Andromeda': 'Andromède', 'Cepheus': 'Céphée', 'Draco': 'Dragon', 'Hercules': 'Hercule', 'Corona Borealis': 'Couronne Boréale'}
        
        all_hip_ids = set()
        for const in const_data.get('constellations', []):
            for line in const.get('lines', []):
                for hip in line:
                    if hip in df.index: all_hip_ids.add(hip)
        
        stars_to_calc = Star.from_dataframe(df.loc[list(all_hip_ids)])
        astrometric_const = obs_at_t.observe(stars_to_calc)
        alt_c, az_c, _ = astrometric_const.apparent().altaz()
        
        hip_map = {hip: (np.deg2rad(az_c.degrees[i]), 90 - alt_c.degrees[i]) 
                  for i, hip in enumerate(all_hip_ids) if alt_c.degrees[i] > 0}
        
        for constellation in const_data.get('constellations', []):
            native_name = constellation.get('common_name', {}).get('native', '')
            name = fr_names.get(native_name, native_name)
            x_l, y_l = [], []
            for line in constellation.get('lines', []):
                for i in range(len(line) - 1):
                    if line[i] in hip_map and line[i+1] in hip_map:
                        t1, r1 = hip_map[line[i]]
                        t2, r2 = hip_map[line[i+1]]
                        ax.plot([t1, t2], [r1, r2], color=line_color, alpha=0.3, linewidth=0.8)
                        x_l.extend([t1, t2]); y_l.extend([r1, r2])
            if x_l and name:
                ax.text(np.mean(x_l), np.mean(y_l), name, color=text_color, alpha=0.5, fontsize=7, ha='center')

    # Draw stars
    theta = np.deg2rad(azimuth.degrees[mask])
    r = 90 - altitude.degrees[mask]
    sizes = (magnitude_limit + 1 - bright_stars['magnitude'][mask]) ** 2 * 2
    ax.scatter(theta, r, s=sizes, color=star_color, alpha=0.8, edgecolors='none', zorder=2)

    # Planets
    bodies = {'Lune': eph['moon'], 'Vénus': eph['venus'], 'Mars': eph['mars'], 'Jupiter': eph['jupiter barycenter'], 'Saturne': eph['saturn barycenter']}
    for name, body in bodies.items():
        astrometric_p = obs_at_t.observe(body)
        alt, az, _ = astrometric_p.apparent().altaz()
        if alt.degrees > 0:
            p_theta, p_r = np.deg2rad(az.degrees), 90 - alt.degrees
            ax.scatter(p_theta, p_r, s=100, color=star_color, edgecolors=bg_color, zorder=10)
            ax.text(p_theta, p_r + 3, name, color=text_color, fontsize=9, fontweight='bold', ha='center')

    # Formatting
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(1)
    ax.set_ylim(0, 90)
    ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels(['N', 'E', 'S', 'W'], color=text_color, fontsize=12, fontweight='bold')
    ax.grid(color=text_color, alpha=0.2, linestyle=':')
    ax.spines['polar'].set_visible(False)
    
    return fig

# --- Main Interface ---
dt = datetime.combine(date_val, time_val)
fig = get_sky_map(lat, lon, dt, mag_limit, show_messier, style)

col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.pyplot(fig)

st.info(f"Carte générée pour {lat}, {lon} le {dt.strftime('%d/%m/%Y à %H:%M')} UTC")
