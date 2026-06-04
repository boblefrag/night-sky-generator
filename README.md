# Night Sky Generator

A Python project to generate realistic night sky maps.

## Preview

![Night Sky](night_sky.png)

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the Hipparcos star catalog:
   ```bash
   # Use -L to follow redirects (essential for CDS servers)
   curl -L -o hip_main.dat.gz https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat.gz
   # Alternative if the above fails:
   # curl -L -o hip_main.dat.gz https://vizier.cfa.harvard.edu/viz-bin/nph-Cat?I/239/hip_main.dat.gz
   
   gunzip hip_main.dat.gz
   ```

## Usage

Run the main script to generate a new night sky:
```bash
python generate_sky.py
```

## Files

- `generate_sky.py`: Main generation script.
- `night_sky.png`: Latest generated sky map.
- `constellations.json`, `constellations.npz`, `constellationship.fab`: Constellation data.
- `hip_main.dat`: Star catalog data (Hipparcos). **(Manual download required)**
- `de421.bsp`: Ephemeris data for celestial bodies.
