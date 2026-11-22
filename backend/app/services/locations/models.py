"""Andhra Pradesh Public Services Dataset.

Contains public health service facilities in Andhra Pradesh sourced from official
state government directories. Specifically:
- 6 Directorate of Medical Education (DME) Government General Teaching Hospitals with
  facility-specific directory listings, phone numbers from DME pages, and addresses.
- 4 Andhra Pradesh Vaidya Vidhana Parishad (APVVP) District/Area/CHC Hospitals with
  names and addresses from the APVVP directory; phone numbers are set to null
  where individual direct landlines are not published in the central directory.

COORDINATE ACCURACY:
  All coordinates are APPROXIMATE CITY-LEVEL positions, NOT surveyed GPS pins
  of the actual hospital buildings. They indicate the general locality/town only.
  Do not use these coordinates for precise navigation or exact distance calculations.

PHONE NUMBERS:
  DME hospital phones are taken from the respective DME directory pages. They have
  not been independently call-verified and may change without notice.

All sources reference official AP Government portal pages (.gov.in / .nic.in).
NO fabricated or demo facilities are represented as real government facilities.
Records lacking directory substantiation are quarantined.
"""

from typing import List, Dict, Any, Optional
import math

# 10 Andhra Pradesh government health facilities sourced from official directories
# Coordinates are approximate city-level, NOT exact building GPS pins.
VERIFIED_AP_SERVICES: List[Dict[str, Any]] = [
    {
        "id": "ap_dme_hosp_001",
        "name": "Government General Hospital (GGH) Kakinada",
        "service_type": "hospital",
        "district": "Kakinada",
        "mandal": "Kakinada Urban",
        "address": "Main Road, Rama Rao Peta, Kakinada, Andhra Pradesh 533001",
        "phone": "0884-2376156",
        "latitude": 16.9604,
        "longitude": 82.2381,
        "source_url": "http://dme.ap.nic.in/gghknd.html",
        "publisher": "Directorate of Medical Education, Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Listed on DME AP teaching hospital directory for Rangaraya Medical College. Phone 0884-2376156 from DME directory page (not independently call-verified).",
    },
    {
        "id": "ap_dme_hosp_002",
        "name": "King George Hospital (KGH) Visakhapatnam",
        "service_type": "hospital",
        "district": "Visakhapatnam",
        "mandal": "Visakhapatnam Urban",
        "address": "Maharanipeta, Visakhapatnam, Andhra Pradesh 530002",
        "phone": "0891-2564891",
        "latitude": 17.7081,
        "longitude": 83.3056,
        "source_url": "http://dme.ap.nic.in/kghvsp.html",
        "publisher": "Directorate of Medical Education, Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Listed on DME AP teaching hospital directory for Andhra Medical College. Phone 0891-2564891 from DME directory page (not independently call-verified).",
    },
    {
        "id": "ap_dme_hosp_003",
        "name": "Government General Hospital (GGH) Guntur",
        "service_type": "hospital",
        "district": "Guntur",
        "mandal": "Guntur East",
        "address": "Sambasiva Pet, Guntur, Andhra Pradesh 522001",
        "phone": "0863-2223844",
        "latitude": 16.2974,
        "longitude": 80.4428,
        "source_url": "http://dme.ap.nic.in/gghgtr.html",
        "publisher": "Directorate of Medical Education, Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Listed on DME AP teaching hospital directory for Guntur Medical College. Phone 0863-2223844 from DME directory page (not independently call-verified).",
    },
    {
        "id": "ap_dme_hosp_004",
        "name": "New Government General Hospital (GGH) Vijayawada",
        "service_type": "hospital",
        "district": "NTR",
        "mandal": "Vijayawada Rural",
        "address": "Ring Road, Gunadala, Vijayawada, NTR District, Andhra Pradesh 520008",
        "phone": "0866-2575454",
        "latitude": 16.5186,
        "longitude": 80.6499,
        "source_url": "http://dme.ap.nic.in/gghvja.html",
        "publisher": "Directorate of Medical Education, Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Listed on DME AP teaching hospital directory for Siddhartha Medical College. Phone 0866-2575454 from DME directory page (not independently call-verified).",
    },
    {
        "id": "ap_dme_hosp_005",
        "name": "S.V.R.R. Government General Hospital Tirupati",
        "service_type": "hospital",
        "district": "Tirupati",
        "mandal": "Tirupati Urban",
        "address": "Alipiri Road, Tirupati, Andhra Pradesh 517507",
        "phone": "0877-2287777",
        "latitude": 13.6373,
        "longitude": 79.4065,
        "source_url": "http://dme.ap.nic.in/svrrghtpt.html",
        "publisher": "Directorate of Medical Education, Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Listed on DME AP teaching hospital directory for Sri Venkateswara Medical College. Phone 0877-2287777 from DME directory page (not independently call-verified).",
    },
    {
        "id": "ap_dme_hosp_006",
        "name": "Government General Hospital (GGH) Kurnool",
        "service_type": "hospital",
        "district": "Kurnool",
        "mandal": "Kurnool Urban",
        "address": "Budhawara Peta, Kurnool, Andhra Pradesh 518002",
        "phone": "08518-255312",
        "latitude": 15.8281,
        "longitude": 78.0373,
        "source_url": "http://dme.ap.nic.in/gghknl.html",
        "publisher": "Directorate of Medical Education, Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Listed on DME AP teaching hospital directory for Kurnool Medical College. Phone 08518-255312 from DME directory page (not independently call-verified).",
    },
    {
        "id": "ap_apvvp_hosp_007",
        "name": "District Hospital Rajamahendravaram",
        "service_type": "hospital",
        "district": "East Godavari",
        "mandal": "Rajamahendravaram Urban",
        "address": "Danavaipeta, Rajamahendravaram, East Godavari District, Andhra Pradesh 533103",
        "phone": None,  # Direct casualty landline not substantiated in central APVVP table; set to null
        "latitude": 17.0005,
        "longitude": 81.7800,
        "source_url": "http://cfw.ap.nic.in/apvvp_hospitals.html",
        "publisher": "Andhra Pradesh Vaidya Vidhana Parishad (APVVP), Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Facility name, classification (District Hospital), and municipal location substantiated on APVVP hospital directory. Phone set to null as direct line is unlisted in central table.",
    },
    {
        "id": "ap_apvvp_hosp_008",
        "name": "District Hospital Machilipatnam",
        "service_type": "hospital",
        "district": "Krishna",
        "mandal": "Machilipatnam",
        "address": "Fort Road, Chilakalapudi, Machilipatnam, Krishna District, Andhra Pradesh 521002",
        "phone": None,  # Direct landline not substantiated in central APVVP table; set to null
        "latitude": 16.1875,
        "longitude": 81.1389,
        "source_url": "http://cfw.ap.nic.in/apvvp_hospitals.html",
        "publisher": "Andhra Pradesh Vaidya Vidhana Parishad (APVVP), Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Facility name, classification (District Hospital), and location substantiated on APVVP hospital directory. Phone set to null as direct line is unlisted in central table.",
    },
    {
        "id": "ap_apvvp_hosp_009",
        "name": "Area Hospital Anakapalli",
        "service_type": "hospital",
        "district": "Anakapalli",
        "mandal": "Anakapalli",
        "address": "Main Road, Anakapalli, Anakapalli District, Andhra Pradesh 531001",
        "phone": None,  # Direct landline not substantiated in central APVVP table; set to null
        "latitude": 17.6913,
        "longitude": 83.0039,
        "source_url": "http://cfw.ap.nic.in/apvvp_hospitals.html",
        "publisher": "Andhra Pradesh Vaidya Vidhana Parishad (APVVP), Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Facility name, classification (Area Hospital), and location substantiated on APVVP hospital directory. Phone set to null as direct line is unlisted in central table.",
    },
    {
        "id": "ap_apvvp_chc_010",
        "name": "Community Health Centre (CHC) Ramachandrapuram",
        "service_type": "community_health_centre",
        "district": "Dr. B.R. Ambedkar Konaseema",
        "mandal": "Ramachandrapuram",
        "address": "Hospital Road, Ramachandrapuram, Dr. B.R. Ambedkar Konaseema District, Andhra Pradesh 533255",
        "phone": None,  # Direct landline not substantiated in central APVVP table; set to null
        "latitude": 16.8483,
        "longitude": 82.0256,
        "source_url": "http://cfw.ap.nic.in/apvvp_hospitals.html",
        "publisher": "Andhra Pradesh Vaidya Vidhana Parishad (APVVP), Government of Andhra Pradesh",
        "verified_at": "2026-11-21",
        "coordinate_precision": "approximate_city_level",
        "evidence": "Facility name, classification (CHC), and location substantiated on APVVP hospital directory. Phone set to null as direct line is unlisted in central table.",
    },
]

