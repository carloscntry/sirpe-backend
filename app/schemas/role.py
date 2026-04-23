from pydantic import BaseModel

class RoleCreate(BaseModel):
    nombre: str
    descripcion: str | None = None

class RoleResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None

    class Config:
        from_attributes = True