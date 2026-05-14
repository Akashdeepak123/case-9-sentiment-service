"""
Adversarial input detector.

Runs heuristic checks on incoming text BEFORE the model sees it. Detects:
- Prompt-injection patterns
- Excessive length (potential payload smuggling)
- Non-ASCII character density
- Repetitive spam
- All-caps screaming
"""
import re

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(\w+\s+){0,3}(instructions?|prompts?|prior|previous|above|context)",
    r"disregard\s+(the\s+)?(above|previous|prior)",
    r"you\s+are\s+now\s+(a|an|going)",
    r"new\s+instructions?:",
    r"system\s*[:>]",
    r"forget\s+(everything|all|previous)",
    r"</?(system|user|assistant)>",
    r"```\s*system",
    r"act\s+as\s+(a|an|if)",
]

PROMPT_INJECTION_RE = re.compile("|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)


def check_input(text: str) -> dict:
    """Run all heuristic checks. Returns structured guard report."""
    flags = []
    risk_score = 0
    text_len = len(text)

    if text_len > 5000:
        flags.append("excessive_length")
        risk_score += 30
    elif text_len > 2000:
        flags.append("long_input")
        risk_score += 10

    if PROMPT_INJECTION_RE.search(text):
        flags.append("prompt_injection_suspect")
        risk_score += 80

    if text_len > 0:
        non_ascii = sum(1 for c in text if ord(c) > 127)
        ascii_ratio = non_ascii / text_len
        if ascii_ratio > 0.3:
            flags.append("non_ascii_heavy")
            risk_score += 20

    if text_len > 20:
        tokens = text.lower().split()
        if tokens:
            most_common = max(set(tokens), key=tokens.count)
            most_common_ratio = tokens.count(most_common) / len(tokens)
            if most_common_ratio > 0.5 and len(tokens) > 10:
                flags.append("repetitive_spam")
                risk_score += 40

    if text_len > 20:
        alpha_count = sum(1 for c in text if c.isalpha())
        if alpha_count > 0:
            caps_ratio = sum(1 for c in text if c.isupper()) / alpha_count
            if caps_ratio > 0.8:
                flags.append("all_caps")
                risk_score += 10

    if risk_score >= 80:
        action = "block"
    elif risk_score >= 40:
        action = "flag"
    else:
        action = "allow"

    return {
        "passed": action != "block",
        "flags": flags,
        "risk_score": min(risk_score, 100),
        "action": action,
    }