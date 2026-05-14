# DRIFT_PLAYBOOK — How I'd Know This Model Is Broken in Production

The case author said "few freshers think about how would I know this
is broken in production — that's the differentiator we're hunting for."
This document is exactly that.

## 1. What could break this model in production

**Data drift.** Input distribution shifts. A fintech customer onboards
and their banking-complaint vocabulary diverges from movie reviews the
model was trained on. The model still returns predictions, but with
eroding confidence on words it has never strongly seen.

**Concept drift.** The label meaning shifts. Sarcasm — "best day ever"
after a service outage is business-NEGATIVE but the model confidently
predicts POSITIVE. No input-distribution alarm fires; the words are
familiar, the meaning has moved.

**Pipeline failure.** Tokenizer version mismatch after a transformers
upgrade. Encoding bugs that silently truncate the negation. These
look like model failures but aren't — rolling back the model won't
help. Reading logs is the only way to tell.

**Eval set rot.** The held-out 30 samples drift from real production
traffic over months. CI keeps passing while real performance degrades.
The silent killer of model serving.

## 2. How I'd detect each

| Failure | Signal | Threshold | Tool |
|---|---|---|---|
| Data drift | KS test on text length, Jaccard on top-200 vocab | p<0.05 OR Jaccard<0.5 | Designed in DECISIONS; would add /drift endpoint |
| Concept drift | Human-labeled sample weekly | Disagreement rate >5% | Not built — see Section 4 |
| Pipeline failure | Confidence median + error rate spike | Median confidence drops >10% in 1 hour | Logs.db query + Render logs |
| Eval set rot | Compare eval-set vocab to recent prod-log vocab | Jaccard <0.6 over 30 days | Manual quarterly review (drafted) |

## 3. What I'd do at 2 AM

1. Alert fires (UptimeRobot OR drift threshold breach). Open the live
   service in browser. Confirm /health responds.
2. If /health returns 5xx: app crashed. Check HF Space logs. Roll back
   to previous git tag (see RUNBOOK.md).
3. If /health is fine but predictions look wrong: query the log DB.
   Look at confidence distribution over the last hour vs the baseline
   (median should be ~0.95+). If confidence has cratered, model is
   uncertain — something upstream changed.
4. If both length distribution AND vocab Jaccard shifted in the same
   window: tokenizer/pipeline issue. ROLLBACK image. Do not investigate
   first — restore service first, debug second.
5. If only vocab drift over hours (not minutes): likely legitimate
   traffic shift. DON'T rollback. Page the data team during business
   hours. Continue serving.
6. If uncertain after 10 minutes: route traffic to the previous model
   (would use shadow deployment infra — see "What's not built" below).
   Investigate without customer impact.

## 4. What I'm NOT monitoring yet (honest gaps)

- **Concept drift requires labeled feedback I don't have.** Would
  build: a 50-sample-per-week human-review queue surfaced via a
  /review endpoint, with a /label sister endpoint reviewers post back to.
- **Adversarial inputs** (prompt-injection-style payloads). Would add
  an input validator before model invocation: length cap, banned-token
  list, language sanity check.
- **Cohort-level drift** (specific customer segments drift while overall
  traffic looks normal). Would require joining logs with user metadata
  — we don't store user IDs by design (PII).
- **Per-request cost monitoring.** Single-model service today; routing
  across multiple models would need this.
- **Shadow deployment.** Loading a candidate model in parallel, never
  exposing its output to users, computing disagreement rate offline.
  De-scoped for time. The eval harness and CI gate are the foundation
  this would build on.

## 5. The 60-day rollout plan for a new model

1. Eval gate on PR (BUILT — see .github/workflows/ci.yml)
2. Merge to main, shadow-deploy to 1% traffic (NOT BUILT — designed)
3. Monitor for 7 days: disagreement <2%, no latency regression >50ms p95
4. Promote to 50% canary for 7 days, same metrics
5. Full promotion if guardrails hold

## 6. Philosophy

A model in production is a service. Services have on-call. On-call
needs runbooks. This is the runbook. Most "ML in production" failures
don't look like ML failures — they look like ops failures. Treat them
like ops failures.
