# Crime Management System

A modular Python project for crime data analysis, prediction, and management using the Rasayani dataset.

## Features
- Data loading and cleaning
- Exploratory Data Analysis (EDA)
- Crime prediction and hotspot detection
- CLI dashboard for interaction

## Project Structure
```
crime-management-system/
│
├── data/
│   └── rasayani_crime_dataset.csv
│
├── src/
│   ├── data_loader.py        # Load and clean dataset
│   ├── eda.py                # Exploratory analysis
│   ├── model.py              # ML models for prediction
│   ├── dashboard.py          # Terminal UI or simple CLI
│   └── utils.py              # Common helpers
│
├── main.py                   # Entry point CLI
├── requirements.txt
└── README.md
```

## Setup
1. Clone the repo and navigate to the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run modules as needed:
   ```bash
   python src/data_loader.py
   python src/eda.py
   # etc.
   ```

## Data
- Place your CSV files in the `data/` directory.
- Default dataset: `rasayani_crime_dataset.csv` 