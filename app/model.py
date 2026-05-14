import os

# Disables HuggingFace tokenizer parallelism to prevent semaphore leaks on macOS that cause bus errors during process shutdown.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import time

from transformers import pipeline

MODEL_VERSION = "distilbert-sst2-v1"
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


class SentimentModel:
    """Loads DistilBERT SST-2 once and runs CPU inference via Hugging Face pipeline."""

    def __init__(self) -> None:
        self._pipe = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            device=-1,
        )

    def predict(self, text: str) -> dict[str, str | float | int]:
        start = time.perf_counter()
        outputs = self._pipe(text, truncation=True, max_length=512)
        latency_ms = int((time.perf_counter() - start) * 1000)

        result = outputs[0]
        label = str(result["label"])
        score = float(result["score"])

        return {
            "label": label,
            "score": score,
            "latency_ms": latency_ms,
            "model_version": MODEL_VERSION,
        }
