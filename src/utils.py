"""
utils.py - Common helper functions for the Crime Management System
"""

import pandas as pd
from geopy.geocoders import Nominatim
import time
import os

def print_divider():
    print("\n" + "-"*40 + "\n")

def update_locality_coordinates(csv_path, output_path=None, locality_col='Locality', lat_col='Latitude', lon_col='Longitude', delay=1):
    df = pd.read_csv(csv_path)
    geolocator = Nominatim(user_agent="crime_map")
    # Find unique localities
    localities = df[locality_col].dropna().unique()
    locality_coords = {}
    for loc in localities:
        try:
            location = geolocator.geocode(f"{loc}, Maharashtra, India")
            if location:
                locality_coords[loc] = (location.latitude, location.longitude)
                print(f"{loc}: {location.latitude}, {location.longitude}")
            else:
                print(f"Could not geocode: {loc}")
                locality_coords[loc] = (None, None)
        except Exception as e:
            print(f"Error geocoding {loc}: {e}")
            locality_coords[loc] = (None, None)
        time.sleep(delay)  # To avoid hitting API rate limits
    # Update DataFrame
    for loc, (lat, lon) in locality_coords.items():
        df.loc[df[locality_col] == loc, lat_col] = lat
        df.loc[df[locality_col] == loc, lon_col] = lon
    # Save to output
    if not output_path:
        base, ext = os.path.splitext(csv_path)
        output_path = f"{base}_corrected{ext}"
    df.to_csv(output_path, index=False)
    print(f"Saved corrected data to {output_path}")

if __name__ == "__main__":
    update_locality_coordinates(
        'data/rasayani_crime_dataset/rasayani_crime_dataset_corrected.csv',
        locality_col='Locality',
        lat_col='Latitude',
        lon_col='Longitude',
        delay=1
    ) 