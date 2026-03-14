import pandas as pd
import os
import glob
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_crime_data(folder_path=None):
    """
    Load and merge all CSV files in the given folder, clean, and explore the dataset.
    - Standardizes column names (lowercase, underscores)
    - Parses 'date' and 'time' columns if available
    - Prints shape, columns, null count
    Returns: Cleaned DataFrame
    """
    if folder_path is None:
        # Always resolve relative to the project root
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        folder_path = os.path.join(script_dir, 'data', 'rasayani_crime_dataset')
    all_files = glob.glob(os.path.join(folder_path, "rasayani_crime_dataset_corrected.csv"))
    if not all_files:
        logging.error(f"No corrected CSV file found in {folder_path}")
        return None
    df_list = []
    for file in all_files:
        df = pd.read_csv(file)
        df_list.append(df)
    df = pd.concat(df_list, ignore_index=True)

    # Standardize column names
    df.columns = [re.sub(r'\s+', '_', col.strip().lower()) for col in df.columns]

    # Parse date/time columns if present
    for col in df.columns:
        if re.search(r'date|time', col):
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
                logging.info(f"Parsed column '{col}' as datetime if possible.")
            except Exception as e:
                logging.warning(f"Could not parse '{col}' as datetime: {e}")

    # Print shape, columns, null count
    print(f"\n--- Data Shape: {df.shape} ---")
    print(f"--- Columns: {df.columns.tolist()} ---")
    print("--- Null Values ---")
    print(df.isnull().sum())

    return df

if __name__ == "__main__":
    df = load_crime_data() 