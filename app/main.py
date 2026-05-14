"""FastAPI entry point for the sentiment classification HTTP API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from app.logging_setup import init_db, log_prediction
from app.model import SentimentModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.model = SentimentModel()
    yield


app = FastAPI(lifespan=lifespan)


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    label: str
    score: float
    latency_ms: int
    model_version: str


@app.get("/")
def root() -> dict:
    """Root route — friendly landing for visitors."""
    return {
        "service": "sentiment-api",
        "docs": "/docs",
        "health": "/health",
        "predict": "/predict (POST)",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.1.0",
        "service": "sentiment-api",
    }


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    # DEMO HACK — simulating a regressed model to verify CI catches it.
    # This branch is for the CI rejection demo only; main has the real
    # prediction path. DO NOT MERGE THIS BRANCH.
    result = {
        "label": "POSITIVE",
        "score": 0.5,
        "latency_ms": 1,
        "model_version": "broken-test",
    }
    response = PredictResponse(**result)
    log_prediction(
        request.text,
        response.label,
        response.score,
        response.latency_ms,
        response.model_version,
    )
    return response
