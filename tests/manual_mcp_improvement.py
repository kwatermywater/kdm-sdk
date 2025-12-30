#!/usr/bin/env python3
"""
Test if MCP server improvement is complete
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_mcp_improvements():
    """Test MCP server improvements for find_related_stations"""
    print("=" * 60)
    print("Testing MCP Server Improvements")
    print("=" * 60)

    client = KDMClient()
    await client.connect()

    try:
        # Test 1: Empty query with facility_type
        print("\n✓ Test 1: Empty query search")
        print("-" * 60)
        try:
            result = await client.search_facilities(
                query="",
                facility_type="water_level",
                limit=10
            )
            print(f"✅ SUCCESS! Retrieved {len(result)} water_level facilities")
            if result:
                print(f"   First result: {result[0].get('site', result[0]).get('site_name')}")
        except Exception as e:
            print(f"❌ FAILED: {e}")

        # Test 2: Short query
        print("\n✓ Test 2: Short query search")
        print("-" * 60)
        try:
            result = await client.search_facilities(
                query="춘천",
                facility_type="water_level",
                limit=10
            )
            print(f"✅ SUCCESS! Retrieved {len(result)} facilities with '춘천'")
        except Exception as e:
            print(f"❌ FAILED: {e}")

        # Test 3: find_related_stations
        print("\n✓ Test 3: find_related_stations (our feature)")
        print("-" * 60)
        try:
            stations = await client.find_related_stations(
                dam_name="소양강댐",
                direction="downstream",
                limit=5
            )

            if stations:
                print(f"✅ SUCCESS! Found {len(stations)} downstream stations:")
                for i, s in enumerate(stations, 1):
                    print(f"\n   {i}. {s['site_name']}")
                    print(f"      ID: {s['site_id']}")
                    print(f"      Match type: {s['match_type']}")
                    if 'basin' in s:
                        print(f"      Basin: {s['basin']}")
                    if 'distance_km' in s:
                        print(f"      Distance: {s['distance_km']}km")
            else:
                print(f"⚠️  No stations found (MCP improvement may not be complete)")

        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

        # Test 4: Test with 팔당댐
        print("\n✓ Test 4: find_related_stations for 팔당댐")
        print("-" * 60)
        try:
            stations = await client.find_related_stations(
                dam_name="팔당댐",
                direction="downstream",
                limit=3
            )

            if stations:
                print(f"✅ SUCCESS! Found {len(stations)} stations:")
                for s in stations:
                    print(f"   - {s['site_name']} ({s['match_type']})")
            else:
                print(f"⚠️  No stations found")

        except Exception as e:
            print(f"❌ FAILED: {e}")

        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print("If all tests passed, MCP improvement is complete! ✅")
        print("If tests failed, MCP improvement is still needed. ❌")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_mcp_improvements())
