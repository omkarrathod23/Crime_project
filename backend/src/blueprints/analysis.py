from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
import os
import pandas as pd
import joblib
import folium
from sklearn.cluster import KMeans
from models.model import predict_crime_type
from src.eda import load_data
import matplotlib.pyplot as plt
import seaborn as sns

analysis_bp = Blueprint('analysis', __name__)

# Helper to load crime data from MongoDB
def load_crime_data():
    return load_data()

@analysis_bp.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    df = load_crime_data()
    locations = sorted(df['locality'].unique()) if not df.empty else []
    prediction = None
    if request.method == 'POST':
        location = request.form['location']
        date = request.form['date']
        hour = request.form['hour']
        features = {'locality': location, 'hour': hour, 'date': date}
        # Assuming the model is loaded in the blueprint or passed via current_app
        model_path = os.path.join(current_app.root_path, 'models', 'crime_type_rf.joblib')
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            prediction = predict_crime_type(model, features, df)
    return render_template('predict.html', locations=locations, prediction=prediction)

@analysis_bp.route('/eda')
@login_required
def eda():
    df = load_data()
    if df is None:
        return render_template('eda.html', error='Could not load crime data.', total_crimes=None, top_types_labels=[], top_types_values=[], trend_labels=[], trend_values=[], recent_cases=[], summary_stats={})
    
    total_crimes = len(df)
    top_types = df['crime_description'].value_counts().head(5)
    top_types_labels = [str(x) for x in top_types.index]
    top_types_values = [int(x) for x in top_types.values]
    
    recent_cases = []
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        try:
            df_sorted = df.sort_values('date', ascending=False)
        except Exception:
            df_sorted = df
        recent_cases = df_sorted.head(10).to_dict(orient='records')
    else:
        recent_cases = df.head(10).to_dict(orient='records')
    
    num_unique_crime_types = df['crime_description'].nunique() if 'crime_description' in df.columns else 0
    most_common_crime_types = df['crime_description'].value_counts().head(3).to_dict() if 'crime_description' in df.columns else {}
    most_affected_areas = df['locality'].value_counts().head(3).to_dict() if 'locality' in df.columns else {}
    
    def get_time_of_day(hour):
        try:
            h = int(hour)
            if 5 <= h < 12: return 'Morning'
            elif 12 <= h < 18: return 'Afternoon'
            else: return 'Night'
        except: return 'Unknown'
    
    if 'hour' in df.columns:
        df['time_of_day'] = df['hour'].apply(get_time_of_day)
        crimes_by_time_of_day = df['time_of_day'].value_counts().to_dict()
    else:
        crimes_by_time_of_day = {}
        
    summary_stats = {
        'total_crimes': total_crimes,
        'num_unique_crime_types': num_unique_crime_types,
        'most_common_crime_types': most_common_crime_types,
        'most_affected_areas': most_affected_areas,
        'crimes_by_time_of_day': crimes_by_time_of_day
    }
    return render_template(
        'eda.html',
        total_crimes=total_crimes,
        top_types_labels=top_types_labels,
        top_types_values=top_types_values,
        trend_labels=[],
        trend_values=[],
        error=None,
        recent_cases=recent_cases,
        summary_stats=summary_stats
    )

@analysis_bp.route('/hotspot', methods=['GET', 'POST'])
@login_required
def hotspot():
    df = load_data()
    if df is None or 'latitude' not in df.columns or 'longitude' not in df.columns:
        return render_template('hotspot.html', error='Could not load location data.', map_path=None, localities=[], selected_locality=None, criminals=[])
    
    df = df.dropna(subset=['latitude', 'longitude'])
    all_localities = sorted(df['locality'].dropna().unique())
    selected_locality = request.form.get('locality') or request.args.get('locality')
    
    filtered_df = df
    if selected_locality and selected_locality != 'All':
        filtered_df = df[df['locality'] == selected_locality]
    
    if len(filtered_df) > 0:
        coords = filtered_df[['latitude', 'longitude']].values
        n_clusters = min(3, len(filtered_df)) if len(filtered_df) >= 3 else max(1, len(filtered_df))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        filtered_df['cluster'] = kmeans.fit_predict(coords)
        centers = kmeans.cluster_centers_
    else:
        centers = []

    rasayani_center = [18.8600, 73.1500]
    m = folium.Map(location=rasayani_center, zoom_start=14, max_bounds=True)
    if len(filtered_df) > 0:
        bounds = [[filtered_df['latitude'].min(), filtered_df['longitude'].min()], 
                  [filtered_df['latitude'].max(), filtered_df['longitude'].max()]]
        m.fit_bounds(bounds)
    
    folium.Marker(location=rasayani_center, icon=folium.Icon(color='blue', icon='home'), popup='Rasayani City Center').add_to(m)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=4,
            color=colors[row['cluster'] % len(colors)],
            fill=True,
            fill_opacity=0.7,
            popup=row.get('locality', '')
        ).add_to(m)
    
    for i, center in enumerate(centers):
        folium.Marker(location=center, icon=folium.Icon(color=colors[i % len(colors)], icon='star'), popup=f'Hotspot Center {i+1}').add_to(m)
    
    map_dir = os.path.join(current_app.root_path, 'static')
    os.makedirs(map_dir, exist_ok=True)
    map_path = os.path.join(map_dir, 'hotspot_map.html')
    m.save(map_path)
    
    criminals = filtered_df[['crime_description', 'crime_domain', 'weapon_used', 'victim_age', 'victim_gender', 'criminal_name', 'hour', 'locality']].to_dict(orient='records') if len(filtered_df) > 0 else []
    return render_template('hotspot.html', error=None, map_path='static/hotspot_map.html', localities=all_localities, selected_locality=selected_locality, criminals=criminals)

@analysis_bp.route('/analytics')
@login_required
def analytics():
    # Simple analytics placeholder based on the original logic
    df = load_data()
    if df is None:
        return render_template('analytics.html', error='Could not load data.')
    
    total_crimes = len(df)
    crime_types = df['crime_description'].value_counts().head(5).to_dict()
    areas = df['locality'].value_counts().head(5).to_dict()
    
    return render_template('analytics.html', 
                         total_crimes=total_crimes,
                         crime_types=crime_types,
                         areas=areas)
