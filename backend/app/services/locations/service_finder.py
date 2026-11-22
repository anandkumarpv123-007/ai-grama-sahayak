"""Service Finder for Nearby Government Services.

Implements query filtering by district, coordinates (with approximate Haversine radial distance),
and service_type over substantiated Andhra Pradesh public facilities.
Strictly returns honest results: never fabricates records, addresses, or phone numbers.

IMPORTANT NOTE ON LOCATION PRECISION:
Facility coordinates in this dataset are approximate city/locality-level centers,
NOT surveyed GPS pins of individual buildings. Distances are approximate radial estimates
for discovery/sorting, not exact road distances or navigation directions.
"""

from typing import List, Dict, Any, Optional
import math
from .models import VERIFIED_AP_SERVICES, haversine_distance_km


def find_nearby_services(
    service_type: Optional[str] = None,
    district: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 50.0,
) -> List[Dict[str, Any]]:
    """Find verified public services in Andhra Pradesh matching the query criteria.

    Parameters:
        service_type: Type of service (e.g. 'hospital', 'community_health_centre').
        district: Name of Andhra Pradesh district (case-insensitive).
        latitude: Latitude in decimal degrees [-90, 90].
        longitude: Longitude in decimal degrees [-180, 180].
        radius_km: Maximum search radius in kilometers when coordinates are provided (must be positive & finite).

    Returns:
        List of verified service dictionaries matching the API contract:
        [
            {
                "name": str,
                "service_type": str,
                "address": str,
                "phone": Optional[str],
                "distance_km": Optional[float],
                "source_url": Optional[str]
            }
        ]
    """
    has_lat = latitude is not None
    has_lon = longitude is not None

    if has_lat != has_lon:
        raise ValueError("Both latitude and longitude must be provided together.")

    if not district and not has_lat:
        raise ValueError("Either district or both latitude and longitude coordinates must be specified.")

    if radius_km is not None:
        if not isinstance(radius_km, (int, float)) or not math.isfinite(radius_km) or radius_km <= 0:
            raise ValueError("radius_km must be a positive, finite number.")

    if has_lat and has_lon:
        if not isinstance(latitude, (int, float)) or not math.isfinite(latitude):
            raise ValueError("Latitude must be a finite numerical value.")
        if not isinstance(longitude, (int, float)) or not math.isfinite(longitude):
            raise ValueError("Longitude must be a finite numerical value.")
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError("Longitude must be between -180 and 180 degrees.")

    cleaned_service_type = service_type.strip().lower() if service_type else None
    cleaned_district = district.strip().lower() if district else None

    results: List[Dict[str, Any]] = []

    for item in VERIFIED_AP_SERVICES:
        # Filter by service_type if provided
        if cleaned_service_type:
            item_type = item["service_type"].lower()
            if cleaned_service_type != item_type:
                # Also allow 'healthcare' alias to match hospital and community health centres
                if cleaned_service_type == "healthcare" and item_type in [
                    "hospital",
                    "community_health_centre",
                ]:
                    pass
                else:
                    continue

        # Filter by district if provided
        if cleaned_district:
            item_district = item["district"].lower()
            if cleaned_district != item_district and cleaned_district not in item_district:
                continue

        # Calculate distance if coordinates provided
        dist_km: Optional[float] = None
        if has_lat and has_lon:
            dist_km = haversine_distance_km(
                float(latitude), float(longitude), item["latitude"], item["longitude"]
            )
            if radius_km is not None and dist_km > radius_km:
                continue

        results.append(
            {
                "name": item["name"],
                "service_type": item["service_type"],
                "address": item["address"],
                "phone": item.get("phone"),
                "distance_km": dist_km,
                "source_url": item.get("source_url"),
            }
        )

    # Sort by distance if coordinates were provided
    if has_lat and has_lon:
        results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else float("inf")))

    return results
