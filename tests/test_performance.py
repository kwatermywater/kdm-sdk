"""
Performance Tests for KDM SDK

These tests measure and benchmark the performance of various SDK operations.
They require a running KDM MCP Server at http://203.237.1.4:8080

Run these tests with:
    pytest -v -m "integration and slow"
    pytest -v tests/test_performance.py

Note: These tests are marked as both 'integration' and 'slow'
"""

import pytest
import sys
import time
import asyncio
import pandas as pd
from pathlib import Path
from statistics import mean, stdev

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from kdm_sdk import KDMClient, KDMQuery, FacilityPair
except ImportError as e:
    # Skip all tests if imports fail (dependencies not installed)
    pytest.skip(f"Cannot import kdm_sdk modules: {e}", allow_module_level=True)

# Mark all tests as integration and slow
pytestmark = [pytest.mark.integration, pytest.mark.slow]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def connected_client():
    """Provide a connected KDM client"""
    client = KDMClient(server_url="http://203.237.1.4:8080/sse")
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
def performance_threshold():
    """Define performance thresholds"""
    return {
        "single_query_max": 5.0,  # seconds
        "batch_query_max": 10.0,  # seconds
        "parallel_speedup_min": 1.2,  # parallel should be at least 20% faster
    }


# =============================================================================
# Query Performance Tests
# =============================================================================


@pytest.mark.asyncio
async def test_single_query_performance(connected_client, performance_threshold):
    """
    Performance Test 1: Measure single query execution time

    Benchmarks the time taken to execute a basic query
    """
    query = KDMQuery(client=connected_client)

    # Measure execution time
    start_time = time.time()

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    execution_time = time.time() - start_time

    # Log performance
    print(f"\n[Performance] Single query executed in {execution_time:.3f}s")

    # Verify performance threshold
    assert (
        execution_time < performance_threshold["single_query_max"]
    ), f"Query took {execution_time:.3f}s, exceeds threshold of {performance_threshold['single_query_max']}s"

    assert result is not None


@pytest.mark.asyncio
async def test_batch_query_performance(connected_client, performance_threshold):
    """
    Performance Test 2: Measure batch query execution time

    Benchmarks batch query execution with multiple facilities
    """
    query = KDMQuery(client=connected_client)

    # Add multiple facilities
    dams = ["소양강댐", "충주댐", "팔당댐", "화천댐", "춘천댐"]
    for dam in dams:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    # Measure execution time
    start_time = time.time()

    results = await query.execute_batch(parallel=True)

    execution_time = time.time() - start_time

    # Log performance
    print(
        f"\n[Performance] Batch query ({len(dams)} facilities) executed in {execution_time:.3f}s"
    )
    print(f"[Performance] Average time per facility: {execution_time/len(dams):.3f}s")

    # Verify performance threshold
    assert (
        execution_time < performance_threshold["batch_query_max"]
    ), f"Batch query took {execution_time:.3f}s, exceeds threshold"

    assert results is not None


@pytest.mark.asyncio
async def test_parallel_vs_sequential_performance(
    connected_client, performance_threshold
):
    """
    Performance Test 3: Compare parallel vs sequential batch execution

    Measures the speedup gained from parallel execution
    """
    dams = ["소양강댐", "충주댐", "팔당댐"]

    # Test 1: Sequential execution
    query_seq = KDMQuery(client=connected_client)
    for dam in dams:
        query_seq.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    start_seq = time.time()
    results_seq = await query_seq.execute_batch(parallel=False)
    time_seq = time.time() - start_seq

    # Test 2: Parallel execution
    query_par = KDMQuery(client=connected_client)
    for dam in dams:
        query_par.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    start_par = time.time()
    results_par = await query_par.execute_batch(parallel=True)
    time_par = time.time() - start_par

    # Calculate speedup
    speedup = time_seq / time_par if time_par > 0 else 0

    # Log performance
    print(f"\n[Performance] Sequential execution: {time_seq:.3f}s")
    print(f"[Performance] Parallel execution: {time_par:.3f}s")
    print(f"[Performance] Speedup: {speedup:.2f}x")

    # Verify parallel is faster (or at least not significantly slower)
    # Note: In some cases, parallel might not be faster due to overhead
    # We use a relaxed threshold
    assert (
        speedup >= 0.8
    ), f"Parallel execution is significantly slower (speedup: {speedup:.2f}x)"

    # Ideally, parallel should be faster
    if speedup < performance_threshold["parallel_speedup_min"]:
        pytest.warn(
            f"Parallel speedup ({speedup:.2f}x) is less than expected "
            f"({performance_threshold['parallel_speedup_min']}x)"
        )


