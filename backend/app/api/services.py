"""API Router for Nearby Government Services.

Endpoint:
GET /api/services/nearby (when mounted under /api)

Prefix: /services

Query parameters:
- service_type: Optional[str]
- district: Optional[str]
- latitude: Optional[float]
- longitude: Optional[float]
- radius_km: Optional[float] (default 50.0 km)

Responses strictly follow the frozen API contracts in docs/api_contracts.md.
"""

from typing import Optional, List, Dict, Any
import math
import logging

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse
from app.schemas.services import NearbyServicesResponse, ServiceItem

from app.services.locations.service_finder import find_nearby_services

logger = logging.getLogger(__name__)

# Router prefix is "/services"; when Member 1 mounts under prefix="/api",
# the final endpoint path is exactly GET /api/services/nearby
router = APIRouter(prefix="/services", tags=["services"])


def _make_error_response(code: str, message: str, status_code: int = 400, details: Optional[List[Any]] = None) -> JSONResponse:
    """Format an error response following the shared API contract."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            }
        },
    )


@router.get("/nearby", response_model=NearbyServicesResponse)
def get_nearby_services(
    service_type: Optional[str] = Query(None, description="Type of public service, e.g. 'hospital', 'community_health_centre'"),
    district: Optional[str] = Query(None, description="Andhra Pradesh district name"),
    latitude: Optional[float] = Query(None, description="Latitude in decimal degrees"),
    longitude: Optional[float] = Query(None, description="Longitude in decimal degrees"),
    radius_km: Optional[float] = Query(50.0, description="Search radius in kilometers when coordinates are provided"),
):
    """Find verified nearby government public services in Andhra Pradesh.

    Supports search by district name or by geographic coordinates (latitude + longitude).
    Returns substantiated government hospitals and community health centres.

    Note on location accuracy:
    Facility coordinates are approximate city/locality-level centers, not exact building
    GPS pins. Calculated distance_km represents an approximate radial estimate for discovery,
    not exact road distances or navigation directions.

    Never invents or fabricates locations. Returns empty services list if no verified match.
    """
    has_lat = latitude is not None
    has_lon = longitude is not None

    # Validate coordinate coupling: both must be present together
    if has_lat != has_lon:
        return _make_error_response(
            code="VALIDATION_ERROR",
            message="Both latitude and longitude must be supplied together when using coordinate search.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate that at least one search dimension is provided
    if not district and not has_lat:
        return _make_error_response(
            code="VALIDATION_ERROR",
            message="Either district or both latitude and longitude coordinates must be specified.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Validate radius_km: must be positive and finite
    if radius_km is not None:
        if not isinstance(radius_km, (int, float)) or not math.isfinite(radius_km) or radius_km <= 0:
            return _make_error_response(
                code="VALIDATION_ERROR",
                message="radius_km must be a positive, finite number.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    # Validate coordinate finite values and ranges
    if has_lat and has_lon:
        if not isinstance(latitude, (int, float)) or not math.isfinite(latitude):
            return _make_error_response(
                code="VALIDATION_ERROR",
                message="Latitude must be a finite numerical value.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(longitude, (int, float)) or not math.isfinite(longitude):
            return _make_error_response(
                code="VALIDATION_ERROR",
                message="Longitude must be a finite numerical value.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            return _make_error_response(
                code="VALIDATION_ERROR",
                message="Latitude must be between -90 and 90, and longitude between -180 and 180 degrees.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    try:
        services = find_nearby_services(
            service_type=service_type,
            district=district,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )
        return {"services": services}
    except ValueError as e:
        return _make_error_response(
            code="VALIDATION_ERROR",
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        # Server-side logging of unexpected errors, returning generic public message
        logger.exception("Unexpected error occurred while querying nearby services")
        return _make_error_response(
            code="SERVER_ERROR",
            message="An unexpected server error occurred while retrieving nearby services.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
