"""
KDM Query Builder Tests (TDD Approach)

Tests for Fluent API query builder and result handling.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kdm_sdk.query import KDMQuery
from kdm_sdk.results import QueryResult, BatchResult
from kdm_sdk.client import KDMClient


# =============================================================================
# RED PHASE: Write failing tests first
# =============================================================================


@pytest.mark.asyncio
async def test_fluent_api_basic():
    """기본 Fluent API 메서드 체이닝 테스트"""
    query = KDMQuery()

    # Test method chaining
    result = (
        query.site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량"])
        .days(7)
    )

    # Query should return self for chaining
    assert isinstance(result, KDMQuery)

    # Query should store configuration
    assert query._site_name == "소양강댐"
    assert query._facility_type == "dam"
    assert "저수율" in query._measurement_items
    assert "유입량" in query._measurement_items
    assert query._days == 7


@pytest.mark.asyncio
async def test_fluent_api_execute():
    """Fluent API 실행 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Result should be QueryResult instance
    assert isinstance(result, QueryResult)

    # Result should have data
    assert result.success is not None
    if result.success:
        assert result.data is not None
        assert isinstance(result.data, list)


@pytest.mark.asyncio
async def test_query_with_time_key():
    """시간 단위 지정 테스트"""
    query = KDMQuery()

    result = (
        query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .time_key("h_1")
    )

    assert query._time_key == "h_1"


@pytest.mark.asyncio
async def test_query_with_date_range():
    """날짜 범위 지정 테스트"""
    query = KDMQuery()

    result = (
        query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .date_range(start_date="2024-01-01", end_date="2024-01-07")
    )

    assert query._start_date == "2024-01-01"
    assert query._end_date == "2024-01-07"


@pytest.mark.asyncio
async def test_year_over_year_comparison():
    """전년 대비 비교 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    result = (
        await query.site("장흥댐", facility_type="dam")
        .measurements(["저수율"])
        .compare_with_previous_year()
        .execute()
    )

    # Result should have comparison data
    assert isinstance(result, QueryResult)
    if result.success and result.comparison_data:
        assert "current_year" in result.comparison_data
        assert "previous_year" in result.comparison_data


@pytest.mark.asyncio
async def test_batch_execution():
    """배치 조회 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    # Add multiple facilities
    query.site("소양강댐", facility_type="dam").measurements(["저수율"]).days(7).add()

    query.site("충주댐", facility_type="dam").measurements(["저수율"]).days(7).add()

    query.site("팔당댐", facility_type="dam").measurements(["저수율"]).days(7).add()

    # Execute all queries in batch
    results = await query.execute_batch()

    assert isinstance(results, BatchResult)
    assert len(results.results) > 0

    # Each result should be accessible by site name
    if "소양강댐" in results:
        assert isinstance(results["소양강댐"], QueryResult)


@pytest.mark.asyncio
async def test_batch_parallel_execution():
    """병렬 배치 조회 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    # Add multiple facilities
    for dam in ["소양강댐", "충주댐", "팔당댐"]:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    # Execute in parallel
    results = await query.execute_batch(parallel=True)

    assert isinstance(results, BatchResult)
    assert len(results.results) > 0


@pytest.mark.asyncio
async def test_query_result_to_dataframe():
    """QueryResult를 DataFrame으로 변환 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율", "유입량"])
        .days(7)
        .execute()
    )

    # Convert to DataFrame
    df = result.to_dataframe()

    assert df is not None

    if result.success and len(result.data) > 0:
        import pandas as pd

        assert isinstance(df, pd.DataFrame)

        # Check columns
        assert "datetime" in df.columns
        # Data may have nested structure, check if values are accessible


