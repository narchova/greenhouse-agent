"""Firestore tools for greenhouse plants catalog and inventory."""
from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-2deba0eddfc5"


def _get_db() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def list_plants(limit: int = 10) -> List[Dict[str, Any]]:
    """List available plants in the greenhouse catalog.

    Args:
        limit: Maximum number of plants to return (default 10).

    Returns:
        A list of plant dictionaries containing id, name, species, light, watering_interval_days, care_level, price, stock, and description.
    """
    db = _get_db()
    docs = db.collection("plants").limit(limit).stream()
    results = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        results.append(item)
    return results


def search_plants_by_light(light_query: str) -> List[Dict[str, Any]]:
    """Search plants matching light conditions (e.g., 'low', 'bright', 'indirect').

    Args:
        light_query: Keyword describing the light environment (e.g. 'low', 'bright', 'indirect').

    Returns:
        List of matching plant records.
    """
    db = _get_db()
    docs = db.collection("plants").stream()
    matches = []
    query_lower = light_query.lower()
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if query_lower in data.get("light", "").lower() or query_lower in data.get("care_level", "").lower():
            matches.append(data)
    return matches


def get_plant_details(name_or_id: str) -> Optional[Dict[str, Any]]:
    """Get full details for a specific plant by ID or name.

    Args:
        name_or_id: The ID or name of the plant (e.g., 'snake-plant' or 'Snake Plant').

    Returns:
        Plant details dict if found, or None.
    """
    db = _get_db()
    # Direct doc lookup
    doc_ref = db.collection("plants").document(name_or_id.lower().replace(" ", "-"))
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    # Search by name match
    query_lower = name_or_id.lower()
    for d in db.collection("plants").stream():
        data = d.to_dict()
        if data.get("name", "").lower() == query_lower or query_lower in d.id:
            data["id"] = d.id
            return data
    return None


def add_plant(
    name: str,
    species: str,
    light: str,
    watering_interval_days: int,
    care_level: str,
    price: float,
    stock: int,
    description: str,
) -> Dict[str, Any]:
    """Add a new plant to the greenhouse collection.

    Args:
        name: Common name of the plant (e.g. 'ZZ Plant').
        species: Botanical name (e.g. 'Zamioculcas zamiifolia').
        light: Light requirements (e.g. 'Low to bright indirect').
        watering_interval_days: Recommended days between watering.
        care_level: Care difficulty (e.g. 'Beginner', 'Easy', 'Moderate', 'Expert').
        price: Price in dollars.
        stock: Available quantity in inventory.
        description: A short description and care summary.

    Returns:
        Dictionary confirming the created plant with its ID.
    """
    db = _get_db()
    doc_id = name.lower().replace(" ", "-")
    data = {
        "name": name,
        "species": species,
        "light": light,
        "watering_interval_days": watering_interval_days,
        "care_level": care_level,
        "price": price,
        "stock": stock,
        "description": description,
    }
    db.collection("plants").document(doc_id).set(data)
    data["id"] = doc_id
    return {"status": "success", "message": f"Added {name} to greenhouse catalog", "plant": data}


def log_plant_watering(plant_id: str, notes: str = "") -> Dict[str, Any]:
    """Log that a plant was watered today and compute its next watering date.

    Args:
        plant_id: The ID or name of the plant (e.g., 'monstera-deliciosa' or 'snake-plant').
        notes: Optional care notes (e.g., 'misted leaves', 'added liquid fertilizer').

    Returns:
        Confirmation dictionary with the recorded date and scheduled next watering date.
    """
    import datetime
    plant = get_plant_details(plant_id)
    if not plant:
        return {"status": "error", "message": f"Plant '{plant_id}' not found in catalog."}

    actual_id = plant.get("id", plant_id)
    interval = plant.get("watering_interval_days", 7)
    today = datetime.date.today()
    next_date = today + datetime.timedelta(days=interval)

    log_entry = {
        "plant_id": actual_id,
        "plant_name": plant.get("name", actual_id),
        "watered_date": today.isoformat(),
        "next_watering_date": next_date.isoformat(),
        "notes": notes,
    }

    db = _get_db()
    db.collection("care_logs").add(log_entry)

    return {
        "status": "success",
        "plant_name": plant.get("name"),
        "watered_date": today.isoformat(),
        "next_watering_date": next_date.isoformat(),
        "watering_interval_days": interval,
        "notes": notes,
        "message": f"Recorded watering for {plant.get('name')}. Next watering due on {next_date.isoformat()}."
    }
