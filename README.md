# Sentiment Service

A production-minded sentiment classification service with evaluation, drift detection, and CI.

## Status

Work in progress — building toward demo submission

## How to Run Locally

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

In another terminal (with the venv activated):

```bash
curl http://localhost:8000/health
```