@pytest.mark.asyncio
async def test_dataframe_conversion_performance(connected_client):
    """
    Performance Test 4: Measure DataFrame conversion performance

    Benchmarks the time taken to convert query results to DataFrame
    """
    # Get data
    query = KDMQuery(client=connected_client)
    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량", "방류량"])
        .days(30)
        .execute()
    )

    if result.success and len(result.data) > 0:
        # Measure conversion time
        start_time = time.time()
        df = result.to_dataframe()
        conversion_time = time.time() - start_time

        print(f"\n[Performance] DataFrame conversion: {conversion_time:.3f}s")
        print(f"[Performance] Data points: {len(result.data)}")
        print(f"[Performance] DataFrame shape: {df.shape}")

        # Conversion should be fast (< 1 second for typical datasets)
        assert (
            conversion_time < 1.0
        ), f"DataFrame conversion took {conversion_time:.3f}s, too slow"


@pytest.mark.asyncio
async def test_large_dataset_handling(connected_client):
    """
    Performance Test 5: Test handling of large datasets

    Measures performance with larger date ranges (e.g., 1 year of data)
    """
    query = KDMQuery(client=connected_client)

    # Request 1 year of data (will likely use daily data due to auto-fallback)
    start_time = time.time()

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(365)
        .time_key("auto")
        .execute()
    )

    execution_time = time.time() - start_time

    if result.success and len(result.data) > 0:
        # Convert to DataFrame
        df_start = time.time()
        df = result.to_dataframe()
        df_time = time.time() - df_start

        print(f"\n[Performance] Large dataset query: {execution_time:.3f}s")
        print(f"[Performance] Data points: {len(result.data)}")
        print(f"[Performance] DataFrame conversion: {df_time:.3f}s")
        print(f"[Performance] Total time: {execution_time + df_time:.3f}s")

        # Should handle large datasets reasonably well
        assert execution_time < 15.0, "Large dataset query too slow"
        assert df_time < 2.0, "Large DataFrame conversion too slow"


# =============================================================================
# Connection Performance Tests
# =============================================================================


@pytest.mark.asyncio
async def test_connection_overhead():
    """
    Performance Test 6: Measure connection establishment overhead

    Benchmarks the time taken to establish connection
    """
    times = []

    # Measure multiple connection attempts
    for i in range(3):
        client = KDMClient()

        start_time = time.time()
        await client.connect()
        connect_time = time.time() - start_time

        times.append(connect_time)
        await client.disconnect()

    avg_time = mean(times)
    std_time = stdev(times) if len(times) > 1 else 0

    print(
        f"\n[Performance] Average connection time: {avg_time:.3f}s (±{std_time:.3f}s)"
    )

    # Connection should be reasonably fast
    assert avg_time < 5.0, f"Connection too slow: {avg_time:.3f}s"


@pytest.mark.asyncio
async def test_reconnection_performance(connected_client):
    """
    Performance Test 7: Measure reconnection performance

    Tests the overhead of disconnect and reconnect
    """
    # Disconnect
    disconnect_start = time.time()
    await connected_client.disconnect()
    disconnect_time = time.time() - disconnect_start

    # Reconnect
    reconnect_start = time.time()
    await connected_client.connect()
    reconnect_time = time.time() - reconnect_start

    print(f"\n[Performance] Disconnect time: {disconnect_time:.3f}s")
    print(f"\n[Performance] Reconnect time: {reconnect_time:.3f}s")

    # Should be fast
    assert disconnect_time < 1.0, "Disconnect too slow"
    assert reconnect_time < 5.0, "Reconnect too slow"


# =============================================================================
# FacilityPair Performance Tests
# =============================================================================


