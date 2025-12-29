#!/usr/bin/env python3
"""
Test maximum period limits for d_1 time key with response time measurement
"""
import asyncio
import sys
import time
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_period_with_timing(client, days):
    """Test a specific number of days and measure response time"""
    try:
        start_time = time.time()

        result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["저수율"],
            time_key="d_1",
            days=days
        )

        elapsed_time = time.time() - start_time

        if result and result.get('success'):
            data_count = len(result.get('data', []))
            return True, data_count, elapsed_time
        else:
            return False, 0, elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        return False, 0, elapsed_time

async def main():
    client = KDMClient()
    await client.connect()

    print("=" * 80)
    print("d_1 (일별 데이터) 최대 기간 테스트 - 응답 시간 측정")
    print("=" * 80)
    print()

    # Test periods: 10, 15, 20, 25, 30 years
    test_periods = [
        (3650, 10.0),   # 10 years
        (5475, 15.0),   # 15 years
        (7300, 20.0),   # 20 years
        (9125, 25.0),   # 25 years
        (10950, 30.0),  # 30 years
    ]

    max_days = 0

    for days, years in test_periods:
        works, count, elapsed = await test_period_with_timing(client, days)
        status = "✅" if works else "❌"

        print(f"{status} {days:4}일 ({years:4.1f}년) - {'성공' if works else '실패':4} - "
              f"{count:5} 포인트 - {elapsed:6.2f}초")

        if works:
            max_days = days

        await asyncio.sleep(0.5)

    print()
    print("=" * 80)
    print(f"📊 결과: d_1 최대 기간은 {max_days}일 ({max_days/365:.1f}년)")
    print("=" * 80)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
