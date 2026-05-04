import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.database import init_database
from app.routes import auth, dashboard, members, misc, profile, rankings
from app.services.war_tracking import poll_war_data_loop
from app.services.ranking_snapshots import snapshot_loop

app = FastAPI(title="CrStats API")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_war_data_loop())
    asyncio.create_task(snapshot_loop())

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_database()

app.include_router(misc.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(dashboard.router)
app.include_router(members.router)
app.include_router(rankings.router)
