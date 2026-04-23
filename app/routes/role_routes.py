from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.post("/", response_model=RoleResponse)
def crear_rol(role: RoleCreate, db: Session = Depends(get_db)):
    nuevo_rol = Role(nombre=role.nombre, descripcion=role.descripcion)
    db.add(nuevo_rol)
    db.commit()
    db.refresh(nuevo_rol)
    return nuevo_rol

@router.get("/", response_model=list[RoleResponse])
def listar_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()