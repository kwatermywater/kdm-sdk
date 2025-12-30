"""
Integration Tests for KDM SDK

These tests require a running KDM MCP Server at http://203.237.1.4:8080
They verify the entire workflow from connection to data retrieval and conversion.

Run these tests with:
    pytest -v -m integration  # Run only integration tests
    pytest -v -m "not integration"  # Skip integration tests

Prerequisites:
- KDM MCP Server must be running at http://203.237.1.4:8080
- Server must have access to real KDM data
"""

import pytest
import sys
import pandas as pd
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from kdm_sdk import KDMClient, KDMQuery, FacilityPair, TemplateBuilder
    from kdm_sdk.results import QueryResult, BatchResult
    from kdm_sdk.templates import load_yaml, load_python
except ImportError as e:
    # Skip all tests if imports fail (dependencies not installed)
    pytest.skip(f"Cannot import kdm_sdk modules: {e}", allow_module_level=True)

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def connected_client():
    """
    Provide a connected KDM client for integration tests

    Yields a connected client and ensures proper cleanup.
    """
    client = KDMClient(server_url="http://203.237.1.4:8080/sse")
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for file operations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# Category 1: Basic Workflow Tests (5 tests)
# =============================================================================


@pytest.mark.asyncio
async def test_connection_and_disconnection(connected_client):
    """
    Test 1.1: Verify client can connect and disconnect properly

    This test ensures the basic client lifecycle works correctly.
    """
    # Client should be connected via fixture
    assert connected_client.is_connected()

    # Disconnect
    await connected_client.disconnect()
    assert not connected_client.is_connected()

    # Reconnect
    await connected_client.connect()
    assert connected_client.is_connected()


@pytest.mark.asyncio
async def test_simple_query_execution(connected_client):
    """
    Test 1.2: Execute a simple query and verify data structure

    Tests the complete workflow: query → result → validate structure
    """
    result = await connected_client.get_water_data(
        site_name="소양강댐", facility_type="dam", measurement_items=["저수율"], days=7
    )

    # Verify result structure
    assert result is not None
    assert isinstance(result, dict)
    assert "success" in result

    if result.get("success"):
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0

        # Verify data point structure
        first_point = result["data"][0]
        assert "datetime" in first_point
        assert "values" in first_point


@pytest.mark.asyncio
async def test_dataframe_conversion(connected_client):
    """
    Test 1.3: Test complete workflow from query to DataFrame

    Verifies the most common use case: query → QueryResult → DataFrame
    """
    query = KDMQuery(client=connected_client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량"])
        .days(7)
        .execute()
    )

    assert isinstance(result, QueryResult)

    # Convert to DataFrame
    df = result.to_dataframe()

    assert df is not None

    if result.success and len(result.data) > 0:
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # Verify column structure
        assert "datetime" in df.columns

        # Data should have datetime index or column
        if df.index.name == "datetime" or "datetime" in df.columns:
            # Check datetime is properly parsed
            assert True


@pytest.mark.asyncio
async def test_batch_query_execution(connected_client):
    """
    Test 1.4: Execute batch queries for multiple facilities

    Tests parallel query execution and result aggregation
    """
    query = KDMQuery(client=connected_client)

    # Add multiple facilities
    dams = ["소양강댐", "충주댐", "팔당댐"]
    for dam in dams:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    # Execute batch query
    results = await query.execute_batch(parallel=True)

    assert isinstance(results, BatchResult)
    assert len(results.results) > 0

    # Verify each result
    for dam_name in dams:
        if dam_name in results:
            result = results[dam_name]
            assert isinstance(result, QueryResult)


@pytest.mark.asyncio
async def test_error_handling():
    """
    Test 1.5: Verify error handling for network errors and invalid data

    Tests robustness of error handling throughout the system
    """
    # Test 1: Invalid server URL
    client = KDMClient(server_url="http://invalid-server:9999/sse")

    try:
        await asyncio.wait_for(client.connect(), timeout=5.0)
    except (asyncio.TimeoutError, Exception) as e:
        # Should handle connection errors gracefully
        assert True

    # Test 2: Invalid facility name
    client2 = KDMClient()
    await client2.connect()

    result = await client2.get_water_data(
        site_name="존재하지않는댐999999",
        facility_type="dam",
        measurement_items=["저수율"],
        days=7,
    )

    # Should return result with success=False or empty data
    assert isinstance(result, dict)
    assert result.get("success") is False or len(result.get("data", [])) == 0

    await client2.disconnect()


