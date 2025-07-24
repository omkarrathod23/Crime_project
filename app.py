import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import joblib
from models.model import predict_crime_type
from src.eda import load_data
from sklearn.cluster import KMeans
import folium

app = Flask(__name__, template_folder='src/templates')
app.secret_key = 'your_secret_key'  # Change this in production

DATA_PATH = os.path.join('data', 'rasayani_crime_dataset')
STATIC_IMG_PATH = os.path.join('static', 'images')
os.makedirs(STATIC_IMG_PATH, exist_ok=True)

# Utility to load data
def load_crime_data(folder_path=None):
    import glob, re, os
    if folder_path is None:
        folder_path = os.path.join('data', 'rasayani_crime_dataset')
    search_path = os.path.join(folder_path, 'rasayani_crime_dataset_corrected.csv')
    print('Looking for file in:', search_path)
    all_files = glob.glob(search_path)
    print('Found files:', all_files)
    df_list = [pd.read_csv(f) for f in all_files]
    if not df_list:
        print('No files found to load!')
    df = pd.concat(df_list, ignore_index=True)
    df.columns = [re.sub(r'\s+', '_', c.strip().lower()) for c in df.columns]
    return df

def get_top_crime_types(df, n=5):
    return df['crime_description'].value_counts().head(n)

# Load model and data once
model = joblib.load('models/crime_type_rf.joblib')
data = load_crime_data()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'rasayani' and password == 'rasayani123':
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    df = data
    total_crimes = len(df)
    top_types = get_top_crime_types(df)
    # Generate and save bar chart
    plt.figure(figsize=(8,4))
    sns.barplot(x=top_types.values, y=top_types.index, palette='viridis')
    plt.title('Top 5 Crime Types')
    plt.xlabel('Count')
    plt.tight_layout()
    chart_path = os.path.join(STATIC_IMG_PATH, 'chart.png')
    plt.savefig(chart_path)
    plt.close()
    return render_template('dashboard.html', total_crimes=total_crimes, top_types=top_types, chart_url='/static/images/chart.png')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    df = data
    locations = sorted(df['locality'].unique())
    prediction = None
    if request.method == 'POST':
        location = request.form['location']
        date = request.form['date']
        hour = request.form['hour']
        features = {'locality': location, 'hour': hour, 'date': date}
        prediction = predict_crime_type(model, features, df)
    return render_template('predict.html', locations=locations, prediction=prediction)

@app.route('/eda')
def eda():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    df = load_data()
    if df is None:
        return render_template('eda.html', error='Could not load crime data.', total_crimes=None, top_types_labels=[], top_types_values=[], trend_labels=[], trend_values=[], recent_cases=[], summary_stats={})
    total_crimes = len(df)
    # Top 5 crime types
    top_types = df['crime_description'].value_counts().head(5)
    top_types_labels = [str(x) for x in top_types.index]
    top_types_values = [int(x) for x in top_types.values]
    # No date column, so skip monthly trend
    trend_labels = []
    trend_values = []
    # Prepare recent cases (last 10 by date if possible)
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
    # Basic summary statistics
    num_unique_crime_types = df['crime_description'].nunique() if 'crime_description' in df.columns else 0
    most_common_crime_types = df['crime_description'].value_counts().head(3).to_dict() if 'crime_description' in df.columns else {}
    most_affected_areas = df['locality'].value_counts().head(3).to_dict() if 'locality' in df.columns else {}
    # Crimes by time of day
    def get_time_of_day(hour):
        try:
            h = int(hour)
            if 5 <= h < 12:
                return 'Morning'
            elif 12 <= h < 18:
                return 'Afternoon'
            else:
                return 'Night'
        except:
            return 'Unknown'
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
        trend_labels=trend_labels,
        trend_values=trend_values,
        error=None,
        recent_cases=recent_cases,
        summary_stats=summary_stats
    )

