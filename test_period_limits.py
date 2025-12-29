#!/usr/bin/env python3
"""
Test to verify actual period limits for each time_key
"""
import asyncio
import sys
from datetime import datetime, timedelta
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_period_limit(client, time_key, days_to_test):
    """Test if a specific number of days works for a time_key"""
    try:
        result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["저수율"],
            time_key=time_key,
            days=days_to_test
        )

        if result and result.get('success'):
            data_count = len(result.get('data', []))
            return True, data_count
        else:
            return False, 0
    except Exception as e:
        return False, 0

async def main():
    client = KDMClient()
    await client.connect()

    print("=" * 70)
    print("Testing Period Limits for KDM API")
    print("=" * 70)
    print()

    # Test h_1 (hourly) limits
    print("시간별 데이터 (h_1) 제한 테스트:")
    print("-" * 70)
    h1_test_periods = [7, 30, 60, 90, 180, 365]  # days
    h1_max = 0

    for days in h1_test_periods:
        works, count = await test_period_limit(client, "h_1", days)
        status = "✅" if works else "❌"
        print(f"{status} {days:4}일 ({days//30:2}개월) - {'작동' if works else '실패':4} - {count:5} data points")
        if works:
            h1_max = days
        await asyncio.sleep(0.5)

    print()
    print(f"💡 h_1 최대 기간: 약 {h1_max}일 ({h1_max//30}개월)")
    print()

    # Test d_1 (daily) limits
    print("일별 데이터 (d_1) 제한 테스트:")
    print("-" * 70)
    d1_test_periods = [30, 90, 180, 365, 730, 1095, 1460, 1825, 2190]  # days = 3m, 6m, 1y, 2y, 3y, 4y, 5y, 6y
    d1_max = 0

    for days in d1_test_periods:
        years = days / 365
        works, count = await test_period_limit(client, "d_1", days)
        status = "✅" if works else "❌"
        print(f"{status} {days:4}일 ({years:3.1f}년) - {'작동' if works else '실패':4} - {count:5} data points")
        if works:
            d1_max = days
        await asyncio.sleep(0.5)

    print()
    print(f"💡 d_1 최대 기간: 약 {d1_max}일 ({d1_max/365:.1f}년)")
    print()

    await client.disconnect()

    print("=" * 70)
    print("결론:")
    print("=" * 70)
    print(f"• 시간별 (h_1): 최대 {h1_max}일 (약 {h1_max//30}개월)")
    print(f"• 일별   (d_1): 최대 {d1_max}일 (약 {d1_max/365:.1f}년)")
    print(f"• 10분   (min_10): 지원 안함 ❌")
    print(f"• 월별   (mt_1): 작동 안함 ❌")

if __name__ == "__main__":
    asyncio.run(main())
