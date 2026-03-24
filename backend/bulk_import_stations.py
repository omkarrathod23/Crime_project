import csv
import argparse
from app import app
from models.database import Department
import os

def import_from_csv(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with app.app_context():
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    # Required fields: name, city, latitude, longitude
                    name = row.get('name')
                    city = row.get('city')
                    district = row.get('district', 'Unknown')
                    lat = float(row.get('latitude'))
                    lon = float(row.get('longitude'))
                    
                    if not name or not city:
                        continue

                    existing = Department.objects(name=name).first()
                    if not existing:
                        dept = Department(
                            name=name,
                            city=city,
                            district=district,
                            latitude=lat,
                            longitude=lon,
                            state="Maharashtra"
                        )
                        dept.save()
                        count += 1
                    else:
                        print(f"Skipping {name} (already exists).")
                except Exception as e:
                    print(f"Error importing row {row}: {e}")
            
            print(f"Successfully imported {count} new police stations.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk import police stations from CSV.")
    parser.add_argument("file", help="Path to the CSV file.")
    args = parser.parse_args()
    import_from_csv(args.file)
