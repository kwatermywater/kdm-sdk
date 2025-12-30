#!/usr/bin/env python3
"""
Quick test for find_related_stations functionality
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_basic():
    """Test basic downstream station search"""
    print("=" * 60)
    print("Testing find_related_stations")
    print("=" * 60)

    client = KDMClient()
    await client.connect()

    try:
        # Test 1: Find downstream stations for 소양강댐
        print("\n1. Finding downstream stations for 소양강댐...")
        stations = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            limit=5
        )

        if stations:
            print(f"✅ Found {len(stations)} stations:")
            for i, s in enumerate(stations, 1):
                print(f"\n{i}. {s['site_name']}")
                print(f"   ID: {s['site_id']}")
                print(f"   Type: {s['facility_type']}")
                print(f"   Match: {s['match_type']}")
                if 'basin' in s:
                    print(f"   Basin: {s['basin']}")
                if 'distance_km' in s:
                    print(f"   Distance: {s['distance_km']}km")
        else:
            print("❌ No stations found")

        # Test 2: Try upstream
        print("\n\n2. Finding upstream stations for 소양강댐...")
        upstream = await client.find_related_stations(
            dam_name="소양강댐",
            direction="upstream",
            limit=3
        )

        if upstream:
            print(f"✅ Found {len(upstream)} upstream stations:")
            for s in upstream:
                print(f"   - {s['site_name']} ({s['match_type']})")
        else:
            print("ℹ️  No upstream stations found (this is normal)")

        # Test 3: Test with 팔당댐
        print("\n\n3. Finding downstream stations for 팔당댐...")
        stations2 = await client.find_related_stations(
            dam_name="팔당댐",
            direction="downstream",
            limit=3
        )

        if stations2:
            print(f"✅ Found {len(stations2)} stations:")
            for s in stations2:
                print(f"   - {s['site_name']} ({s['match_type']})")
        else:
            print("❌ No stations found")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_basic())
