import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
# from xgboost import XGBClassifier  # Uncomment if using XGBoost
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


class CrimePredictor:
    """
    Predicts crime type based on features using a classification model.
    """
    def __init__(self):
        self.model = RandomForestClassifier(random_state=42)

    def train(self, df):
        """Train the model on the dataset (stub)."""
        # TODO: Implement feature engineering and model training
        pass

    def predict(self, features):
        """Predict crime type for given features (stub)."""
        # TODO: Implement prediction logic
        pass

class HotspotDetector:
    """
    Detects crime hotspots using clustering (e.g., KMeans).
    """
    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=n_clusters, random_state=42)

    def fit(self, df):
        """Fit the clustering model to location data (stub)."""
        # TODO: Implement clustering on latitude/longitude
        pass

    def predict(self, locations):
        """Predict hotspot cluster for given locations (stub)."""
        # TODO: Implement cluster prediction
        pass

class TimeSeriesTrends:
    """
    Analyzes time-based trends in crime data.
    """
    def analyze(self, df):
        """Analyze time trends (stub)."""
        # TODO: Implement time series analysis
        pass

def preprocess_features(df):
    """
    Prepare features for modeling: encode categorical, extract time features, etc.
    """
    df = df.copy()
    # Example: extract hour, day, etc.
    if 'hour' in df.columns:
        df['hour'] = df['hour'].astype(int)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['dayofweek'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
    # Encode categorical features
    for col in ['locality', 'crime_domain', 'weapon_used', 'victim_gender']:
        if col in df.columns:
            df[col] = df[col].astype('category').cat.codes
    # Drop columns not used for prediction
    drop_cols = ['crime_description', 'criminal_name', 'date']
    X = df.drop([c for c in drop_cols if c in df.columns], axis=1)
    return X

def train_crime_type_model(df, model_type='rf', save_path=None):
    """
    Train a model to predict crime type. Returns trained model and test set.
    """
    X = preprocess_features(df)
    y = df['crime_description']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    if model_type == 'rf':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    # elif model_type == 'xgb':
    #     model = XGBClassifier(random_state=42)
    else:
        raise ValueError("Unsupported model type")
    model.fit(X_train, y_train)
    if save_path:
        joblib.dump(model, save_path)
        logging.info(f"Model saved to {save_path}")
    return model, X_test, y_test

def test_crime_type_model(model, X_test, y_test):
    """
    Output classification report and accuracy for the model.
    """
    y_pred = model.predict(X_test)
    print("\n--- Classification Report ---")
    print(classification_report(y_test, y_pred))
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")

if __name__ == "__main__":
    from data_loader import load_crime_data
    df = load_crime_data()
    model, X_test, y_test = train_crime_type_model(df, save_path=os.path.join(MODEL_DIR, 'crime_type_rf.joblib'))
    test_crime_type_model(model, X_test, y_test) 