from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    rol_id: int

class UserLogin(BaseModel):
    correo: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    rol_id: int
    activo: bool

    class Config:
        from_attributes = True