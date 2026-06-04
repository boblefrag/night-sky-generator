from skyfield.api import load
from skyfield.data import hipparcos
with load.open(hipparcos.URL) as f:
    df = hipparcos.load_dataframe(f)
print(df.columns)
