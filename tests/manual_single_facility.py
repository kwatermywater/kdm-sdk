#!/usr/bin/env python3
"""
Test a single facility name
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_facility():
    client = KDMClient()
    await client.connect()

    # Test 의암댐(FTP) as rainfall station
    print("Testing: 의암댐(FTP) - rainfall")
    try:
        result = await client.get_water_data(
            site_name="의암댐(FTP)",
            facility_type="rainfall",
            measurement_items=["우량"],
            time_key="d_1",
            days=3
        )

        if result and result.get('success'):
            data_count = len(result.get('data', []))
            print(f"✅ 작동! ({data_count} data points)")
        else:
            print(f"❌ 실패")
            print(f"응답: {result}")
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_facility())
