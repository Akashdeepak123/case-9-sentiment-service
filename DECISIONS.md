# Decisions

## Logging: SQLite with SHA-256 text hashing

**What:** every prediction logs to a local SQLite database.
**Why SQLite:** zero infrastructure, queryable with SQL, file-based.
Swaps to Postgres in production with one connection string change.
**Why hash text:** PII safety. We never store raw user input. The hash
plus length is enough to find a specific prediction by recomputing the
hash from the user's complaint.
**In production:** Postgres + structured logs to a log aggregator
(Datadog, CloudWatch, etc).

## Development environment: Docker-first

Apple Silicon Python 3.11 + transformers showed intermittent shutdown
crashes during pytest. Linux containers are rock-solid for the same
code, and they match our production deploy target. Doing dev inside
the container removes a class of "works on my machine" bugs.

## Evaluation: committed baseline + regression gate

**Why a held-out test set:** the JD lists "evaluation-first mindset"
three times. This is the artifact that proves it.

**Why 30 samples, not 2000:** for a demo with a pretrained model on a
well-known task, a small curated set gives a fast signal and is
inspectable. In production: 1000+ samples drawn from real traffic,
plus a continuous human-review queue.

**Why F1 macro, not accuracy:** balanced metric that doesn't reward
predicting the majority class.

**Tolerance: 2 percentage points.** Tight enough to catch real
regressions, loose enough to avoid flapping on dataset variance.

## CI: tests + eval as merge gates

Every push to main and every PR triggers GitHub Actions. The workflow:
1. Installs dependencies in a clean Ubuntu environment.
2. Runs pytest (6 tests).
3. Runs eval/run_eval.py — exits 1 if F1 macro drops > 2 percentage
   points from baseline_metrics.json.

If either step fails, the commit gets a red X. With branch protection
enabled, this blocks merges to main.

**Why this matters:** the JD lists "build evaluation systems (offline
metrics, regression suites)" explicitly. This workflow IS the
regression suite. It treats the model like any other production
software — quality gates before merge.

**In production:** add a third step running tests against a staging
deployment, plus latency budget checks. Add branch protection rule
requiring this workflow to pass before merge.
