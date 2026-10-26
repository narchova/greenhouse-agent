"""Tool to fetch botanical taxonomic and species data from GBIF (Global Biodiversity Information Facility)."""
import os
import json
import urllib.parse
import urllib.request
from typing import Any, Dict


def lookup_species_taxonomy(plant_scientific_or_common_name: str) -> Dict[str, Any]:
    """Look up botanical taxonomy and scientific classification for a plant species using the free GBIF API.

    Args:
        plant_scientific_or_common_name: Scientific or common plant name (e.g. 'Monstera deliciosa', 'Sansevieria', 'Ficus lyrata').

    Returns:
        A dictionary containing scientific name, family, order, genus, kingdom, confidence score, and match status.
    """
    api_base = os.environ.get("GBIF_API_URL", "https://api.gbif.org/v1/species/match")
    encoded_name = urllib.parse.quote_plus(plant_scientific_or_common_name)
    url = f"{api_base}?name={encoded_name}&verbose=false"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "GreenhouseAgent/1.0", "Accept": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "query": plant_scientific_or_common_name,
                "status": "success",
                "matched_name": data.get("scientificName", data.get("canonicalName", "Unknown")),
                "rank": data.get("rank", "Unknown"),
                "family": data.get("family", "Unknown"),
                "genus": data.get("genus", "Unknown"),
                "order": data.get("order", "Unknown"),
                "kingdom": data.get("kingdom", "Plantae"),
                "confidence": data.get("confidence", 0),
                "match_type": data.get("matchType", "NONE"),
            }
    except Exception as e:
        return {
            "query": plant_scientific_or_common_name,
            "status": "error",
            "message": f"Failed to retrieve species data from GBIF: {str(e)}"
        }
