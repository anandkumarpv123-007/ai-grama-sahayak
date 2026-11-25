from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Name of public service institution / facility")
    service_type: str = Field(..., description="Type of service (e.g., hospital, phc, school, sachivalayam)")
    address: str = Field(..., description="Physical address of the facility")
    phone: Optional[str] = Field(default=None, description="Contact telephone or helpline")
    distance_km: Optional[float] = Field(default=None, description="Distance from requested location in km")
    source_url: Optional[str] = Field(default=None, description="Official portal or verified registry link")


class NearbyServicesResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    services: List[ServiceItem] = Field(
        default_factory=list,
        description="List of matching verified public service facilities",
    )
