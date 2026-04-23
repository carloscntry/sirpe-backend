from pydantic import BaseModel
from typing import Optional

class ZoneCreate(BaseModel):
    nombre: str
    tipo: str
    nivel_riesgo: str
    latitud: float
    longitud: float
    geometry_geojson: Optional[str] = None

class ZoneResponse(BaseModel):
    id: int
    nombre: str
    tipo: str
    nivel_riesgo: str
    latitud: float
    longitud: float
    geometry_geojson: Optional[str] = None

    class Config:
        from_attributes = True