"""Tests for model pricing and cost estimation."""

from __future__ import annotations

from gitowl.pricing import DEFAULT_PRICING, PricingTable, default_pricing_table


def test_known_model_cost_is_input_plus_output() -> None:
    table = default_pricing_table()
    # gpt-4o-mini = (0.15, 0.60) per 1M tokens.
    # 1M in + 1M out => 0.15 + 0.60 = 0.75.
    cost = table.estimate_cost("openai/gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost == 0.75


def test_cost_scales_with_token_counts() -> None:
    table = default_pricing_table()
    # 500k in @0.15, 250k out @0.60 => 0.075 + 0.15 = 0.225.
    cost = table.estimate_cost("openai/gpt-4o-mini", 500_000, 250_000)
    assert cost == 0.225


def test_unknown_model_returns_none() -> None:
    table = default_pricing_table()
    assert table.estimate_cost("some/unpriced-model", 1000, 1000) is None
    assert table.price_for("some/unpriced-model") is None


def test_lookup_is_case_insensitive() -> None:
    table = default_pricing_table()
    assert table.price_for("OpenAI/GPT-4o-Mini") == DEFAULT_PRICING["openai/gpt-4o-mini"]


def test_override_wins_over_default() -> None:
    table = PricingTable(overrides={"openai/gpt-4o-mini": (1.0, 2.0)})
    assert table.price_for("openai/gpt-4o-mini") == (1.0, 2.0)
    # 1M in @1.0 + 1M out @2.0 = 3.0.
    assert table.estimate_cost("openai/gpt-4o-mini", 1_000_000, 1_000_000) == 3.0


def test_override_adds_new_model() -> None:
    table = PricingTable(overrides={"local/custom": (0.0, 0.0)})
    assert table.price_for("local/custom") == (0.0, 0.0)
    assert table.estimate_cost("local/custom", 999, 999) == 0.0


def test_zero_tokens_costs_zero() -> None:
    assert default_pricing_table().estimate_cost("openai/gpt-4o-mini", 0, 0) == 0.0
