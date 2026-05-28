from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from model.pitch_mappings import PITCHES
from model.recommend import recommend_pitch


class RecommendationRequest(BaseModel):
    balls: int = Field(ge=0, le=3)
    strikes: int = Field(ge=0, le=2)
    outs: int = Field(ge=0, le=2)
    on_1b: bool
    on_2b: bool
    on_3b: bool
    batter_hand: str = Field(pattern="^[LR]$")
    pitcher_hand: str = Field(pattern="^[LR]$")
    prev_pitch: str | None = None
    available_pitches: list[str] = Field(min_length=1)


app = FastAPI(
    title="Pitch Recommendation API",
    version="0.1.0",
    description="FastAPI backend for reinforcement-learning pitch recommendations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/pitches")
def pitches() -> list[dict[str, str]]:
    return [{"code": code, **details} for code, details in PITCHES.items()]


@app.post("/recommend")
def recommend(request: RecommendationRequest) -> dict:
    try:
        return recommend_pitch(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
