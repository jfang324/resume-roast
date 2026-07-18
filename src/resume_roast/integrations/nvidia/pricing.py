"""Per-model NIM pricing and cost estimation."""

from resume_roast.integrations.types import Usage

MODEL_PRICING: dict[str, tuple[float, float]] = {
    "nvidia/nemotron-3-super-120b-a12b": (0.09, 0.45),
    "deepseek-ai/deepseek-v4-flash": (0.14, 0.28),
    "mistralai/mistral-large-3-675b-instruct-2512": (0.50, 1.50),
    "meta/llama-4-maverick-17b-128e-instruct": (0.15, 0.60),
}
"""($ per 1M input tokens, $ per 1M output tokens) for every catalog model.

A test pins the keys to the `Settings` model catalog so the two can't drift.
"""

_TOKENS_PER_PRICE_UNIT = 1_000_000


def estimate_cost(usage: Usage, model: str) -> float | None:
    """Estimate the cost in USD of one call, or None when `model` has no pricing.

    None (rather than $0) lets displays skip the figure instead of understating it.
    """
    prices = MODEL_PRICING.get(model)
    if prices is None:
        return None

    input_price, output_price = prices
    cost = usage.prompt_tokens / _TOKENS_PER_PRICE_UNIT * input_price
    cost += usage.completion_tokens / _TOKENS_PER_PRICE_UNIT * output_price

    return cost
