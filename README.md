# Sentiment Service

A production-minded sentiment classification service with evaluation, drift detection, and CI.

## Status

Work in progress — building toward demo submission

## Run locally (Docker-first — recommended)

```bash
# Run the API
docker compose up --build

# In another terminal, run the tests
docker compose run --rm tests
```

Open http://localhost:8000/docs for the interactive API.

## Run locally (without Docker — Linux/Intel Mac only)

Apple Silicon Macs may hit known transformers + Apple Silicon issues.
Use Docker on Apple Silicon. Otherwise:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
python -m uvicorn app.main:app --reload
```
