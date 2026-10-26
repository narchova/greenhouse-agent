#!/usr/bin/env python3
"""Seed script for greenhouse plants in Firestore."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-2deba0eddfc5"

PLANTS = [
    {
        "id": "monstera-deliciosa",
        "name": "Monstera Deliciosa",
        "species": "Monstera deliciosa",
        "light": "Bright indirect",
        "watering_interval_days": 7,
        "care_level": "Easy",
        "price": 28.50,
        "stock": 14,
        "description": "Vibrant split-leaf philodendron, thrives in bright indirect sunlight.",
    },
    {
        "id": "snake-plant",
        "name": "Snake Plant",
        "species": "Sansevieria trifasciata",
        "light": "Low to bright",
        "watering_interval_days": 14,
        "care_level": "Beginner",
        "price": 18.00,
        "stock": 25,
        "description": "Hardy, drought-tolerant architectural succulent that purifies indoor air.",
    },
    {
        "id": "fiddle-leaf-fig",
        "name": "Fiddle Leaf Fig",
        "species": "Ficus lyrata",
        "light": "Bright filtered",
        "watering_interval_days": 7,
        "care_level": "Moderate",
        "price": 45.00,
        "stock": 8,
        "description": "Popular indoor tree with broad, violin-shaped glossy green leaves.",
    },
    {
        "id": "peace-lily",
        "name": "Peace Lily",
        "species": "Spathiphyllum wallisii",
        "light": "Medium to low",
        "watering_interval_days": 5,
        "care_level": "Easy",
        "price": 22.00,
        "stock": 18,
        "description": "Tropical plant with glossy leaves and elegant white flowering spathes.",
    },
    {
        "id": "pothos-golden",
        "name": "Golden Pothos",
        "species": "Epipremnum aureum",
        "light": "Low to medium indirect",
        "watering_interval_days": 8,
        "care_level": "Beginner",
        "price": 14.50,
        "stock": 30,
        "description": "Trailing vine with heart-shaped, variegated golden-green leaves.",
    },
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    plants_ref = db.collection("plants")
    print(f"Seeding plants into collection 'plants' on project {PROJECT_ID}...")
    for plant in PLANTS:
        doc_id = plant["id"]
        data = {k: v for k, v in plant.items() if k != "id"}
        plants_ref.document(doc_id).set(data)
        print(f"  ✓ Seeded {plant['name']} ({doc_id})")
    print("Done seeding Firestore!")

if __name__ == "__main__":
    seed()
