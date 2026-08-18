"""Optional LLM step: narrates a decision the rules already made. Never makes the decision itself."""

from __future__ import annotations

from typing import Any

_SYSTEM_PROMPT = (
    "You write single-sentence, plain-language rationales for a commercial real estate "
    "opportunity list. Ground every statement strictly in the fields you are given; never "
    "introduce a fact that isn't in them, and never make a recommendation - a rules engine "
    "already decided this record qualifies, your only job is to explain why in one sentence."
)


def generate_rationale(
    opportunity: dict[str, Any], fired_rules: list[str], model: str = "claude-opus-5"
) -> str | None:
    """Writes one grounded sentence explaining why an opportunity was flagged.

    Purely explanatory and called only after ranking and qualification are already final -
    its output is never read back into scoring, so a failure here never changes which
    opportunities appear or in what order, only whether that row has a rationale.
    Returns None (rather than raising) if the anthropic package isn't installed, no
    credentials are configured, or the request fails for any reason - this step must
    degrade gracefully, since it is explicitly not load-bearing for the pipeline.
    """
    try:
        import anthropic
    except ImportError:
        return None

    prompt = (
        "Explain in exactly one plain-language sentence why this commercial real estate "
        "record was flagged as a cross-line-of-business opportunity. Base the sentence "
        "strictly on the fields below - do not infer or invent anything not present here. "
        "Write a natural sentence a broker could read, not a restatement of the rule names.\n\n"
        f"Entity: {opportunity.get('entity_name')}\n"
        f"Sale price: {opportunity.get('sale_price') or 'n/a'}\n"
        f"Loan amount: {opportunity.get('loan_amount') or 'n/a'}\n"
        f"Loan maturity date: {opportunity.get('maturity_date') or 'n/a'}\n"
        f"Loan notes: {opportunity.get('notes') or 'n/a'}\n"
        f"Entity resolution confidence: {opportunity.get('entity_resolution_confidence')}\n"
        f"Rules that fired: {', '.join(fired_rules)}\n"
    )

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        # Deliberately broad: missing/invalid credentials, network failures, rate limits,
        # and malformed responses should all fall back to "no rationale", never crash the run.
        return None

    text = next((block.text for block in response.content if block.type == "text"), None)
    return text.strip() if text else None
