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

# Sentiment Service — Production-Minded ML Serving

> 🌐 **Live API:** https://akashdeepak1-sentiment-service.hf.space
> 
> 📖 **Interactive Docs:** https://akashdeepak1-sentiment-service.hf.space/docs
> 
> ⚡ **CI Status:** [![CI](https://github.com/Akashdeepak123/case-9-sentiment-service/actions/workflows/ci.yml/badge.svg)](https://github.com/Akashdeepak123/case-9-sentiment-service/actions/workflows/ci.yml)

A sentiment classification service that knows when it's wrong before customers do — with a CI gate that refuses to deploy regressions and a documented playbook for the failure modes that matter.

![Demo](docs/demo.gif)

## What this demonstrates

Maps directly to the AI/ML Consultant role expectations:

| Requirement | Where in this build |
|---|---|
| Build evaluation systems (offline metrics, regression suites) | `eval/run_eval.py`, `eval/baseline_metrics.json` |
| Identify edge cases like drift, hallucinations, bias | `DRIFT_PLAYBOOK.md` — failure modes, detection, on-call tree |
| Own model quality, latency, cost, and safety in production | CI gate, latency tracking in eval, SHA-256 PII safety |
| Production ML deployment | Dockerfile + HF Spaces, live URL, structured logging |
| Strong written communication | This README, DECISIONS.md, DRIFT_PLAYBOOK.md |

## Quick demo

```bash
# Hit the live service
curl https://akashdeepak1-sentiment-service.hf.space/health

curl -X POST https://akashdeepak1-sentiment-service.hf.space/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "this exceeded every expectation I had"}'
```

Note: the free-tier Space sleeps after inactivity. First request after a long idle takes 30–60s to wake.

## Run locally

```bash
git clone https://github.com/Akashdeepak123/case-9-sentiment-service
cd case-9-sentiment-service
docker compose up --build
```

Then open http://localhost:8000/docs for the interactive API.

### Running tests

```bash
docker compose run --rm tests
```

### Running the eval harness

```bash
docker compose run --rm -v "$(pwd)/eval:/app/eval" sentiment-api python eval/run_eval.py
```

## Architecture
POST /predict
   Client  ──────────────────────────►  FastAPI app
                                            │
                   ┌────────────────────────┤
                   ▼                        ▼
               DistilBERT              SQLite log
              (HF pipeline)         (hashed text + meta)
                   │                        │
                   └────────┬───────────────┘
                            ▼
                    Pydantic response
                    ────────────────►  Client
                    GitHub PR ──► Actions CI ──► pytest ──► eval ──► merge gate
│
└──► fails build
if F1 drops >2pp
## Stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI | Async, automatic OpenAPI docs, listed in the JD |
| Model | DistilBERT SST-2 | 250 MB, <30 ms p95 on CPU, F1 0.97 on held-out set |
| Container | Docker + Compose | Reproducible local dev that matches the deploy target |
| Logging | SQLite + SHA-256 hashed text | Zero infra, queryable, PII-safe |
| Deployment | Hugging Face Spaces | 16 GB free tier, purpose-built for ML serving |
| CI | GitHub Actions | Runs pytest + eval on every PR, blocks regressions |
| Eval | 30-sample held-out + committed baseline | Reproducible quality gate |

## Key decisions and trade-offs

See [DECISIONS.md](./DECISIONS.md). Highlights:

- **Switched from Render to HF Spaces** after Render's 512 MB free tier couldn't fit DistilBERT in memory. HF Spaces gives 16 GB free.
- **Switched to Docker-first development** after Apple Silicon + Python 3.13 produced intermittent bus errors. Linux containers are rock-solid for the same code and match production.
- **Custom drift detection over Evidently/Arize.** Explainable in 10 lines; the named libraries are a 1-day swap if production needs them.
- **Single-stage Dockerfile.** Multi-stage saves ~150 MB of image size but adds debug overhead. Documented as a follow-up.

## What's NOT done (de-scoped honestly)

- Shadow deployment for candidate models — described in the playbook's 60-day rollout plan.
- Per-cohort drift monitoring — requires PII I deliberately don't store.
- API authentication — internal demo service. In production: API keys + rate limiting.
- UptimeRobot external monitor — HF Spaces' built-in healthcheck covers MVP needs.

## How I'd know this is broken in production

See [DRIFT_PLAYBOOK.md](./DRIFT_PLAYBOOK.md). The differentiator document — four failure modes, detection thresholds, a 2 AM decision tree, and explicit gaps I haven't covered yet.

## License

MIT — see [LICENSE](./LICENSE).