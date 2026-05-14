---
title: Sentiment Service
emoji: 👀
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Sentiment Service

> 🌐 **Live Demo:** https://akashdeepak1-sentiment-service.hf.space *(coming live after build completes)*

[![CI](https://github.com/Akashdeepak123/case-9-sentiment-service/actions/workflows/ci.yml/badge.svg)](https://github.com/Akashdeepak123/case-9-sentiment-service/actions/workflows/ci.yml)

> 📺 **Demo Video:** coming with submission

A production-minded sentiment classification service with structured logging, evaluation harness, and CI that blocks regressions.

## Status

Work in progress — building toward demo submission.

## Run locally (Docker-first — recommended)

```bash
# Run the API
docker compose up --build

# In another terminal, run the tests
docker compose run --rm tests
```

Open http://localhost:8000/docs for the interactive API.

## Run locally (without Docker — Linux / Intel Mac only)

Apple Silicon Macs may hit known transformers + Apple Silicon shutdown issues. Use Docker on Apple Silicon. Otherwise:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
python -m uvicorn app.main:app --reload
```

## Stack

| Layer | Choice |
|---|---|
| API | FastAPI |
| Model | DistilBERT (HuggingFace) |
| Container | Docker |
| Logging | SQLite |
| Deploy | Hugging Face Spaces |
| CI | GitHub Actions |

## Evaluation

The model is evaluated against a held-out 30-sample test set on every
PR. CI fails if F1 (macro) drops more than 2 percentage points from the
committed baseline.

```bash
# Run eval inside the container
docker compose run --rm sentiment-api python eval/run_eval.py
```

Baseline metrics live in eval/baseline_metrics.json and are committed.

## License

MIT