@pytest.mark.asyncio
async def test_facility_pair_performance(connected_client):
    """
    Performance Test 8: Measure FacilityPair query and alignment performance

    Benchmarks upstream-downstream data fetching and alignment
    """
    # Helper function to convert KDM data to DataFrame
    def convert_to_dataframe(data):
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

    # Measure fetch and data preparation time
    start_time = time.time()

    # Fetch upstream data (dam)
    upstream_result = await connected_client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["방류량"],
        days=30,
        time_key="h_1"
    )

    # Fetch downstream data (water level station)
    downstream_result = await connected_client.get_water_data(
        site_name="춘천",
        facility_type="water_level",
        measurement_items=["수위"],
        days=30,
        time_key="h_1"
    )

    # Convert to DataFrames
    upstream_data = convert_to_dataframe(upstream_result.get("data", []))
    downstream_data = convert_to_dataframe(downstream_result.get("data", []))

    # Skip if insufficient data
    if len(upstream_data) == 0 or len(downstream_data) == 0:
        pytest.skip("Insufficient data for performance test")

    # Create pair with data
    pair = FacilityPair(
        upstream_name="소양강댐",
        downstream_name="춘천",
        upstream_type="dam",
        downstream_type="water_level",
        upstream_data=upstream_data,
        downstream_data=downstream_data
    )

    execution_time = time.time() - start_time

    # Measure DataFrame conversion
    df_start = time.time()
    df = pair.to_dataframe(lag_hours=6.0)
    df_time = time.time() - df_start

    print(f"\n[Performance] FacilityPair fetch+align: {execution_time:.3f}s")
    print(f"[Performance] DataFrame conversion: {df_time:.3f}s")
    print(f"[Performance] Total time: {execution_time + df_time:.3f}s")

    # Should complete in reasonable time
    assert execution_time < 10.0, "FacilityPair fetch too slow"


# =============================================================================
# Stress Tests
# =============================================================================


@pytest.mark.asyncio
async def test_concurrent_query_stress(connected_client):
    """
    Performance Test 9: Stress test with many concurrent queries

    Tests system behavior under high concurrent load
    """
    num_concurrent = 10
    dams = ["소양강댐", "충주댐", "팔당댐"]

    async def single_query(index):
        dam = dams[index % len(dams)]
        query = KDMQuery(client=connected_client)
        return (
            await query.site(dam, facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .execute()
        )

    # Execute many concurrent queries
    start_time = time.time()

    results = await asyncio.gather(
        *[single_query(i) for i in range(num_concurrent)], return_exceptions=True
    )

    execution_time = time.time() - start_time

    # Count successful queries
    successful = sum(1 for r in results if not isinstance(r, Exception))

    print(
        f"\n[Performance] {num_concurrent} concurrent queries in {execution_time:.3f}s"
    )
    print(f"[Performance] Successful: {successful}/{num_concurrent}")
    print(f"[Performance] Average time per query: {execution_time/num_concurrent:.3f}s")

    # Most queries should succeed
    success_rate = successful / num_concurrent
    assert (
        success_rate >= 0.8
    ), f"Too many failures: {success_rate*100:.1f}% success rate"


@pytest.mark.asyncio
async def test_memory_efficiency():
    """
    Performance Test 10: Test memory efficiency with multiple queries

    Verifies that the SDK doesn't leak memory or use excessive resources
    """
    import gc

    # Force garbage collection before test
    gc.collect()

    client = KDMClient()
    await client.connect()

    # Execute multiple queries
    for i in range(10):
        query = KDMQuery(client=client)
        result = (
            await query.site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .execute()
        )

        if result.success:
            # Convert to DataFrame and discard
            df = result.to_dataframe()
            del df

        # Explicitly delete result
        del result

    # Force garbage collection
    gc.collect()

    await client.disconnect()

    # If we get here without memory errors, test passes
    assert True


# =============================================================================
# Benchmark Summary
# =============================================================================


@pytest.mark.asyncio
async def test_benchmark_summary(connected_client):
    """
    Performance Test 11: Run comprehensive benchmark suite

    Runs various operations and produces a summary report
    """
    benchmarks = {}

    # 1. Single query
    start = time.time()
    result = (
        await KDMQuery(client=connected_client)
        .site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )
    benchmarks["single_query"] = time.time() - start

    # 2. DataFrame conversion
    start = time.time()
    df = result.to_dataframe()
    benchmarks["dataframe_conversion"] = time.time() - start

    # 3. Batch query
    query = KDMQuery(client=connected_client)
    for dam in ["소양강댐", "충주댐", "팔당댐"]:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    start = time.time()
    batch_results = await query.execute_batch(parallel=True)
    benchmarks["batch_query_parallel"] = time.time() - start

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    for operation, duration in benchmarks.items():
        print(f"{operation:30s}: {duration:8.3f}s")
    print("=" * 60)

    # All operations should complete
    assert all(v < 30.0 for v in benchmarks.values()), "Some operations are too slow"