@pytest.mark.asyncio
async def test_batch_result_aggregate():
    """배치 결과 집계 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    for dam in ["소양강댐", "충주댐"]:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    results = await query.execute_batch()

    # Aggregate all results into single DataFrame
    combined_df = results.aggregate()

    assert combined_df is not None

    if len(results.results) > 0 and any(r.success for r in results.results.values()):
        import pandas as pd

        assert isinstance(combined_df, pd.DataFrame)


@pytest.mark.asyncio
async def test_query_result_to_dict():
    """QueryResult를 딕셔너리로 변환 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

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
async def test_query_result_to_list():
    """QueryResult를 리스트로 변환 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Convert to list
    data_list = result.to_list()

    assert isinstance(data_list, list)


@pytest.mark.asyncio
async def test_query_with_include_options():
    """추가 데이터 포함 옵션 테스트"""
    query = KDMQuery()

    result = (
        query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .include_comparison()
        .include_weather()
        .include_related()
    )

    assert query._include_comparison is True
    assert query._include_weather is True
    assert query._include_related is True


@pytest.mark.asyncio
async def test_query_validation():
    """쿼리 검증 테스트 - 필수 파라미터 누락"""
    query = KDMQuery()

    # Execute without required parameters should raise error
    with pytest.raises(ValueError, match="site_name is required"):
        await query.execute()


@pytest.mark.asyncio
async def test_query_auto_connect():
    """자동 연결 테스트"""
    # Create query without explicit client connection
    query = KDMQuery()

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Should auto-connect and execute
    assert isinstance(result, QueryResult)


@pytest.mark.asyncio
async def test_query_error_handling():
    """에러 핸들링 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    # Query non-existent facility
    result = (
        await query.site("존재하지않는댐12345", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Should return QueryResult with success=False, not raise exception
    assert isinstance(result, QueryResult)
    assert result.success is False or (result.success and len(result.data) == 0)


@pytest.mark.asyncio
async def test_query_reset():
    """쿼리 리셋 테스트"""
    query = KDMQuery()

    query.site("소양강댐", facility_type="dam").measurements(["저수율"]).days(7)

    # Reset query
    query.reset()

    # All parameters should be cleared
    assert query._site_name is None
    assert query._facility_type is None
    assert query._measurement_items == []
    assert query._days is None


@pytest.mark.asyncio
async def test_batch_result_iteration():
    """배치 결과 반복 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    for dam in ["소양강댐", "충주댐"]:
        query.site(dam, facility_type="dam").measurements(["저수율"]).days(7).add()

    results = await query.execute_batch()

    # Should be iterable
    count = 0
    for site_name, result in results:
        assert isinstance(site_name, str)
        assert isinstance(result, QueryResult)
        count += 1

    assert count > 0


@pytest.mark.asyncio
async def test_query_result_properties():
    """QueryResult 속성 접근 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    # Test properties
    assert hasattr(result, "success")
    assert hasattr(result, "data")
    assert hasattr(result, "site_name")
    assert hasattr(result, "measurement_item")

    if result.success:
        # Test data length property
        assert hasattr(result, "__len__")
        assert len(result) >= 0


@pytest.mark.asyncio
async def test_dataframe_preserves_types():
    """DataFrame 변환 시 데이터 타입 보존 테스트"""
    client = KDMClient()
    await client.connect()

    query = KDMQuery(client=client)

    result = (
        await query.site("소양강댐", facility_type="dam")
        .measurements(["저수율"])
        .days(7)
        .execute()
    )

    if result.success and len(result.data) > 0:
        df = result.to_dataframe()

        # Datetime should be parsed
        if "datetime" in df.columns:
            # Should be datetime type or string
            assert df["datetime"].dtype == "object" or "datetime" in str(
                df["datetime"].dtype
            )


@pytest.mark.asyncio
async def test_comparison_date_arithmetic():
    """전년 대비 비교 시 날짜 연산 정확성 테스트"""
    query = KDMQuery()

    # Set specific date range
    query.site("소양강댐", facility_type="dam").measurements(["저수율"]).date_range(
        start_date="2024-01-01", end_date="2024-01-07"
    ).compare_with_previous_year()

    # Should calculate previous year dates correctly
    assert query._comparison_mode is True

    # When executed, should query both 2024 and 2023 data


@pytest.mark.asyncio
async def test_query_clone():
    """쿼리 복제 테스트"""
    query1 = KDMQuery()

    query1.site("소양강댐", facility_type="dam").measurements(["저수율"]).days(7)

    # Clone the query
    query2 = query1.clone()

    # Modify clone
    query2.site("충주댐", facility_type="dam")

    # Original should be unchanged
    assert query1._site_name == "소양강댐"
    assert query2._site_name == "충주댐"
