from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes.user_routes import router as user_router
from app.routes.zone_routes import router as zone_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SIRPE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(zone_router)

@app.get("/")
def root():
    return {"message": "SIRPE API operativa"}