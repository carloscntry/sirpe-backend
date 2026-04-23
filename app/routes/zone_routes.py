from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.zone import Zone
from app.schemas.zone import ZoneCreate, ZoneResponse

router = APIRouter(prefix="/zonas", tags=["Zonas"])

@router.post("/", response_model=ZoneResponse)
def crear_zona(zone: ZoneCreate, db: Session = Depends(get_db)):
    nueva_zona = Zone(
        nombre=zone.nombre,
        tipo=zone.tipo,
        nivel_riesgo=zone.nivel_riesgo,
        latitud=zone.latitud,
        longitud=zone.longitud,
        geometry_geojson=zone.geometry_geojson
    )
    db.add(nueva_zona)
    db.commit()
    db.refresh(nueva_zona)
    return nueva_zona

@router.get("/", response_model=list[ZoneResponse])
def listar_zonas(db: Session = Depends(get_db)):
    return db.query(Zone).all()