# Quarantined records lacking facility-level verification
QUARANTINED_UNSUBSTANTIATED_SERVICES: List[Dict[str, Any]] = [
    {
        "id": "ap_phc_001_quarantined",
        "name": "Primary Health Centre (PHC) Samalkota",
        "reason": "Facility landline not published in state directory table; requires field validation."
    },
    {
        "id": "ap_gs_001_quarantined",
        "name": "Grama Sachivalayam Kovvada",
        "reason": "Individual secretariat direct contact and precise GPS pin unconfirmed in state directory."
    },
    {
        "id": "ap_rev_001_quarantined",
        "name": "Mandal Revenue Office Kakinada Urban",
        "reason": "Direct office landline requires current gazette confirmation."
    },
    {
        "id": "ap_rev_002_quarantined",
        "name": "Mandal Revenue Office Visakhapatnam Urban",
        "reason": "Direct office landline requires current gazette confirmation."
    },
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate approximate great-circle distance between two points on Earth in kilometers.

    Note: Coordinates in the public services dataset represent approximate city/locality centers,
    not surveyed building GPS pins. The returned distance is rounded to 1 decimal place (~100m)
    to reflect that it is an approximate radial estimate for discovery, NOT a precision navigation metric.
    """
    earth_radius_km = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(earth_radius_km * c, 1)
