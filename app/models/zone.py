from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base

class Zone(Base):
    __tablename__ = "zonas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    nivel_riesgo = Column(String, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    geometry_geojson = Column(Text, nullable=True)