@app.route('/hotspot', methods=['GET', 'POST'])
def hotspot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    df = load_data()
    if df is None or 'latitude' not in df.columns or 'longitude' not in df.columns:
        return render_template('hotspot.html', error='Could not load location data.', map_path=None, localities=[], selected_locality=None, criminals=[])
    df = df.dropna(subset=['latitude', 'longitude'])
    all_localities = sorted(df['locality'].dropna().unique())
    selected_locality = None
    if request.method == 'POST':
        selected_locality = request.form.get('locality')
    else:
        selected_locality = request.args.get('locality')
    filtered_df = df
    if selected_locality and selected_locality != 'All':
        filtered_df = df[df['locality'] == selected_locality]
    # Cluster filtered locations
    coords = filtered_df[['latitude', 'longitude']].values
    n_clusters = 3 if len(filtered_df) >= 3 else max(1, len(filtered_df))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    filtered_df['cluster'] = kmeans.fit_predict(coords) if len(filtered_df) > 0 else 0
    centers = kmeans.cluster_centers_ if len(filtered_df) > 0 else []
    # Always center on Rasayani, fit bounds to data if available
    rasayani_center = [18.8600, 73.1500]
    m = folium.Map(location=rasayani_center, zoom_start=14, max_bounds=True)
    if len(filtered_df) > 0:
        min_lat, max_lat = filtered_df['latitude'].min(), filtered_df['latitude'].max()
        min_lon, max_lon = filtered_df['longitude'].min(), filtered_df['longitude'].max()
        bounds = [[min_lat, min_lon], [max_lat, max_lon]]
        m.fit_bounds(bounds)
    # Optionally, add a marker for Rasayani center
    folium.Marker(
        location=rasayani_center,
        icon=folium.Icon(color='blue', icon='home'),
        popup='Rasayani City Center'
    ).add_to(m)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=4,
            color=colors[row['cluster'] % len(colors)] if len(filtered_df) > 0 else 'gray',
            fill=True,
            fill_opacity=0.7,
            popup=row.get('locality', '')
        ).add_to(m)
    # Mark cluster centers
    if len(filtered_df) > 0:
        for i, center in enumerate(centers):
            folium.Marker(
                location=center,
                icon=folium.Icon(color=colors[i % len(colors)], icon='star'),
                popup=f'Hotspot Center {i+1}'
            ).add_to(m)
    map_path = 'static/hotspot_map.html'
    m.save(map_path)
    # Prepare criminal table data
    criminals = filtered_df[['crime_description', 'crime_domain', 'weapon_used', 'victim_age', 'victim_gender', 'criminal_name', 'hour', 'locality']].to_dict(orient='records') if len(filtered_df) > 0 else []
    return render_template('hotspot.html', error=None, map_path=map_path, localities=all_localities, selected_locality=selected_locality, criminals=criminals)

@app.route('/fir/add', methods=['GET', 'POST'])
def add_fir():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    message = None
    if request.method == 'POST':
        # Get form data
        fields = [
            'Locality', 'Latitude', 'Longitude', 'Crime Description', 'Crime Domain',
            'Weapon Used', 'Hour', 'Victim Age', 'Victim Gender', 'Criminal Name'
        ]
        fir_data = {field: request.form.get(field, '').strip() for field in fields}
        # Basic validation
        required_fields = ['Locality', 'Latitude', 'Longitude', 'Crime Description', 'Crime Domain', 'Hour', 'Victim Age', 'Victim Gender']
        missing = [f for f in required_fields if not fir_data[f]]
        if missing:
            message = f"Missing required fields: {', '.join(missing)}"
        else:
            # Save to CSV
            import csv
            csv_path = os.path.join('data', 'rasayani_crime_dataset', 'rasayani_crime_dataset.csv')
            file_exists = os.path.isfile(csv_path)
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(fir_data)
            message = "FIR submitted successfully!"
    return render_template('add_fir.html', message=message)

