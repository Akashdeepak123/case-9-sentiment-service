"""FastAPI entry point for the sentiment classification HTTP API."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "0.1.0",
        "service": "sentiment-api",
    }
