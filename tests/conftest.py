"""
pytest 공통 설정 및 픽스처

이 파일은 모든 테스트에서 공유되는 픽스처와 설정을 제공합니다.
"""

import pytest
from typing import List, Dict, Any


@pytest.fixture
async def kdm_client():
    """
    KDM 클라이언트 픽스처

    비동기 컨텍스트에서 KDM 클라이언트를 생성하고 반환합니다.
    테스트 종료 시 자동으로 연결을 종료합니다.

    Yields:
        KDMClient: 연결된 KDM 클라이언트 인스턴스

    Example:
        async def test_something(kdm_client):
            result = await kdm_client.get_facility_data(...)
            assert result is not None
    """
    # 클라이언트 모듈이 아직 구현되지 않았으므로 mock 반환
    # Agent B가 구현 후 실제 클라이언트로 교체
    try:
        from kdm_sdk.client import KDMClient

        client = KDMClient(server_url="http://203.237.1.4:8080/sse")
        await client.connect()
        yield client
        await client.disconnect()
    except ImportError:
        # 모듈이 아직 없으면 None 반환
        yield None


@pytest.fixture
def sample_water_data() -> List[Dict[str, Any]]:
    """
    샘플 수자원 데이터 픽스처

    테스트에서 사용할 수 있는 샘플 수자원 데이터를 제공합니다.

    Returns:
        List[Dict[str, Any]]: 샘플 데이터 리스트

    Example:
        def test_data_processing(sample_water_data):
            assert len(sample_water_data) == 2
            assert sample_water_data[0]["datetime"] == "2024-01-01 00:00:00"
    """
    return [
        {
            "datetime": "2024-01-01 00:00:00",
            "values": {
                "저수율": {"value": 45.2, "unit": "%"},
                "유입량": {"value": 120.5, "unit": "m³/s"},
            },
        },
        {
            "datetime": "2024-01-01 01:00:00",
            "values": {
                "저수율": {"value": 45.3, "unit": "%"},
                "유입량": {"value": 118.2, "unit": "m³/s"},
            },
        },
    ]


@pytest.fixture
def sample_dam_data() -> Dict[str, Any]:
    """
    샘플 댐 정보 데이터 픽스처

    Returns:
        Dict[str, Any]: 샘플 댐 정보
    """
    return {
        "dam_name": "소양강댐",
        "dam_code": "DAM001",
        "location": {"latitude": 38.0, "longitude": 127.8},
        "capacity": {"total": 2900000000, "unit": "m³"},
    }


@pytest.fixture
def sample_river_data() -> Dict[str, Any]:
    """
    샘플 하천 정보 데이터 픽스처

    Returns:
        Dict[str, Any]: 샘플 하천 정보
    """
    return {
        "river_name": "한강",
        "river_code": "RIV001",
        "length": 494.0,
        "basin_area": 26219.0,
    }


@pytest.fixture
def mock_api_response() -> Dict[str, Any]:
    """
    Mock API 응답 데이터 픽스처

    MCP 서버의 API 응답을 시뮬레이션하는 샘플 데이터

    Returns:
        Dict[str, Any]: Mock API 응답
    """
    return {
        "success": True,
        "data": {
            "facility_id": "DAM001",
            "measurements": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "water_level": 150.5,
                    "inflow": 120.3,
                    "outflow": 110.2,
                }
            ],
        },
        "error": None,
    }


# pytest 훅 함수들


def pytest_configure(config):
    """
    pytest 설정 초기화

    테스트 실행 전에 호출되는 훅 함수
    """
    # 테스트 환경 설정
    config.addinivalue_line(
        "markers", "requires_server: tests that require MCP server to be running"
    )


def pytest_collection_modifyitems(config, items):
    """
    테스트 수집 후 호출되는 훅

    테스트 아이템들을 수정하거나 필터링할 수 있습니다.
    """
    # 비동기 테스트에 자동으로 asyncio 마커 추가
    for item in items:
        if "async" in item.nodeid:
            item.add_marker(pytest.mark.asyncio)
