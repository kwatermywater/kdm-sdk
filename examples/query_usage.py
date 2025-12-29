#!/usr/bin/env python3
"""
KDM Query Builder Usage Examples

This script demonstrates how to use the Fluent API query builder
to fetch and analyze KDM water resource data.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kdm_sdk import KDMQuery


async def example_basic_query():
    """Example 1: Basic query with fluent API"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Query")
    print("=" * 60)

    query = KDMQuery()

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량"])
        .days(7)
        .execute()
    )

    print(f"Query successful: {result.success}")
    print(f"Site: {result.site_name}")
    print(f"Records: {len(result)}")

    if result.success and len(result) > 0:
        # Convert to DataFrame
        df = result.to_dataframe()
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nFirst few rows:")
        print(df.head())


async def example_date_range_query():
    """Example 2: Query with specific date range"""
    print("\n" + "=" * 60)
    print("Example 2: Date Range Query")
    print("=" * 60)

    query = KDMQuery()

    result = (
        await query.site("충주댐", facility_type="dam")
        .measurements(["저수율"])
        .date_range(start_date="2024-01-01", end_date="2024-01-07")
        .time_key("d_1")
        .execute()
    )

    print(f"Query successful: {result.success}")
    print(f"Records: {len(result)}")

    if result.success:
        data_list = result.to_list()
        print(f"\nSample data:")
        for record in data_list[:3]:
            print(f"  {record}")


async def example_year_over_year_comparison():
    """Example 3: Year-over-year comparison"""
    print("\n" + "=" * 60)
    print("Example 3: Year-over-Year Comparison")
    print("=" * 60)

    query = KDMQuery()

    result = (
        await query.site("팔당댐", facility_type="dam")
        .measurements(["저수율"])
        .date_range(start_date="2024-06-01", end_date="2024-06-30")
        .compare_with_previous_year()
        .execute()
    )

    print(f"Query successful: {result.success}")
    print(f"Records: {len(result)}")

    if result.comparison_data:
        print(f"\nComparison data available:")
        print(f"  Current year: {result.comparison_data.get('current_year')}")
        print(f"  Previous year: {result.comparison_data.get('previous_year')}")


async def example_batch_query():
    """Example 4: Batch query for multiple facilities"""
    print("\n" + "=" * 60)
    print("Example 4: Batch Query")
    print("=" * 60)

    query = KDMQuery()

    # Add multiple facilities to batch
    dams = ["소양강댐", "충주댐", "팔당댐"]

    for dam in dams:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    # Execute all queries
    results = await query.execute_batch()

    print(f"Batch size: {len(results)}")
    print(f"\nResults:")

    for site_name, result in results:
        status = "✓" if result.success else "✗"
        print(f"  {status} {site_name}: {len(result)} records")


async def example_batch_parallel():
    """Example 5: Parallel batch execution"""
    print("\n" + "=" * 60)
    print("Example 5: Parallel Batch Execution")
    print("=" * 60)

    query = KDMQuery()

    # Add multiple facilities
    dams = ["소양강댐", "충주댐", "팔당댐", "대청댐", "안동댐"]

    for dam in dams:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    # Execute in parallel for better performance
    import time

    start_time = time.time()

    results = await query.execute_batch(parallel=True)

    elapsed = time.time() - start_time

    print(f"Batch size: {len(results)}")
    print(f"Execution time: {elapsed:.2f}s")
    print(f"\nResults:")

    for site_name, result in results:
        status = "✓" if result.success else "✗"
        print(f"  {status} {site_name}: {len(result)} records")


async def example_aggregate_results():
    """Example 6: Aggregate batch results into single DataFrame"""
    print("\n" + "=" * 60)
    print("Example 6: Aggregate Batch Results")
    print("=" * 60)

    query = KDMQuery()

    # Add multiple facilities
    for dam in ["소양강댐", "충주댐", "팔당댐"]:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    results = await query.execute_batch()

    # Aggregate all results into single DataFrame
    combined_df = results.aggregate()

    print(f"Combined DataFrame shape: {combined_df.shape}")
    print(f"Columns: {list(combined_df.columns)}")

    if len(combined_df) > 0:
        print(f"\nSample of combined data:")
        print(combined_df.head(10))

        # Group by site
        if "site_name" in combined_df.columns and "저수율" in combined_df.columns:
            print(f"\nAverage 저수율 by site:")
            avg_by_site = combined_df.groupby("site_name")["저수율"].mean()
            print(avg_by_site)


async def example_with_options():
    """Example 7: Query with additional data options"""
    print("\n" + "=" * 60)
    print("Example 7: Query with Additional Options")
    print("=" * 60)

    query = KDMQuery()

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .include_comparison()
        .include_weather()
        .include_related()
        .execute()
    )

    print(f"Query successful: {result.success}")
    print(f"Records: {len(result)}")

    if result.success:
        print(f"Metadata keys: {list(result.metadata.keys())}")


async def example_error_handling():
    """Example 8: Error handling"""
    print("\n" + "=" * 60)
    print("Example 8: Error Handling")
    print("=" * 60)

    query = KDMQuery()

    # Query non-existent facility
    result = (
        await query.site("존재하지않는댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    print(f"Query successful: {result.success}")
    print(f"Message: {result.message}")

    if not result.success:
        print("Query failed as expected (facility not found)")


async def example_data_conversion():
    """Example 9: Data conversion methods"""
    print("\n" + "=" * 60)
    print("Example 9: Data Conversion Methods")
    print("=" * 60)

    query = KDMQuery()

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    if result.success and len(result) > 0:
        # Convert to different formats
        print("1. to_dict():")
        result_dict = result.to_dict()
        print(f"   Keys: {list(result_dict.keys())}")

        print("\n2. to_list():")
        result_list = result.to_list()
        print(f"   Length: {len(result_list)}")
        print(f"   First item: {result_list[0] if result_list else 'None'}")

        print("\n3. to_dataframe():")
        df = result.to_dataframe()
        print(f"   Shape: {df.shape}")
        print(f"   Data types:\n{df.dtypes}")


async def example_query_clone():
    """Example 10: Clone and modify query"""
    print("\n" + "=" * 60)
    print("Example 10: Clone Query")
    print("=" * 60)

    # Create base query
    base_query = KDMQuery()
    base_query.measurements(["저수율"]).days(7)

    # Clone for different facilities
    query1 = base_query.clone().site("소양강댐", facility_type="dam")
    query2 = base_query.clone().site("충주댐", facility_type="dam")

    result1 = await query1.execute()
    result2 = await query2.execute()

    print(f"Query 1 ({result1.site_name}): {len(result1)} records")
    print(f"Query 2 ({result2.site_name}): {len(result2)} records")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("KDM Query Builder Examples")
    print("=" * 60)

    # Run examples
    await example_basic_query()
    await example_date_range_query()
    await example_year_over_year_comparison()
    await example_batch_query()
    await example_batch_parallel()
    await example_aggregate_results()
    await example_with_options()
    await example_error_handling()
    await example_data_conversion()
    await example_query_clone()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
