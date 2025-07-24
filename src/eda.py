import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DATA_PATH = "data/rasayani_crime_dataset/rasayani_crime_dataset_corrected.csv"

# Utility to load data
def load_data(filepath=DATA_PATH):
    try:
        df = pd.read_csv(filepath)
        # Normalize column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        logging.info(f"Loaded data with shape: {df.shape}")
        return df
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return None

PLOT_DIR = "eda_plots"
os.makedirs(PLOT_DIR, exist_ok=True)

def plot_crime_types(df, save=False):
    plt.figure(figsize=(10, 6))
    top_types = df['crime_description'].value_counts().head(10)
    sns.barplot(x=top_types.values, y=top_types.index, palette='viridis')
    plt.title('Top 10 Crime Types')
    plt.xlabel('Number of Crimes')
    plt.ylabel('Crime Type')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, 'top_crime_types.png'))
    plt.show()

def plot_crime_by_location(df, save=False):
    plt.figure(figsize=(10, 6))
    top_locs = df['locality'].value_counts().head(10)
    sns.barplot(x=top_locs.values, y=top_locs.index, palette='magma')
    plt.title('Top 10 Crime Locations')
    plt.xlabel('Number of Crimes')
    plt.ylabel('Location')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, 'top_crime_locations.png'))
    plt.show()

def plot_crime_trend(df, date_col='date', freq='M', save=False):
    if date_col not in df.columns:
        logging.warning(f"Column '{date_col}' not found for time-series plot.")
        return
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if freq == 'Y':
        df['period'] = df[date_col].dt.year
        title = 'Crime Trend by Year'
        fname = 'crime_trend_year.png'
    elif freq == 'M':
        df['period'] = df[date_col].dt.to_period('M')
        title = 'Crime Trend by Month'
        fname = 'crime_trend_month.png'
    elif freq == 'Q':
        df['period'] = df[date_col].dt.to_period('Q')
        title = 'Crime Trend by Quarter'
        fname = 'crime_trend_quarter.png'
    else:
        df['period'] = df[date_col]
        title = 'Crime Trend'
        fname = 'crime_trend.png'
    trend = df.groupby('period').size()
    plt.figure(figsize=(12, 6))
    trend.plot(marker='o')
    plt.title(title)
    plt.xlabel('Period')
    plt.ylabel('Number of Crimes')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, fname))
    plt.show()

def plot_crime_heatmap(df, save=False):
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        logging.warning("Latitude/Longitude columns not found for heatmap.")
        return
    plt.figure(figsize=(8, 8))
    sns.kdeplot(
        x=df['longitude'], y=df['latitude'],
        cmap="Reds", fill=True, thresh=0.05, levels=100
    )
    plt.title('Crime Hotspot Heatmap')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, 'crime_heatmap.png'))
    plt.show()

def plot_crime_by_gender(df, save=False):
    if 'victim_gender' not in df.columns:
        logging.warning("victim_gender column not found.")
        return
    plt.figure(figsize=(6, 4))
    gender_counts = df['victim_gender'].value_counts()
    sns.barplot(x=gender_counts.index, y=gender_counts.values, palette='pastel')
    plt.title('Crimes by Victim Gender')
    plt.xlabel('Gender')
    plt.ylabel('Number of Crimes')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, 'crimes_by_gender.png'))
    plt.show()

def plot_crime_by_age_group(df, save=False):
    if 'victim_age' not in df.columns:
        logging.warning("victim_age column not found.")
        return
    bins = [0, 18, 35, 60, 100]
    labels = ['0-18', '19-35', '36-60', '60+']
    df['age_group'] = pd.cut(df['victim_age'], bins=bins, labels=labels, right=False)
    age_counts = df['age_group'].value_counts().sort_index()
    plt.figure(figsize=(8, 4))
    sns.barplot(x=age_counts.index, y=age_counts.values, palette='Blues')
    plt.title('Crimes by Victim Age Group')
    plt.xlabel('Age Group')
    plt.ylabel('Number of Crimes')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, 'crimes_by_age_group.png'))
    plt.show()

def plot_weapon_usage(df, save=False):
    if 'weapon_used' not in df.columns:
        logging.warning("weapon_used column not found.")
        return
    plt.figure(figsize=(8, 4))
    weapon_counts = df['weapon_used'].value_counts().head(10)
    sns.barplot(x=weapon_counts.values, y=weapon_counts.index, palette='OrRd')
    plt.title('Top Weapons Used in Crimes')
    plt.xlabel('Number of Crimes')
    plt.ylabel('Weapon Used')
    plt.tight_layout()
    if save:
        plt.savefig(os.path.join(PLOT_DIR, 'weapon_usage.png'))
    plt.show()

def main():
    df = load_data()
    if df is None:
        return
    plot_crime_types(df, save=True)
    plot_crime_by_location(df, save=True)
    plot_crime_trend(df, date_col='date', freq='M', save=True)
    plot_crime_trend(df, date_col='date', freq='Y', save=True)
    plot_crime_heatmap(df, save=True)
    plot_crime_by_gender(df, save=True)
    plot_crime_by_age_group(df, save=True)
    plot_weapon_usage(df, save=True)

if __name__ == "__main__":
    from data_loader import load_crime_data
    df = load_crime_data()
    plot_crime_types(df, save=True)
    plot_crime_by_location(df, save=True)
    plot_crime_trend(df, date_col='date', freq='M', save=True)
    plot_crime_trend(df, date_col='date', freq='Y', save=True)
    plot_crime_heatmap(df, save=True)
    plot_crime_by_gender(df, save=True)
    plot_crime_by_age_group(df, save=True)
    plot_weapon_usage(df, save=True) 