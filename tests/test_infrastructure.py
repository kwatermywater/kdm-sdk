"""
테스트 인프라 검증 테스트

TDD Red Phase: 이 테스트들은 처음에는 실패해야 합니다.
pytest 설정이 완료되면 통과할 것입니다.
"""

import pytest


def test_pytest_configured():
    """pytest 설정 확인"""
    assert True


def test_fixtures_available():
    """공통 픽스처 사용 가능 확인"""
    pass


@pytest.mark.asyncio
async def test_async_test_works():
    """비동기 테스트 실행 확인"""

    async def async_function():
        return True

    result = await async_function()
    assert result is True


def test_sample_data_fixture(sample_water_data):
    """샘플 데이터 픽스처 사용 확인"""
    assert sample_water_data is not None
    assert len(sample_water_data) == 2
    assert "datetime" in sample_water_data[0]
    assert "values" in sample_water_data[0]


@pytest.mark.unit
def test_unit_marker():
    """unit 마커 테스트"""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """integration 마커 테스트"""
    assert True


@pytest.mark.slow
def test_slow_marker():
    """slow 마커 테스트"""
    assert True
