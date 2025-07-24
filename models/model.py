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