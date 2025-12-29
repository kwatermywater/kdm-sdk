#!/usr/bin/env python3
"""
Test to verify which time periods are actually available
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_time_periods():
    client = KDMClient()
    await client.connect()

    # Test different time periods
    time_keys = ["min_10", "h_1", "d_1", "mt_1"]

    print("Testing available time periods for 소양강댐...")
    print("=" * 60)

    for time_key in time_keys:
        try:
            result = await client.get_water_data(
                site_name="소양강댐",
                facility_type="dam",
                measurement_items=["저수율"],
                time_key=time_key,
                days=3
            )

            if result and result.get('success'):
                data_count = len(result.get('data', []))
                print(f"✅ {time_key:8} - Works! ({data_count} data points)")
            else:
                print(f"❌ {time_key:8} - No data or failed")
        except Exception as e:
            print(f"❌ {time_key:8} - Error: {str(e)[:50]}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_time_periods())
