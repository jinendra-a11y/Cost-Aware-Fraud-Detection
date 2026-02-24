import requests
from dotenv import load_dotenv
import os

load_dotenv()
OPENROUTESERVICE_API = os.getenv("OPENROUTESERVICE_API")

def get_route_distance(
    pickup_lat: float,
    pickup_lng: float,
    drop_lat: float,
    drop_lng: float,
    profile: str = "driving-car"
) -> dict:
    """
    Get route distance and duration from OpenRouteService.

    Returns:
        {
            "distance_km": float,
            "duration_min": float,
            "route_points": int,
            "geometry": list
        }
    """

    url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"

    headers = {
        "Authorization": OPENROUTESERVICE_API
    }

    body = {
        "coordinates": [
            [pickup_lng, pickup_lat],   # NOTE: lng, lat order
            [drop_lng, drop_lat]
        ],
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        
        feature = data["features"][0]

        summary = feature["properties"]["summary"]

        distance_km = summary["distance"] / 1000
        duration_min = summary["duration"] / 60

        geometry = feature["geometry"]["coordinates"]

        return {
            "distance_km": round(distance_km, 2),
            "duration_min": round(duration_min, 2),
            "route_points": len(geometry),
            "geometry": geometry
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

    except (KeyError, IndexError, TypeError) as e:
        return {"error": f"Unexpected response format: {str(e)}"}
