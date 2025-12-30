#!/usr/bin/env python3
"""
Debug test for find_related_stations
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def debug_search():
    """Debug the search process"""
    client = KDMClient()
    await client.connect()

    try:
        # Step 1: Get dam info
        print("Step 1: Searching for 소양강댐...")
        dam_results = await client.search_facilities(
            query="소양강댐",
            facility_type="dam",
            limit=3
        )

        print(f"Found {len(dam_results)} dams:")
        for dam in dam_results:
            print(f"\n  Raw data: {dam}")
            print(f"\n  Dam: {dam.get('site_name')}")
            print(f"  ID: {dam.get('site_id')}")
            print(f"  Basin: {dam.get('basin')}")
            print(f"  Location: {dam.get('location')}")

        if not dam_results:
            return

        dam_info = dam_results[0]
        dam_basin = dam_info.get('basin')
        print(f"\n\nUsing basin: {dam_basin}")

        # Step 2: Search for related stations
        if dam_basin:
            base_basin = dam_basin.replace("하류", "").replace("상류", "")
            search_query = base_basin.replace("댐", "")
            print(f"Search query: '{search_query}'")

            print(f"\nStep 2: Searching for water_level stations with query='{search_query}'...")
            stations = await client.search_facilities(
                query=search_query,
                facility_type="water_level",
                limit=20
            )

            print(f"\nFound {len(stations)} water_level stations:")
            for s in stations[:10]:  # Show first 10
                print(f"\n  Station: {s.get('site_name')}")
                print(f"  Basin: {s.get('basin')}")
                print(f"  Location: {s.get('location')}")

            # Check basin matching
            print(f"\n\nStep 3: Checking basin matching...")
            print(f"Looking for basin matching: '{base_basin}하류'")

            matches = [s for s in stations if s.get('basin') == f"{base_basin}하류"]
            print(f"Found {len(matches)} matches with basin='{base_basin}하류'")

            if matches:
                print("\nMatches:")
                for m in matches:
                    print(f"  - {m.get('site_name')} (basin: {m.get('basin')})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_search())
