from skyfield.api import load, Star, wgs84, utc
from skyfield.data import hipparcos
from datetime import datetime, timezone

def debug_uma():
    eph = load('de421.bsp')
    ts = load.timescale()
    
    # Paris, 4 June 2026 at 22:00 UTC (Midnight local)
    t = ts.from_datetime(datetime(2026, 6, 4, 22, 0, tzinfo=utc))
    paris = eph['earth'] + wgs84.latlon(48.8566, 2.3522)
    obs = paris.at(t)
    
    # Famous stars in Ursa Major
    uma_stars = {
        'Dubhe': Star(ra_hours=(11, 3, 43.67), dec_degrees=(61, 45, 3.2)),
        'Merak': Star(ra_hours=(11, 1, 50.47), dec_degrees=(56, 22, 56.7)),
        'Phecda': Star(ra_hours=(11, 53, 49.83), dec_degrees=(53, 41, 41.1)),
        'Megrez': Star(ra_hours=(12, 15, 25.56), dec_degrees=(57, 1, 42.9)),
        'Alioth': Star(ra_hours=(12, 54, 1.63), dec_degrees=(55, 57, 35.4)),
        'Mizar': Star(ra_hours=(13, 23, 55.54), dec_degrees=(54, 55, 31.3)),
        'Alkaid': Star(ra_hours=(13, 47, 32.44), dec_degrees=(49, 18, 47.9))
    }
    
    print(f"Location: Paris (48.85N, 2.35E)")
    print(f"Time: {t.utc_strftime()}")
    print("-" * 40)
    for name, star in uma_stars.items():
        alt, az, d = obs.observe(star).apparent().altaz()
        print(f"{name:7}: Alt {alt.degrees:5.1f}°, Az {az.degrees:5.1f}°")

if __name__ == "__main__":
    debug_uma()
