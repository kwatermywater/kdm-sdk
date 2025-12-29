#!/usr/bin/env python3
"""
Test time periods for water quality stations
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_water_quality_periods():
    client = KDMClient()
    await client.connect()

    # Test water quality station
    time_keys = ["min_10", "h_1", "d_1", "mt_1"]

    print("=" * 70)
    print("수질관측소 시간 단위 테스트")
    print("=" * 70)
    print()

    for time_key in time_keys:
        try:
            result = await client.get_water_data(
                site_name="소양강댐1",
                facility_type="water_quality",
                measurement_items=["TOC"],
                time_key=time_key,
                days=90
            )

            if result and result.get('success'):
                data_count = len(result.get('data', []))
                print(f"✅ {time_key:8} - 작동! ({data_count} data points)")
            else:
                print(f"❌ {time_key:8} - 데이터 없음")
        except Exception as e:
            print(f"❌ {time_key:8} - 오류: {str(e)[:50]}")

        await asyncio.sleep(0.5)

    print()
    print("=" * 70)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_water_quality_periods())
