import requests

def get_lat_long_from_postcode(postcode: str):
    url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}"
    
    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": "Invalid response from API"}
    
    data = response.json()
    
    if data["status"] != 200:
        return {"error": data.get("error", "Invalid postcode")}
    
    result = data["result"]
    
    return {
        "postcode": result["postcode"],
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "country": result["country"],
        "region": result["region"]
    }

