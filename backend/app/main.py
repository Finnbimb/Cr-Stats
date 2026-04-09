import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.database import Base, engine, ensure_schema
from app.routes import auth, dashboard, misc, profile
from app.services.war_tracking import poll_war_data_loop

app = FastAPI(title="CrStats API")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_war_data_loop())

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
ensure_schema()

app.include_router(misc.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(dashboard.router)
