"""
Cost Estimation Script - Estimate API Costs

Estimates token usage and costs for agent workloads.
"""

import sys


# Pricing per 1K tokens (as of 2026)
PRICING = {
    "gpt-4o": {
        "input": 0.0025,
        "output": 0.01,
    },
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.0006,
    },
    "gpt-4-turbo": {
        "input": 0.01,
        "output": 0.03,
    },
}


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 characters per token)."""
    return len(text) // 4


def estimate_cost(
    model: str,
    input_text: str,
    expected_output_tokens: int = 500,
) -> dict:
    """Estimate cost for a single query."""
    if model not in PRICING:
        return {
            "error": f"Unknown model: {model}",
            "available_models": list(PRICING.keys()),
        }

    input_tokens = estimate_tokens(input_text)
    output_tokens = expected_output_tokens

    input_cost = (input_tokens / 1000) * PRICING[model]["input"]
    output_cost = (output_tokens / 1000) * PRICING[model]["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }


def estimate_workload(
    model: str,
    queries_per_day: int,
    avg_input_length: int,
    avg_output_tokens: int = 500,
) -> dict:
    """Estimate cost for a workload."""
    if model not in PRICING:
        return {
            "error": f"Unknown model: {model}",
            "available_models": list(PRICING.keys()),
        }

    # Estimate per query
    input_tokens = avg_input_length // 4
    output_tokens = avg_output_tokens

    input_cost_per_query = (input_tokens / 1000) * PRICING[model]["input"]
    output_cost_per_query = (output_tokens / 1000) * PRICING[model]["output"]
    cost_per_query = input_cost_per_query + output_cost_per_query

    # Daily costs
    daily_cost = cost_per_query * queries_per_day
    monthly_cost = daily_cost * 30
    yearly_cost = daily_cost * 365

    return {
        "model": model,
        "queries_per_day": queries_per_day,
        "tokens_per_query": input_tokens + output_tokens,
        "cost_per_query": cost_per_query,
        "daily_cost": daily_cost,
        "monthly_cost": monthly_cost,
        "yearly_cost": yearly_cost,
    }


def compare_models(
    input_text: str,
    expected_output_tokens: int = 500,
) -> dict:
    """Compare costs across models."""
    results = {}

    for model in PRICING.keys():
        results[model] = estimate_cost(model, input_text, expected_output_tokens)

    return results


def print_single_estimate(result: dict):
    """Print single query estimate."""
    print("\n" + "="*60)
    print("SINGLE QUERY COST ESTIMATE")
    print("="*60)
    print(f"Model: {result['model']}")
    print(f"Input tokens: {result['input_tokens']:,}")
    print(f"Output tokens: {result['output_tokens']:,}")
    print(f"Total tokens: {result['total_tokens']:,}")
    print(f"\nInput cost: ${result['input_cost']:.6f}")
    print(f"Output cost: ${result['output_cost']:.6f}")
    print(f"Total cost: ${result['total_cost']:.6f}")
    print("="*60)


def print_workload_estimate(result: dict):
    """Print workload estimate."""
    print("\n" + "="*60)
    print("WORKLOAD COST ESTIMATE")
    print("="*60)
    print(f"Model: {result['model']}")
    print(f"Queries per day: {result['queries_per_day']:,}")
    print(f"Tokens per query: {result['tokens_per_query']:,}")
    print(f"\nCost per query: ${result['cost_per_query']:.6f}")
    print(f"Daily cost: ${result['daily_cost']:.2f}")
    print(f"Monthly cost: ${result['monthly_cost']:.2f}")
    print(f"Yearly cost: ${result['yearly_cost']:.2f}")
    print("="*60)


def print_comparison(results: dict):
    """Print model comparison."""
    print("\n" + "="*60)
    print("MODEL COMPARISON")
    print("="*60)

    for model, result in results.items():
        print(f"\n{model}:")
        print(f"  Total cost: ${result['total_cost']:.6f}")
        print(f"  Input: ${result['input_cost']:.6f} ({result['input_tokens']:,} tokens)")
        print(f"  Output: ${result['output_cost']:.6f} ({result['output_tokens']:,} tokens)")

    # Find cheapest
    cheapest = min(results.items(), key=lambda x: x[1]['total_cost'])
    print(f"\n✓ Cheapest: {cheapest[0]} (${cheapest[1]['total_cost']:.6f})")
    print("="*60)


def main():
    print("\n" + "="*60)
    print("OPENAI AGENTS SDK - COST ESTIMATOR")
    print("="*60)

    # Example 1: Single query estimate
    print("\n--- Example 1: Single Query ---")
    query = "What is machine learning? Explain in detail with examples."
    result = estimate_cost("gpt-4o", query, expected_output_tokens=500)
    print_single_estimate(result)

    # Example 2: Workload estimate
    print("\n--- Example 2: Daily Workload ---")
    result = estimate_workload(
        model="gpt-4o-mini",
        queries_per_day=1000,
        avg_input_length=200,  # characters
        avg_output_tokens=300,
    )
    print_workload_estimate(result)

    # Example 3: Model comparison
    print("\n--- Example 3: Model Comparison ---")
    query = "Analyze this data and provide insights."
    results = compare_models(query, expected_output_tokens=500)
    print_comparison(results)

    # Cost savings example
    print("\n" + "="*60)
    print("COST SAVINGS ANALYSIS")
    print("="*60)
    print("\nFor 1000 queries/day with 500 output tokens:")

    gpt4o = estimate_workload("gpt-4o", 1000, 200, 500)
    gpt4o_mini = estimate_workload("gpt-4o-mini", 1000, 200, 500)

    savings_daily = gpt4o["daily_cost"] - gpt4o_mini["daily_cost"]
    savings_monthly = gpt4o["monthly_cost"] - gpt4o_mini["monthly_cost"]
    savings_yearly = gpt4o["yearly_cost"] - gpt4o_mini["yearly_cost"]

    print(f"\ngpt-4o: ${gpt4o['daily_cost']:.2f}/day")
    print(f"gpt-4o-mini: ${gpt4o_mini['daily_cost']:.2f}/day")
    print(f"\nSavings with gpt-4o-mini:")
    print(f"  Daily: ${savings_daily:.2f}")
    print(f"  Monthly: ${savings_monthly:.2f}")
    print(f"  Yearly: ${savings_yearly:.2f}")
    print(f"  Percentage: {(savings_daily/gpt4o['daily_cost']*100):.1f}%")
    print("="*60)


if __name__ == "__main__":
    main()
