"""Google Maps Platform tools: Geocoding and Places API (New)."""
import os
import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


def _get_api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not key or key == "PASTE_KEY_HERE":
        raise ValueError(
            "GOOGLE_MAPS_API_KEY environment variable is not set or contains placeholder. "
            "Please add your valid Google Maps API key to .env."
        )
    return key


def geocode_address(address: str) -> Dict[str, Any]:
    """Turn a street address, city, or landmark into geographic coordinates (latitude, longitude).

    Args:
        address: The address or place to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        Dictionary with formatted address, latitude, and longitude.
    """
    try:
        api_key = _get_api_key()
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    encoded_address = urllib.parse.quote_plus(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return {
                    "status": "error",
                    "message": f"Geocoding failed: {data.get('status', 'NO_RESULTS')}",
                    "error_message": data.get("error_message", "")
                }
            result = data["results"][0]
            loc = result.get("geometry", {}).get("location", {})
            return {
                "status": "success",
                "formatted_address": result.get("formatted_address"),
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
                "place_id": result.get("place_id"),
            }
    except Exception as e:
        return {"status": "error", "message": f"HTTP request failed: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "florist",
    radius_meters: float = 5000.0,
    max_results: int = 5,
) -> Dict[str, Any]:
    """Find nearby places (e.g., florist, greenhouse, plant nursery, park) using the Places API (New).

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        place_type: Primary place type to search for (e.g. 'florist', 'park', 'store').
        radius_meters: Search radius in meters (default 5000.0, max 50000.0).
        max_results: Maximum number of places to return (default 5).

    Returns:
        Dictionary with a list of matching places (name, formatted_address, location).
    """
    try:
        api_key = _get_api_key()
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": min(max_results, 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": float(radius_meters),
            }
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            raw_places = data.get("places", [])
            places = []
            for p in raw_places:
                loc = p.get("location", {})
                places.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress", "No address provided"),
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                    "types": p.get("types", []),
                })
            return {
                "status": "success",
                "count": len(places),
                "places": places,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return {"status": "error", "code": e.code, "message": f"Places API HTTP error: {e.reason} - {err_body}"}
    except Exception as e:
        return {"status": "error", "message": f"HTTP request failed: {str(e)}"}