@app.route('/fir/records')
def fir_records():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    import csv
    csv_path = os.path.join('data', 'rasayani_crime_dataset', 'rasayani_crime_dataset.csv')
    firs = []
    headers = []
    if os.path.isfile(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            for row in reader:
                firs.append(row)
    return render_template('fir_records.html', firs=firs, headers=headers)

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    df = load_data()
    if df is None:
        # Pass empty lists to avoid template errors
        return render_template(
            'analytics.html',
            top_types_labels=[], top_types_values=[],
            area_labels=[], area_values=[],
            gender_labels=[], gender_values=[],
            weapon_labels=[], weapon_values=[],
            hourly_labels=[], hourly_values=[],
            agegroup_labels=[], agegroup_values=[],
            domain_labels=[], domain_values=[],
            heatmap_coords=[],
            suspect_labels=[], suspect_values=[]
        )
    # Top crime types
    top_types = df['crime_description'].value_counts().head(10)
    top_types_labels = list(top_types.index)
    top_types_values = [int(x) for x in top_types.values]
    # Area-wise breakdown
    area_counts = df['locality'].value_counts().head(10)
    area_labels = list(area_counts.index)
    area_values = [int(x) for x in area_counts.values]
    # Victim gender (for pie chart)
    gender_counts = df['victim_gender'].value_counts()
    gender_labels = list(gender_counts.index)
    gender_values = [int(x) for x in gender_counts.values]
    # Weapon usage
    weapon_counts = df['weapon_used'].value_counts().head(10)
    weapon_labels = list(weapon_counts.index)
    weapon_values = [int(x) for x in weapon_counts.values]
    # Hourly crime distribution
    if 'hour' in df.columns:
        hourly = df['hour'].value_counts().sort_index()
        hourly_labels = [str(int(h)) for h in hourly.index]
        hourly_values = [int(x) for x in hourly.values]
    else:
        hourly_labels, hourly_values = [], []
    # Victim age group
    if 'victim_age' in df.columns:
        bins = [0, 18, 35, 60, 100]
        labels = ['0-18', '19-35', '36-60', '60+']
        df['age_group'] = pd.cut(df['victim_age'], bins=bins, labels=labels, right=False)
        agegroup_counts = df['age_group'].value_counts().sort_index()
        agegroup_labels = list(agegroup_counts.index.astype(str))
        agegroup_values = [int(x) for x in agegroup_counts.values]
    else:
        agegroup_labels, agegroup_values = [], []
    # Crime domain breakdown
    if 'crime_domain' in df.columns:
        domain_counts = df['crime_domain'].value_counts().head(10)
        domain_labels = list(domain_counts.index)
        domain_values = [int(x) for x in domain_counts.values]
    else:
        domain_labels, domain_values = [], []
    # Heatmap data (lat/lon)
    if 'latitude' in df.columns and 'longitude' in df.columns:
        heatmap_coords = df[['latitude', 'longitude']].dropna().values.tolist()
    else:
        heatmap_coords = []
    # Top suspects (by criminal name)
    if 'criminal_name' in df.columns:
        suspect_counts = df['criminal_name'].value_counts().head(10)
        suspect_labels = list(suspect_counts.index)
        suspect_values = [int(x) for x in suspect_counts.values]
    else:
        suspect_labels, suspect_values = [], []
    return render_template(
        'analytics.html',
        top_types_labels=top_types_labels,
        top_types_values=top_types_values,
        area_labels=area_labels,
        area_values=area_values,
        gender_labels=gender_labels,
        gender_values=gender_values,
        weapon_labels=weapon_labels,
        weapon_values=weapon_values,
        hourly_labels=hourly_labels,
        hourly_values=hourly_values,
        agegroup_labels=agegroup_labels,
        agegroup_values=agegroup_values,
        domain_labels=domain_labels,
        domain_values=domain_values,
        heatmap_coords=heatmap_coords,
        suspect_labels=suspect_labels,
        suspect_values=suspect_values
    )

@app.route('/ml-insights')
def ml_insights():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import os
    import base64
    from io import BytesIO
    from src.model import train_crime_type_model
    df = load_data()
    if df is None:
        return render_template('ml_insights.html', metrics=None, confusion=None, features=None, report_table=None, roc_img=None, report_csv=None, shap_img=None)
    # Train/test split and model
    model, X_test, y_test = train_crime_type_model(df)
    y_pred = model.predict(X_test)
    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    metrics = {
        'accuracy': report['accuracy'],
        'macro avg': report['macro avg'],
        'weighted avg': report['weighted avg']
    }
    # Full report as table
    report_table = []
    for label in model.classes_:
        row = report.get(str(label), report.get(label, {}))
        if row:
            report_table.append({
                'label': label,
                'precision': row.get('precision', 0),
                'recall': row.get('recall', 0),
                'f1': row.get('f1-score', 0),
                'support': row.get('support', 0)
            })
    # Save report as CSV
    static_dir = os.path.join('static', 'ml_insights')
    os.makedirs(static_dir, exist_ok=True)
    report_csv_path = os.path.join(static_dir, 'classification_report.csv')
    pd.DataFrame(report_table).to_csv(report_csv_path, index=False)
    report_csv = '/static/ml_insights/classification_report.csv'
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    confusion = {
        'labels': list(model.classes_),
        'matrix': cm.tolist()
    }
    confusion_rows = list(zip(confusion['matrix'], confusion['labels']))
    # Feature importance (for tree-based models)
    if hasattr(model, 'feature_importances_'):
        features = sorted(zip(X_test.columns, model.feature_importances_), key=lambda x: -x[1])
    else:
        features = []
    # ROC curve (multi-class, one-vs-rest)
    try:
        from sklearn.preprocessing import label_binarize
        y_test_bin = label_binarize(y_test, classes=model.classes_)
        y_pred_prob = model.predict_proba(X_test)
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i, label in enumerate(model.classes_):
            fpr[label], tpr[label], _ = roc_curve(y_test_bin[:, i], y_pred_prob[:, i])
            roc_auc[label] = auc(fpr[label], tpr[label])
        plt.figure(figsize=(7,5))
        for label in model.classes_:
            plt.plot(fpr[label], tpr[label], label=f"{label} (AUC={roc_auc[label]:.2f})")
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve (One-vs-Rest)')
        plt.legend()
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        roc_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        roc_img = None
    # SHAP summary plot (optional)
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        plt.figure(figsize=(8,5))
        shap.summary_plot(shap_values, X_test, show=False)
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        shap_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        shap_img = None
    return render_template('ml_insights.html', metrics=metrics, confusion=confusion, features=features, report_table=report_table, roc_img=roc_img, report_csv=report_csv, shap_img=shap_img, confusion_rows=confusion_rows)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 