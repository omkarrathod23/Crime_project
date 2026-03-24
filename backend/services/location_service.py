import math
from models.database import Department
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using Haversine formula.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
        
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def assign_nearest_police_station(lat, lon, city_name=None):
    """
    Automatically assigns an FIR to the nearest police station.
    Steps:
    1. Fetch all police stations from MongoDB
    2. Calculate distance from FIR location to each station
    3. Return the nearest station
    """
    logger.info(f"Finding nearest station for coordinates: ({lat}, {lon})")
    
    stations = Department.objects.all()
    if not stations:
        logger.warning("No police stations found in database.")
        return None

    nearest_station = None
    min_distance = float('inf')

    for station in stations:
        # Prioritize point coordinates if available
        s_lat = station.latitude
        s_lon = station.longitude
        
        # Fallback to center of boundaries if point is not set
        if s_lat is None or s_lon is None:
            if station.min_lat and station.max_lat and station.min_lon and station.max_lon:
                s_lat = (station.min_lat + station.max_lat) / 2
                s_lon = (station.min_lon + station.max_lon) / 2
        
        if s_lat is not None and s_lon is not None:
            distance = calculate_distance(lat, lon, s_lat, s_lon)
            logger.info(f"Distance to {station.name}: {distance:.2f} km")
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station

    if nearest_station:
        logger.info(f"Assigned to: {nearest_station.name} (Distance: {min_distance:.2f} km)")
        return {
            "station_id": nearest_station.id,
            "station_name": nearest_station.name,
            "district": nearest_station.district or "Unknown",
            "city": nearest_station.city or "Unknown"
        }
    
    # Fallback: Search by city name if coordinates didn't match any station within reasonable distance
    # or if coordinates were invalid
    if city_name:
        logger.info(f"Attempting fallback to city name mapping: {city_name}")
        station = Department.objects(city__iexact=city_name).first()
        if station:
            logger.info(f"Fallback assigned to: {station.name} via city mapping")
            return {
                "station_id": station.id,
                "station_name": station.name,
                "district": station.district or "Unknown",
                "city": station.city or "Unknown"
            }

    logger.warning("No suitable station found for assignment.")
    return None

def get_nearest_stations(lat, lon, limit=3):
    """
    Returns a list of the top N nearest police stations with their distances.
    """
    logger.info(f"Fetching {limit} nearest stations for ({lat}, {lon})")
    stations = Department.objects.all()
    results = []

    for station in stations:
        s_lat = station.latitude
        s_lon = station.longitude
        
        if s_lat is None or s_lon is None:
            if station.min_lat and station.max_lat and station.min_lon and station.max_lon:
                s_lat = (station.min_lat + station.max_lat) / 2
                s_lon = (station.min_lon + station.max_lon) / 2
        
        if s_lat is not None and s_lon is not None:
            dist = calculate_distance(lat, lon, s_lat, s_lon)
            results.append({
                "name": station.name,
                "distance": round(dist, 2),
                "city": station.city
            })

    # Sort by distance and return top N
    results.sort(key=lambda x: x['distance'])
    return results[:limit]
