import pandas as pd
import numpy as np
import joblib

def preprocess_input(features, data):
    X = data.head(1).copy()
    X['locality'] = features['locality']
    X['hour'] = int(features['hour'])
    for col in ['crime_domain', 'weapon_used', 'victim_gender']:
        if col in X.columns:
            X[col] = data[col].mode()[0]
    if 'victim_age' in X.columns:
        X['victim_age'] = data['victim_age'].median()
    if 'latitude' in X.columns:
        X['latitude'] = data['latitude'].mean()
    if 'longitude' in X.columns:
        X['longitude'] = data['longitude'].mean()
    for col in ['locality', 'crime_domain', 'weapon_used', 'victim_gender']:
        if col in X.columns:
            X[col] = X[col].astype('category').cat.codes
    drop_cols = ['crime_description', 'criminal_name', 'date']
    X = X.drop([c for c in drop_cols if c in X.columns], axis=1)
    return X

def predict_crime_type(model, features, data):
    X = preprocess_input(features, data)
    return model.predict(X)[0]

def get_feature_importance(model):
    """Returns global feature importance for the Random Forest model."""
    if hasattr(model, 'feature_importances_'):
        # Features consistent with preprocess_input logic
        feature_names = ['locality', 'hour', 'crime_domain', 'weapon_used', 
                        'victim_gender', 'victim_age', 'latitude', 'longitude']
        importances = model.feature_importances_
        # Filter to features that actually exist in importances array length
        feat_dict = {feature_names[i]: float(importances[i]) for i in range(min(len(feature_names), len(importances)))}
        return dict(sorted(feat_dict.items(), key=lambda item: item[1], reverse=True))
    return {}

def explain_prediction(features, data, prediction):
    """Generates a human-readable explanation for a specific prediction."""
    locality = features['locality']
    hour = int(features['hour'])
    
    # Filter data for this locality
    loc_data = data[data['locality'] == locality]
    total_loc_crimes = len(loc_data)
    
    if total_loc_crimes == 0:
        return f"Prediction based on global patterns (No prior records for {locality})."
    
    # Check frequency of predicted crime in this locality
    type_loc_data = loc_data[loc_data['crime_description'] == prediction]
    type_count = len(type_loc_data)
    type_freq = type_count / total_loc_crimes
    
    # Check if this hour is a 'high risk' hour for this crime in this locality
    hour_loc_data = type_loc_data[type_loc_data['hour'] == hour]
    hour_risk = len(hour_loc_data) > 0
    
    explanation = f"This prediction for **{prediction}** is primarily driven by historical incidents in **{locality}**."
    
    if type_freq > 0.3:
        explanation += f" Statistically, {prediction} is the most frequent crime in this area, accounting for {type_freq:.1%} of cases."
    elif type_freq > 0:
        explanation += f" Historical data shows that {prediction} occurs in this area, representing {type_freq:.1%} of local crime."
        
    if hour_risk:
        explanation += f" The time of day ({hour}:00) matches the period when such activities have been most frequently recorded in this specific locality."
    else:
        explanation += " Although this specific hour is less common for such incidents, the locality's historical density remains a strong indicator."
        
    return explanation