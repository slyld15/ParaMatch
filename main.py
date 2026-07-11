from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import athletes, tournaments, auth

app = FastAPI(title="ParaMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(athletes.router)
app.include_router(tournaments.router)


@app.get("/")
def health_check():
    return {"status": "ParaMatch API is running"}
