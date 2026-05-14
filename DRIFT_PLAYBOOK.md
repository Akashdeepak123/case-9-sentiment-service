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


## 7. On the adversarial guard's limits — what's enough vs. what's done

The shipped `app/input_guard.py` is a heuristic regex layer covering 
known prompt-injection patterns, length attacks, non-ASCII heavy 
inputs, repetition spam, and all-caps. It will catch the obvious 
class of attacks — and miss novel phrasings every week.

**Why ship this anyway:** the regex layer is cheap (zero ms), 
transparent (an engineer can read every rule), and catches the bulk 
of low-effort attacks. The interesting question isn't whether to ship 
it — it's what comes next.

**The production layered defense:**

1. **Layer 1 (built):** Heuristic regex. Cheap, transparent, catches 
   known patterns. Update with new patterns weekly via PRs.

2. **Layer 2 (designed):** Fine-tuned classifier like 
   `protectai/deberta-v3-base-prompt-injection-v2` — a model whose 
   job is "is this a prompt injection?" Run alongside the heuristic. 
   ~50 ms latency cost.

3. **Layer 3 (designed):** Output filtering. After the model 
   responds, check whether the response contains anything that looks 
   like the system prompt being leaked. Catches injections that got 
   past 1 and 2.

4. **Layer 4 (designed):** Rate-limiting per source. If 5+ 
   injection-flagged inputs come from one IP in 10 minutes, throttle 
   that source. Most injection attempts come in bursts.

5. **Layer 5 (operational):** Sample flagged inputs into a weekly 
   review queue. Human eyeballs catch novel patterns to feed back into 
   Layer 1.

The cost-benefit: Layer 1 is 60 lines of code and blocks 70% of 
script-kiddie attacks. Layer 2 is another model and ~50ms latency for 
maybe +15% coverage. Layers 3-5 are the slope from "demo" to 
"production." Knowing which layer to be on at each stage of a 
product's growth is the engineering call.

**This service is at Layer 1.** That's the right place for a 
demonstration. A real production service serving real users would be 
on Layers 1-4 from day one and Layer 5 by month three.