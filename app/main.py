"""FastAPI entry point for the sentiment classification HTTP API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from app.model import SentimentModel


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.1.0",
        "service": "sentiment-api",
    }


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    result = app.state.model.predict(request.text)
    return PredictResponse(**result)