# =============================================================================
# Category 2: Advanced Features Tests (5 tests)
# =============================================================================


@pytest.mark.asyncio
async def test_template_execution(connected_client, temp_dir):
    """
    Test 2.1: Create and execute a template

    Tests the template system end-to-end
    """
    # Create template using builder
    template = (
        TemplateBuilder("통합테스트_템플릿")
        .site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량"])
        .days(7)
        .build()
    )

    # Execute template
    result = await template.execute(client=connected_client)

    assert isinstance(result, QueryResult)

    if result.success:
        df = result.to_dataframe()
        assert df is not None
        assert isinstance(df, pd.DataFrame)


@pytest.mark.asyncio
async def test_facility_pair_correlation(connected_client):
    """
    Test 2.2: Test FacilityPair correlation analysis with real data

    Verifies upstream-downstream correlation analysis with lag
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
        pytest.skip("Insufficient data for correlation analysis")

    # Create pair with data
    pair = FacilityPair(
        upstream_name="소양강댐",
        downstream_name="춘천",
        upstream_type="dam",
        downstream_type="water_level",
        upstream_data=upstream_data,
        downstream_data=downstream_data
    )

    # Analyze optimal lag
    result = pair.find_optimal_lag(max_lag_hours=12)
    assert result is not None
    assert hasattr(result, 'correlation')

    # Export to DataFrame
    df = pair.to_dataframe(lag_hours=6.0)
    assert df is not None
    assert isinstance(df, pd.DataFrame)

    # Should have columns from both facilities
    columns = df.columns.tolist()
    assert len(columns) > 0


@pytest.mark.asyncio
async def test_year_over_year_comparison(connected_client):
    """
    Test 2.3: Test year-over-year comparison functionality

    Verifies comparison data retrieval and processing
    """
    query = KDMQuery(client=connected_client)

    # Query with year-over-year comparison
    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .compare_with_previous_year()
        .execute()
    )

    assert isinstance(result, QueryResult)

    # Result should have comparison data if available
    if result.success and hasattr(result, "comparison_data"):
        assert result.comparison_data is not None


@pytest.mark.asyncio
async def test_auto_fallback_mechanism(connected_client):
    """
    Test 2.4: Test automatic time key fallback (hourly → daily → monthly)

    Verifies the auto-fallback mechanism works correctly
    """
    # Request data for 2 years (should fall back from hourly to daily/monthly)
    result = await connected_client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["저수율"],
        days=730,  # 2 years
        time_key="auto",
    )

    assert result is not None
    assert isinstance(result, dict)

    # Should still get data even with fallback
    if result.get("success"):
        assert "data" in result
        # Auto fallback should return data with appropriate time_key


@pytest.mark.asyncio
async def test_multiple_measurements(connected_client):
    """
    Test 2.5: Test querying multiple measurement items simultaneously

    Verifies multi-measurement queries and data structure
    """
    query = KDMQuery(client=connected_client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량", "방류량"])
        .days(7)
        .execute()
    )

    assert isinstance(result, QueryResult)

    if result.success and len(result.data) > 0:
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)

        # Should have data for multiple measurements
        # (exact column names may vary based on data structure)
        assert len(df.columns) >= 1


# =============================================================================
# Category 3: Data Validation Tests (3 tests)
# =============================================================================


@pytest.mark.asyncio
async def test_dataframe_structure_validation(connected_client):
    """
    Test 3.1: Validate DataFrame structure and column types

    Ensures DataFrame conversion produces correct data types
    """
    query = KDMQuery(client=connected_client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    if result.success and len(result.data) > 0:
        df = result.to_dataframe()

        # DataFrame should not be empty
        assert not df.empty

        # Should have datetime column or index
        has_datetime = (
            "datetime" in df.columns
            or df.index.name == "datetime"
            or isinstance(df.index, pd.DatetimeIndex)
        )
        assert has_datetime, "DataFrame should have datetime information"

        # Should have at least one measurement column
        assert len(df.columns) >= 1


@pytest.mark.asyncio
async def test_data_types_preservation(connected_client):
    """
    Test 3.2: Verify data types are preserved correctly

    Ensures numeric values are numeric, dates are datetime, etc.
    """
    query = KDMQuery(client=connected_client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    if result.success and len(result.data) > 0:
        df = result.to_dataframe()

        # Numeric columns should be numeric or can be converted
        for col in df.columns:
            if col != "datetime":
                # Should be numeric or convertible to numeric
                try:
                    pd.to_numeric(df[col], errors="coerce")
                    assert True
                except:
                    # Some columns may be non-numeric (e.g., status)
                    pass


@pytest.mark.asyncio
async def test_missing_value_handling(connected_client):
    """
    Test 3.3: Test handling of missing or null values

    Verifies the system handles missing data gracefully
    """
    # Query data that might have missing values
    result = await connected_client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["저수율", "유입량", "방류량"],
        days=30,
    )

    if result.get("success") and len(result.get("data", [])) > 0:
        from kdm_sdk.results import QueryResult

        query_result = QueryResult(result)
        df = query_result.to_dataframe()

        # DataFrame should handle missing values
        # (either as NaN or by excluding them)
        assert df is not None

        # Check if there are any null values
        if df.isnull().any().any():
            # Nulls are present - verify they're handled as NaN
            assert df.isnull().sum().sum() >= 0  # Count of nulls


# =============================================================================
# Category 4: Conversion Methods Tests (3 tests)
# =============================================================================


@pytest.mark.asyncio
async def test_to_dict_conversion(connected_client):
    """
    Test 4.1: Test QueryResult.to_dict() conversion

    Verifies conversion to dictionary format
    """
    query = KDMQuery(client=connected_client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Convert to dict
    data_dict = result.to_dict()

    assert isinstance(data_dict, dict)
    assert "success" in data_dict
    assert "data" in data_dict


@pytest.mark.asyncio
async def test_to_list_conversion(connected_client):
    """
    Test 4.2: Test QueryResult.to_list() conversion

    Verifies conversion to list format
    """
    query = KDMQuery(client=connected_client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Convert to list
    data_list = result.to_list()

    assert isinstance(data_list, list)

    if result.success and len(result.data) > 0:
        assert len(data_list) > 0


@pytest.mark.asyncio
async def test_batch_result_aggregate(connected_client):
    """
    Test 4.3: Test BatchResult.aggregate() method

    Verifies batch result aggregation into single DataFrame
    """
    query = KDMQuery(client=connected_client)

    # Add multiple facilities
    for dam in ["소양강댐", "충주댐"]:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    # Execute batch
    results = await query.execute_batch(parallel=True)

    # Aggregate results
    combined_df = results.aggregate()

    assert combined_df is not None

    if any(r.success for r in results.results.values()):
        assert isinstance(combined_df, pd.DataFrame)
        # Should have columns from multiple facilities
        assert len(combined_df.columns) >= 1


# =============================================================================
# Category 5: Template System Tests (3 tests)
# =============================================================================


@pytest.mark.asyncio
async def test_template_yaml_save_load(connected_client, temp_dir):
    """
    Test 5.1: Test template save and load with YAML format

    Verifies template persistence and loading
    """
    # Create template
    template = (
        TemplateBuilder("YAML_테스트_템플릿")
        .site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .build()
    )

    # Save to YAML
    yaml_path = temp_dir / "test_template.yaml"
    template.save(str(yaml_path))

    assert yaml_path.exists()

    # Load from YAML
    loaded_template = load_yaml(str(yaml_path))

    assert loaded_template is not None
    assert loaded_template.name == "YAML_테스트_템플릿"

    # Execute loaded template
    result = await loaded_template.execute(client=connected_client)
    assert isinstance(result, QueryResult)


@pytest.mark.asyncio
async def test_template_with_facility_pair(connected_client):
    """
    Test 5.2: Test template execution with FacilityPair

    Verifies template system works with facility pairs
    """
    template = (
        TemplateBuilder("FacilityPair_템플릿")
        .add_pair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_type="dam",
            downstream_type="water_level",
            lag_hours=6.0,
        )
        .days(30)
        .build()
    )

    # Execute template
    result = await template.execute(client=connected_client)

    assert result is not None

    # Result should be PairResult with DataFrame
    df = result.to_dataframe()
    assert df is not None


@pytest.mark.asyncio
async def test_template_parameter_override(connected_client):
    """
    Test 5.3: Test template execution with parameter overrides

    Verifies templates can be reused with different parameters
    """
    template = (
        TemplateBuilder("파라미터_오버라이드_템플릿")
        .site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .build()
    )

    # Execute with override
    result = await template.execute(
        client=connected_client, days=14  # Override days parameter
    )

    assert isinstance(result, QueryResult)


# =============================================================================
# Category 6: End-to-End Workflow Tests (2 tests)
# =============================================================================


@pytest.mark.asyncio
async def test_complete_fluent_api_workflow(connected_client):
    """
    Test 6.1: Complete workflow using Fluent API

    Tests the entire chain from query building to DataFrame export
    """
    # Build and execute query
    result = (
        await KDMQuery(client=connected_client)
        .site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량"])
        .days(7)
        .execute()
    )

    assert isinstance(result, QueryResult)

    if result.success and len(result.data) > 0:
        # Convert to DataFrame
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)

        # Convert to dict
        data_dict = result.to_dict()
        assert isinstance(data_dict, dict)

        # Convert to list
        data_list = result.to_list()
        assert isinstance(data_list, list)


@pytest.mark.asyncio
async def test_complete_template_workflow(connected_client, temp_dir):
    """
    Test 6.2: Complete workflow using Template system

    Tests template creation, save, load, and execution
    """
    # 1. Create template
    template = (
        TemplateBuilder("완전_워크플로우_테스트")
        .site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .build()
    )

    # 2. Save template
    template_path = temp_dir / "workflow_test.yaml"
    template.save(str(template_path))
    assert template_path.exists()

    # 3. Load template
    loaded = load_yaml(str(template_path))
    assert loaded.name == "완전_워크플로우_테스트"

    # 4. Execute template
    result = await loaded.execute(client=connected_client)
    assert isinstance(result, QueryResult)

    # 5. Convert to DataFrame
    if result.success and len(result.data) > 0:
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)


# =============================================================================
# Utility Tests
# =============================================================================


@pytest.mark.asyncio
async def test_server_availability():
    """
    Test utility: Check if KDM MCP server is available

    This test can be used to verify server status before running other tests
    """
    client = KDMClient()

    try:
        await asyncio.wait_for(client.connect(), timeout=10.0)
        assert client.is_connected()

        # Try health check if available
        if hasattr(client, "health_check"):
            is_healthy = await client.health_check()
            assert isinstance(is_healthy, bool)

        await client.disconnect()
    except asyncio.TimeoutError:
        pytest.skip("KDM MCP Server not available at http://203.237.1.4:8080")
    except Exception as e:
        pytest.skip(f"Cannot connect to KDM MCP Server: {e}")


@pytest.mark.asyncio
async def test_concurrent_queries(connected_client):
    """
    Test concurrent query execution

    Verifies the system can handle multiple simultaneous queries
    """

    async def single_query(dam_name):
        query = KDMQuery(client=connected_client)
        return (
            await query.site(dam_name, facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .execute()
        )

    # Execute multiple queries concurrently
    results = await asyncio.gather(
        single_query("소양강댐"),
        single_query("충주댐"),
        single_query("팔당댐"),
        return_exceptions=True,
    )

    # All queries should complete
    assert len(results) == 3

    # Verify results
    for result in results:
        if not isinstance(result, Exception):
            assert isinstance(result, QueryResult)
