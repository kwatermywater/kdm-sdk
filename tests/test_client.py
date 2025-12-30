"""
KDM MCP Client Tests (TDD Approach)
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kdm_sdk.client import KDMClient


@pytest.mark.asyncio
async def test_client_initialization():
    """클라이언트 초기화 테스트"""
    client = KDMClient(server_url="http://203.237.1.4:8080/sse")
    assert client is not None
    assert client.server_url == "http://203.237.1.4:8080/sse"


@pytest.mark.asyncio
async def test_get_water_data():
    """get_kdm_data 도구 호출 테스트"""
    client = KDMClient()
    await client.connect()

    result = await client.get_water_data(
        site_name="소양강댐", facility_type="dam", measurement_items=["저수율"], days=7
    )

    assert result is not None
    assert isinstance(result, dict)
    assert "success" in result
    if result.get("success"):
        assert "data" in result
        assert isinstance(result["data"], list)


@pytest.mark.asyncio
async def test_search_facilities():
    """search_catalog 도구 호출 테스트"""
    client = KDMClient()
    await client.connect()

    results = await client.search_facilities(query="소양강", facility_type="dam")

    assert results is not None
    assert isinstance(results, list)
    if len(results) > 0:
        # Check if any result contains "소양강댐"
        # Results may have nested 'site' object
        site_names = [
            r.get("site", {}).get("site_name", "") or r.get("site_name", "")
            for r in results
        ]
        assert any(
            "소양강" in name for name in site_names
        ), f"Expected '소양강' in results, got: {site_names}"


@pytest.mark.asyncio
async def test_list_measurements():
    """list_measurements 도구 호출 테스트"""
    client = KDMClient()
    await client.connect()

    result = await client.list_measurements(site_name="소양강댐", facility_type="dam")

    assert result is not None
    assert isinstance(result, dict)
    if result.get("success"):
        assert "measurements" in result
        items = result["measurements"]
        assert isinstance(items, list)
        # Check if any measurement has "저수율"
        if len(items) > 0:
            measurement_items = [item.get("measurement_item", "") for item in items]
            assert any("저수율" in item for item in measurement_items)


@pytest.mark.asyncio
async def test_auto_fallback():
    """시간 단위 자동 폴백 테스트"""
    client = KDMClient()
    await client.connect()

    # 730일은 시간 데이터가 없을 수 있으므로 일별로 폴백되어야 함
    result = await client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["저수율"],
        days=730,
        time_key="auto",
    )

    assert result is not None
    # Auto fallback should still return data even if time_key needs adjustment


@pytest.mark.asyncio
async def test_connection_retry():
    """연결 재시도 테스트"""
    client = KDMClient()

    # First connection
    await client.connect()
    assert client.is_connected()

    # Disconnect and reconnect
    await client.disconnect()
    assert not client.is_connected()

    await client.connect()
    assert client.is_connected()


@pytest.mark.asyncio
async def test_invalid_facility():
    """존재하지 않는 시설 조회 테스트"""
    client = KDMClient()
    await client.connect()

    result = await client.get_water_data(
        site_name="존재하지않는댐12345",
        facility_type="dam",
        measurement_items=["저수율"],
        days=7,
    )

    assert result is not None
    # Should return error or empty result, not crash
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_health_check():
    """헬스 체크 테스트"""
    client = KDMClient()
    await client.connect()

    is_healthy = await client.health_check()
    assert isinstance(is_healthy, bool)


@pytest.mark.asyncio
async def test_disconnect_sets_session_to_none_on_exception(monkeypatch):
    """Verify _session = None even if __aexit__ raises"""
    client = KDMClient()
    await client.connect()

    # Mock __aexit__ to raise RuntimeError
    async def mock_aexit(*args):
        raise RuntimeError("Mock exception during session cleanup")

    if client._session is not None:
        monkeypatch.setattr(client._session, "__aexit__", mock_aexit)

    # disconnect() should not raise and should set _session to None
    await client.disconnect()
    assert client._session is None


@pytest.mark.asyncio
async def test_disconnect_sets_sse_context_to_none_on_exception(monkeypatch):
    """Verify _sse_context = None even if __aexit__ raises"""
    client = KDMClient()
    await client.connect()

    # Mock __aexit__ to raise RuntimeError
    async def mock_aexit(*args):
        raise RuntimeError("Mock exception during SSE cleanup")

    if client._sse_context is not None:
        monkeypatch.setattr(client._sse_context, "__aexit__", mock_aexit)

    # disconnect() should not raise and should set _sse_context to None
    await client.disconnect()
    assert client._sse_context is None


@pytest.mark.asyncio
async def test_disconnect_cleans_up_both_even_if_both_fail(monkeypatch):
    """Verify both resources cleaned up even if both raise"""
    client = KDMClient()
    await client.connect()

    # Mock both to raise exceptions
    async def mock_session_aexit(*args):
        raise RuntimeError("Session cleanup failed")

    async def mock_sse_aexit(*args):
        raise RuntimeError("SSE cleanup failed")

    if client._session is not None:
        monkeypatch.setattr(client._session, "__aexit__", mock_session_aexit)

    if client._sse_context is not None:
        monkeypatch.setattr(client._sse_context, "__aexit__", mock_sse_aexit)

    # disconnect() should not raise and should clean up both
    await client.disconnect()
    assert client._session is None
    assert client._sse_context is None


@pytest.mark.asyncio
async def test_disconnect_logs_cleanup_errors_as_debug(monkeypatch, caplog):
    """Verify cleanup errors logged at DEBUG level"""
    import logging

    client = KDMClient()
    await client.connect()

    # Mock to raise exception
    async def mock_aexit(*args):
        raise RuntimeError("Mock cleanup error")

    if client._session is not None:
        monkeypatch.setattr(client._session, "__aexit__", mock_aexit)

    # Capture logs at DEBUG level
    with caplog.at_level(logging.DEBUG):
        await client.disconnect()

    # Check that error was logged at DEBUG level (not WARNING)
    debug_messages = [record.message for record in caplog.records if record.levelname == "DEBUG"]
    assert any("Error during disconnect" in msg or "Mock cleanup error" in msg for msg in debug_messages)

    # Verify no WARNING level logs for cleanup errors
    warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
    assert not any("Error during disconnect" in msg for msg in warning_messages)


@pytest.mark.asyncio
async def test_disconnect_idempotent():
    """Verify calling disconnect twice is safe"""
    client = KDMClient()
    await client.connect()

    # First disconnect
    await client.disconnect()
    assert not client.is_connected()

    # Second disconnect should not raise
    await client.disconnect()
    assert not client.is_connected()


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup():
    """각 테스트 후 정리"""
    yield
    # Cleanup code can go here if needed
