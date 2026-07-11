from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import athletes, tournaments
import storage

app = FastAPI(title="ParaMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(athletes.router)
app.include_router(tournaments.router)

storage.seed_demo_athletes()


@app.get("/")
def health_check():
    return {"status": "ParaMatch API is running"}
