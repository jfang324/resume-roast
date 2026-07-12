"""MODEL_PRICING catalog sync and cost estimation."""

from resume_roast.integrations.nvidia.pricing import MODEL_PRICING, estimate_cost
from resume_roast.integrations.nvidia.types import Usage
from resume_roast.persistence.settings.types import MODELS


def test_pricing_covers_exactly_the_settings_model_catalog() -> None:
    assert set(MODEL_PRICING) == set(MODELS)


def test_every_price_is_positive() -> None:
    for input_price, output_price in MODEL_PRICING.values():
        assert input_price > 0
        assert output_price > 0


def test_estimate_cost_charges_input_and_output_rates() -> None:
    usage = Usage(prompt_tokens=1_000_000, completion_tokens=2_000_000, total_tokens=3_000_000)
    cost = estimate_cost(usage, "nvidia/nemotron-3-super-120b-a12b")
    assert cost == 0.09 + 2 * 0.45


def test_estimate_cost_returns_none_for_unknown_model() -> None:
    usage = Usage(prompt_tokens=100, completion_tokens=100, total_tokens=200)
    assert estimate_cost(usage, "unknown/model") is None


def test_estimate_cost_is_zero_for_zero_tokens() -> None:
    usage = Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
    assert estimate_cost(usage, "deepseek-ai/deepseek-v4-flash") == 0.0
