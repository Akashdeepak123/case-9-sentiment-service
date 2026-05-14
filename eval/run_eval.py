"""
Eval harness for the sentiment model.

Loads test_set.jsonl, runs the model in-process (not via API — we
evaluate the model itself), computes metrics, and compares against a
committed baseline. Exits non-zero on regression — CI uses this to
block PRs that degrade quality.
"""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.model import MODEL_VERSION, SentimentModel  # noqa: E402

EVAL_DIR = Path(__file__).parent
TEST_SET = EVAL_DIR / "test_set.jsonl"
LATEST_METRICS = EVAL_DIR / "latest_metrics.json"
BASELINE_METRICS = EVAL_DIR / "baseline_metrics.json"
F1_REGRESSION_TOLERANCE = 0.02  # 2 percentage points


def load_test_set(path: Path) -> list[dict]:
    examples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def _compute_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    # Confusion counts for POSITIVE class
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == "POSITIVE" and p == "POSITIVE")
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == "NEGATIVE" and p == "POSITIVE")
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == "POSITIVE" and p == "NEGATIVE")
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == "NEGATIVE" and p == "NEGATIVE")

    accuracy = (tp + tn) / len(y_true) if y_true else 0.0

    # Macro F1: average of POSITIVE-F1 and NEGATIVE-F1
    pos_precision = tp / (tp + fp) if (tp + fp) else 0.0
    pos_recall = tp / (tp + fn) if (tp + fn) else 0.0
    pos_f1 = (
        2 * pos_precision * pos_recall / (pos_precision + pos_recall)
        if (pos_precision + pos_recall)
        else 0.0
    )

    neg_precision = tn / (tn + fn) if (tn + fn) else 0.0
    neg_recall = tn / (tn + fp) if (tn + fp) else 0.0
    neg_f1 = (
        2 * neg_precision * neg_recall / (neg_precision + neg_recall)
        if (neg_precision + neg_recall)
        else 0.0
    )

    return {
        "accuracy": round(accuracy, 4),
        "f1_macro": round((pos_f1 + neg_f1) / 2, 4),
        "precision_macro": round((pos_precision + neg_precision) / 2, 4),
        "recall_macro": round((pos_recall + neg_recall) / 2, 4),
    }


def run_eval(model: SentimentModel, examples: list[dict]) -> dict:
    y_true = []
    y_pred = []
    latencies = []

    print(f"Running eval on {len(examples)} examples...")
    for i, ex in enumerate(examples):
        result = model.predict(ex["text"])
        y_true.append(ex["label"])
        y_pred.append(result["label"])
        latencies.append(result["latency_ms"])
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(examples)}")

    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2]
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]

    metrics = _compute_metrics(y_true, y_pred)

    return {
        "model_version": MODEL_VERSION,
        "n_examples": len(examples),
        **metrics,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
    }


def compare_to_baseline(
    latest: dict, baseline: dict, tolerance: float = F1_REGRESSION_TOLERANCE
) -> tuple[bool, str]:
    f1_delta = latest["f1_macro"] - baseline["f1_macro"]
    if f1_delta < -tolerance:
        return (
            False,
            f"REGRESSION: F1 dropped {f1_delta:+.4f} (tolerance: {tolerance})",
        )
    return True, f"PASS: F1 delta {f1_delta:+.4f} within tolerance"


def print_table(latest: dict, baseline: dict | None) -> None:
    print("\n" + "=" * 60)
    print(f"{'Metric':<25} {'Latest':>12} {'Baseline':>12} {'Delta':>10}")
    print("-" * 60)
    for key in [
        "accuracy",
        "f1_macro",
        "precision_macro",
        "recall_macro",
        "latency_p50_ms",
        "latency_p95_ms",
    ]:
        l = latest.get(key, "-")
        b = baseline.get(key, "-") if baseline else "-"
        if baseline and isinstance(l, (int, float)) and isinstance(b, (int, float)):
            delta = f"{l - b:+.4f}" if isinstance(l, float) else f"{l - b:+d}"
        else:
            delta = "-"
        print(f"{key:<25} {l!s:>12} {b!s:>12} {delta:>10}")
    print("=" * 60)


def main() -> None:
    print(f"Loading model {MODEL_VERSION}...")
    model = SentimentModel()

    examples = load_test_set(TEST_SET)
    metrics = run_eval(model, examples)

    LATEST_METRICS.write_text(json.dumps(metrics, indent=2))
    print(f"\nWrote {LATEST_METRICS}")

    baseline = None
    if BASELINE_METRICS.exists():
        baseline = json.loads(BASELINE_METRICS.read_text())

    print_table(metrics, baseline)

    if baseline:
        passed, msg = compare_to_baseline(metrics, baseline)
        print(f"\n{msg}")
        if not passed:
            sys.exit(1)
    else:
        print("\nNo baseline yet — current run becomes the baseline.")
        print(f"  Copy with: cp {LATEST_METRICS} {BASELINE_METRICS}")

    sys.exit(0)


if __name__ == "__main__":
    main()
