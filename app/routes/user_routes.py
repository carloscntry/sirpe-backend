from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.core.security import hash_password, verify_password

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=UserResponse)
def crear_usuario(user: UserCreate, db: Session = Depends(get_db)):
    nuevo_usuario = User(
        nombre=user.nombre,
        correo=user.correo,
        password_hash=hash_password(user.password),
        rol_id=user.rol_id,
        activo=True
    )

    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="El correo ya existe o el rol_id no es valido"
        )

@router.get("/", response_model=list[UserResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.correo == user.correo).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if not verify_password(user.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    return {
        "message": "Login exitoso",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "rol_id": usuario.rol_id,
            "activo": usuario.activo
        }
    }