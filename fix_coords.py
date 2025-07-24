import pandas as pd

# Load the dataset
input_path = 'data/rasayani_crime_dataset/rasayani_crime_dataset.csv'
output_path = 'data/rasayani_crime_dataset/rasayani_crime_dataset_corrected.csv'

def is_valid_lat(lat):
    try:
        lat = float(lat)
        return -90 <= lat <= 90
    except:
        return False

def is_valid_lon(lon):
    try:
        lon = float(lon)
        return -180 <= lon <= 180
    except:
        return False

def fix_lat_lon(row):
    lat, lon = row['Latitude'], row['Longitude']
    # If both are valid, return as is
    if is_valid_lat(lat) and is_valid_lon(lon):
        return lat, lon
    # If swapped, fix them
    if is_valid_lat(lon) and is_valid_lon(lat):
        print(f"Swapped lat/lon detected, fixing: {lat}, {lon}")
        return lon, lat
    # If invalid, set to None
    print(f"Invalid lat/lon: {lat}, {lon}")
    return None, None

def main():
    df = pd.read_csv(input_path)
    if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
        print("No Latitude/Longitude columns found!")
        return
    # Fix coordinates
    df[['Latitude', 'Longitude']] = df.apply(lambda row: pd.Series(fix_lat_lon(row)), axis=1)
    # Warn about any remaining invalids
    invalids = df[~df['Latitude'].apply(is_valid_lat) | ~df['Longitude'].apply(is_valid_lon)]
    if not invalids.empty:
        print("Rows with invalid coordinates after fixing:")
        print(invalids[['Latitude', 'Longitude']])
    # Save corrected file
    df.to_csv(output_path, index=False)
    print(f"Corrected file saved to {output_path}")

if __name__ == '__main__':
    main() 