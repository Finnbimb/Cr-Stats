import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.database import init_database
from app.routes import auth, dashboard, members, misc, profile, rankings

from contextlib import asynccontextmanager
from app.services.war_tracking import poll_war_data_loop
from app.services.ranking_snapshots import snapshot_loop


async def lifespan(app: FastAPI):
    task1 = asyncio.create_task(poll_war_data_loop())
    task2 = asyncio.create_task(snapshot_loop())
    yield
    task1.cancel()
    task2.cancel()
    
    
app = FastAPI(title="CrStats API")


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
