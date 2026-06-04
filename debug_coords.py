from skyfield.api import load, Star, wgs84, utc
from datetime import datetime, time

eph = load('de421.bsp')
earth = eph['earth']
ts = load.timescale()

# Paris, June 4, 2026 at midnight local (22:00 UTC)
t = ts.from_datetime(datetime(2026, 6, 4, 22, 0).replace(tzinfo=utc))
paris = earth + wgs84.latlon(48.8566, 2.3522)

# Dubhe (Alpha Ursae Majoris)
dubhe = Star(ra_hours=(11, 3, 43.67), dec_degrees=(61, 45, 3.2))

astrometric = paris.at(t).observe(dubhe)
alt, az, d = astrometric.apparent().altaz()

print(f"Date: {t.utc_strftime()}")
print(f"Dubhe (UMa) - Altitude: {alt.degrees:.2f}, Azimuth: {az.degrees:.2f}")

# Check another star: Spica (South in Spring/Summer)
spica = Star(ra_hours=(13, 25, 11.58), dec_degrees=(-11, 9, 40.7))
astrometric_s = paris.at(t).observe(spica)
alt_s, az_s, d_s = astrometric_s.apparent().altaz()
print(f"Spica - Altitude: {alt_s.degrees:.2f}, Azimuth: {az_s.degrees:.2f}")
