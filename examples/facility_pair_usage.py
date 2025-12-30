"""
Example: Analyzing Dam-Downstream Relationships using FacilityPair

This example demonstrates how to use FacilityPair to analyze the relationship
between a dam's outflow and downstream water level changes.

Scenario:
    소양강댐 (Soyang Dam) releases water → affects 춘천 (Chuncheon) water level station
    Question: How long does it take for released water to reach the monitoring station?
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kdm_sdk import KDMClient, FacilityPair


async def example_with_real_data():
    """
    Example using real KDM data (requires running MCP server)
    """
    print("=" * 60)
    print("Example 1: Analyzing Real Dam-Downstream Relationship")
    print("=" * 60)

    # Initialize KDM client
    client = KDMClient()  # Uses default: http://203.237.1.4:8080/sse

    try:
        # Connect to server
        await client.connect()
        print("\nConnected to KDM MCP Server")

        # Get dam outflow data (방류량)
        print("\nFetching 소양강댐 outflow data...")
        dam_result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["방류량"],
            days=7,
            time_key="h_1",  # Hourly data
        )

        # Get downstream water level data
        print("Fetching 춘천 water level data...")
        station_result = await client.get_water_data(
            site_name="춘천",
            facility_type="water_level",
            measurement_items=["수위"],
            days=7,
            time_key="h_1",
        )

        # Convert to DataFrames
        dam_df = convert_kdm_to_dataframe(dam_result["data"])
        station_df = convert_kdm_to_dataframe(station_result["data"])

        print(f"\nDam data: {len(dam_df)} rows")
        print(f"Station data: {len(station_df)} rows")

        # Create FacilityPair
        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_type="dam",
            downstream_type="water_level",
            upstream_data=dam_df,
            downstream_data=station_df,
        )

        print(f"\nCreated: {pair}")

        # Find optimal lag
        print("\nSearching for optimal lag (0-12 hours)...")
        result = pair.find_optimal_lag(max_lag_hours=12, step_hours=0.5)

        print(f"\nResults:")
        print(f"  Optimal lag: {result.lag_hours:.1f} hours")
        print(f"  Correlation: {result.correlation:.3f}")
        print(f"  Sample size: {result.sample_size}")
        print(f"\nInterpretation:")
        print(f"  Water released from 소양강댐 takes approximately")
        print(f"  {result.lag_hours:.1f} hours to reach 춘천 monitoring station")

        # Export aligned data
        df = pair.to_dataframe(lag_hours=result.lag_hours)
        output_file = "soyang_chuncheon_aligned.csv"
        df.to_csv(output_file)
        print(f"\nAligned data exported to: {output_file}")

        # Test different lags
        print("\nTesting correlations at different lags:")
        for lag in [0, 2, 4, 6, 8]:
            r = pair.calculate_correlation(lag_hours=lag)
            print(f"  Lag {lag:2d}h: correlation = {r.correlation:+.3f}")

    finally:
        await client.disconnect()
        print("\nDisconnected from server")


def example_with_synthetic_data():
    """
    Example using synthetic data to demonstrate lag detection
    """
    print("\n" + "=" * 60)
    print("Example 2: Lag Detection with Synthetic Data")
    print("=" * 60)

    # Generate synthetic data with known 3-hour lag
    print("\nGenerating synthetic data with 3-hour lag...")

    dates = pd.date_range("2024-01-01", periods=7 * 24, freq="h")

    # Upstream: Daily pattern (high during day, low at night)
    hour_of_day = dates.hour
    upstream_values = 100 + 50 * np.sin((hour_of_day - 6) * np.pi / 12)

    # Downstream: Same pattern but delayed by 3 hours + noise
    downstream_values = (
        100
        + 50 * np.sin((hour_of_day - 9) * np.pi / 12)
        + np.random.normal(0, 5, len(dates))
    )

    # Create DataFrames
    upstream_df = pd.DataFrame({"방류량": upstream_values}, index=dates)
    downstream_df = pd.DataFrame({"수위": downstream_values}, index=dates)

    print(f"Created {len(dates)} hours of synthetic data")

    # Create FacilityPair
    pair = FacilityPair(
        upstream_name="가상댐",
        downstream_name="하류관측소",
        upstream_type="dam",
        downstream_type="water_level",
        upstream_data=upstream_df,
        downstream_data=downstream_df,
    )

    # Find optimal lag
    print("\nSearching for optimal lag...")
    result = pair.find_optimal_lag(max_lag_hours=10, step_hours=0.5)

    print(f"\nResults:")
    print(f"  True lag: 3.0 hours")
    print(f"  Detected lag: {result.lag_hours:.1f} hours")
    print(f"  Correlation: {result.correlation:.3f}")
    print(f"  Accuracy: {'✓ GOOD' if abs(result.lag_hours - 3.0) <= 1.0 else '✗ POOR'}")

    # Compare correlations at different lags
    print("\nCorrelation vs Lag:")
    print("  Lag (h)  Correlation")
    print("  -------  -----------")
    for lag in np.arange(0, 8, 0.5):
        r = pair.calculate_correlation(lag_hours=lag)
        marker = " ◄◄◄ PEAK" if abs(lag - result.lag_hours) < 0.1 else ""
        print(f"    {lag:4.1f}      {r.correlation:+.3f}{marker}")


def example_multiple_measurements():
    """
    Example with multiple measurement items
    """
    print("\n" + "=" * 60)
    print("Example 3: Multiple Measurement Items")
    print("=" * 60)

    # Generate data with multiple measurements
    dates = pd.date_range("2024-01-01", periods=30 * 24, freq="h")

    # Dam: outflow and storage rate
    upstream_df = pd.DataFrame(
        {
            "방류량": 100 + 50 * np.sin(np.arange(len(dates)) * 0.01),
            "저수율": 70 + 20 * np.sin(np.arange(len(dates)) * 0.005),
        },
        index=dates,
    )

    # Station: water level and flow
    downstream_df = pd.DataFrame(
        {
            "수위": 5 + 2 * np.sin((np.arange(len(dates)) - 24) * 0.01),
            "유량": 200 + 100 * np.sin((np.arange(len(dates)) - 24) * 0.01),
        },
        index=dates,
    )

    pair = FacilityPair(
        upstream_name="다목적댐",
        downstream_name="하류지점",
        upstream_data=upstream_df,
        downstream_data=downstream_df,
    )

    print("\nAnalyzing different measurement combinations:")

    # Test different combinations
    combinations = [
        ("방류량", "수위", "방류량 → 수위"),
        ("방류량", "유량", "방류량 → 유량"),
        ("저수율", "수위", "저수율 → 수위"),
    ]

    for upstream_col, downstream_col, description in combinations:
        result = pair.find_optimal_lag(
            max_lag_hours=48,
            upstream_column=upstream_col,
            downstream_column=downstream_col,
        )
        print(f"\n{description}:")
        print(f"  Best lag: {result.lag_hours:.1f}h")
        print(f"  Correlation: {result.correlation:.3f}")


def convert_kdm_to_dataframe(data):
    """
    Helper function to convert KDM API response to DataFrame

    Args:
        data: List of data points from KDM API

    Returns:
        DataFrame with datetime index
    """
    records = []
    for item in data:
        record = {"datetime": item.get("datetime")}
        if "values" in item:
            for key, val in item["values"].items():
                record[key] = val.get("value")
        records.append(record)

    df = pd.DataFrame(records)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)

    return df


def main():
    """
    Run all examples
    """
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  KDM SDK - FacilityPair Usage Examples".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")

    # Example with synthetic data (always works)
    example_with_synthetic_data()
    example_multiple_measurements()

    # Example with real data (requires running MCP server)
    print("\n" + "=" * 60)
    print("Example with Real KDM Data")
    print("=" * 60)
    print("\nTo run the real data example, ensure:")
    print("  1. KDM MCP Server is running on http://203.237.1.4:8080")
    print("  2. Uncomment the line below:")
    print("\n# asyncio.run(example_with_real_data())")

    # Uncomment to run with real data:
    # asyncio.run(example_with_real_data())

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
