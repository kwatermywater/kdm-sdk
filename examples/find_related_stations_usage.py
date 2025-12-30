"""
Example: Finding Related Monitoring Stations for Dams

This example demonstrates how to use find_related_stations() to automatically
discover upstream or downstream monitoring stations related to a dam.

Key Features:
- Basin matching using watershed (유역) information (priority)
- Geographic search using Haversine distance (fallback)
- Access to both internal site_id and original facility codes
- Configurable search parameters (direction, distance, limit)

Use Cases:
- Identify monitoring stations for dam impact analysis
- Build upstream-downstream relationship datasets
- Cross-reference with external systems using original facility codes
"""

import asyncio
from kdm_sdk import KDMClient


async def example_by_dam_name():
    """
    Example 1: Find downstream stations by dam name (most common use case)

    This demonstrates the primary use case: finding related stations using
    the dam's name. The algorithm automatically uses basin matching first,
    then falls back to geographic search if needed.
    """
    print("=" * 60)
    print("Example 1: Find Downstream Stations by Dam Name")
    print("=" * 60)

    client = KDMClient()

    try:
        await client.connect()
        print("\nConnected to KDM MCP Server")

        # Find downstream water level stations for 소양강댐
        print("\nSearching for downstream stations of 소양강댐...")
        result = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            station_type="water_level",
            max_distance_km=100.0,
            limit=10
        )

        # Display dam information
        dam = result['dam']
        print(f"\n📍 Dam Information:")
        print(f"  Name: {dam['site_name']}")
        print(f"  Site ID: {dam['site_id']}")
        print(f"  Original Code: {dam.get('original_facility_code', 'N/A')}")
        print(f"  Basin: {dam.get('basin', 'N/A')}")
        print(f"  Location: ({dam['location']['lat']}, {dam['location']['lng']})")

        # Display related stations
        stations = result['stations']
        print(f"\n🌊 Found {len(stations)} downstream water level station(s):")
        print("\n" + "-" * 60)

        for i, station in enumerate(stations, 1):
            print(f"\n{i}. {station['site_name']}")
            print(f"   Site ID: {station['site_id']}")
            print(f"   Original Code: {station.get('original_facility_code', 'N/A')}")
            print(f"   Match Type: {station.get('match_type', 'unknown').upper()}")
            print(f"   Basin: {station.get('basin', 'N/A')}")
            print(f"   Distance: {station.get('distance_km', 0):.1f} km")
            print(f"   Location: ({station['location']['lat']}, {station['location']['lng']})")

        print("\n" + "-" * 60)

        # Explain match types
        basin_matches = [s for s in stations if s.get('match_type') == 'basin']
        geo_matches = [s for s in stations if s.get('match_type') == 'geographic']

        print(f"\nℹ️  Match Strategy Results:")
        print(f"  Basin matching: {len(basin_matches)} station(s)")
        print(f"  Geographic matching: {len(geo_matches)} station(s)")

        if basin_matches:
            print(f"\n  ✓ Basin matching found stations in the same watershed")
            print(f"    (higher confidence in upstream-downstream relationship)")

        if geo_matches:
            print(f"\n  ⚠ Geographic matching used for stations without basin info")
            print(f"    (based on distance and direction only)")

    finally:
        await client.disconnect()
        print("\n✓ Disconnected from server")


async def example_by_dam_id():
    """
    Example 2: Find stations using internal site_id

    When you already have the dam's site_id (e.g., from previous search),
    you can use it directly instead of the name. This is faster and avoids
    ambiguity when multiple dams have similar names.
    """
    print("\n" + "=" * 60)
    print("Example 2: Find Stations by Dam ID")
    print("=" * 60)

    client = KDMClient()

    try:
        await client.connect()
        print("\nConnected to KDM MCP Server")

        # First, search for dam to get its site_id
        print("\nStep 1: Search for dam to get site_id...")
        search_results = await client.search_facilities(
            query="충주댐",
            facility_type="dam",
            limit=5
        )

        if not search_results:
            print("Dam not found")
            return

        dam_site_id = search_results[0]['site']['site_id']
        dam_name = search_results[0]['site']['site_name']
        print(f"  Found: {dam_name} (site_id={dam_site_id})")

        # Now find related stations using site_id
        print(f"\nStep 2: Find downstream stations using site_id={dam_site_id}...")
        result = await client.find_related_stations(
            dam_id=dam_site_id,  # Use dam_id instead of dam_name
            direction="downstream",
            station_type="water_level",
            limit=5
        )

        stations = result['stations']
        print(f"\n✓ Found {len(stations)} downstream station(s):")

        for i, station in enumerate(stations, 1):
            print(f"\n{i}. {station['site_name']}")
            print(f"   Site ID: {station['site_id']}")
            print(f"   Original Code: {station.get('original_facility_code', 'N/A')}")
            print(f"   Distance: {station.get('distance_km', 0):.1f} km")

        print("\nℹ️  Using dam_id is faster and more reliable when:")
        print("  - You already have the site_id from a previous search")
        print("  - The dam name might be ambiguous")
        print("  - You're building automated workflows")

    finally:
        await client.disconnect()
        print("\n✓ Disconnected from server")


async def example_basin_vs_geographic():
    """
    Example 3: Understanding Basin Matching vs Geographic Search

    This example demonstrates the difference between the two matching strategies:
    1. Basin matching: Uses watershed (유역) information for accurate results
    2. Geographic search: Uses distance + direction when basin info is unavailable
    """
    print("\n" + "=" * 60)
    print("Example 3: Basin Matching vs Geographic Search")
    print("=" * 60)

    client = KDMClient()

    try:
        await client.connect()
        print("\nConnected to KDM MCP Server")

        # Example with a dam that has good basin information
        print("\n🔍 Case 1: Dam with Basin Information (소양강댐)")
        print("-" * 60)

        result1 = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            limit=5
        )

        dam1 = result1['dam']
        stations1 = result1['stations']

        print(f"\nDam: {dam1['site_name']}")
        print(f"Basin: {dam1.get('basin', 'N/A')}")
        print(f"\nFound {len(stations1)} station(s):")

        for station in stations1:
            match_indicator = "✓" if station.get('match_type') == 'basin' else "○"
            print(f"  {match_indicator} {station['site_name']} - "
                  f"{station.get('match_type', 'unknown')} match "
                  f"({station.get('distance_km', 0):.1f} km)")

        # Test with different max_distance to see geographic fallback
        print("\n🔍 Case 2: Increasing Search Distance")
        print("-" * 60)
        print("\nSearching with max_distance_km=50...")

        result2 = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            max_distance_km=50.0,  # Shorter distance
            limit=10
        )

        print(f"Found {len(result2['stations'])} station(s) within 50 km")

        print("\nSearching with max_distance_km=200...")
        result3 = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            max_distance_km=200.0,  # Longer distance
            limit=10
        )

        print(f"Found {len(result3['stations'])} station(s) within 200 km")

        print("\nℹ️  Key Insights:")
        print("  • Basin matching provides high-confidence results")
        print("  • Geographic search expands coverage when basin info is limited")
        print("  • Use max_distance_km to control search radius")
        print("  • Check 'match_type' to understand the confidence level")

    finally:
        await client.disconnect()
        print("\n✓ Disconnected from server")


async def example_original_codes():
    """
    Example 4: Cross-referencing with Original Facility Codes

    This example shows how to use original_facility_code to:
    - Cross-reference with external systems (K-water, Ministry of Environment)
    - Link to source data systems
    - Build integration with legacy databases
    """
    print("\n" + "=" * 60)
    print("Example 4: Using Original Facility Codes")
    print("=" * 60)

    client = KDMClient()

    try:
        await client.connect()
        print("\nConnected to KDM MCP Server")

        print("\n📋 Finding related stations and their original codes...")
        result = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            limit=5
        )

        dam = result['dam']
        stations = result['stations']

        # Create a mapping table
        print("\n" + "=" * 90)
        print(f"{'Facility Name':<20} {'Type':<15} {'Site ID':<10} {'Original Code':<15} {'Source':<10}")
        print("=" * 90)

        # Dam row
        dam_code = dam.get('original_facility_code', 'N/A')
        dam_source = "K-water" if dam_code and dam_code.startswith('1') else "Unknown"
        print(f"{dam['site_name']:<20} {'Dam':<15} {dam['site_id']:<10} {dam_code:<15} {dam_source:<10}")

        # Station rows
        for station in stations:
            station_code = station.get('original_facility_code', 'N/A')

            # Infer source from code format
            if station_code == 'N/A':
                source = "N/A"
            elif station_code.startswith('1'):
                source = "K-water"
            elif station_code.startswith('8'):
                source = "MOE"  # Ministry of Environment
            else:
                source = "Unknown"

            print(f"{station['site_name']:<20} {'Water Level':<15} "
                  f"{station['site_id']:<10} {station_code:<15} {source:<10}")

        print("=" * 90)

        print("\n📊 Code Format Guide:")
        print("  • 7-digit codes starting with '1': K-water facilities")
        print("  • 10-digit codes starting with '8': Ministry of Environment facilities")
        print("  • site_id: Internal KDM SDK identifier (integer)")
        print("  • original_facility_code: Source agency code (string)")

        print("\n💡 Use Cases for Original Codes:")
        print("  1. Cross-reference with K-water WAMIS system")
        print("  2. Link to Ministry of Environment water quality data")
        print("  3. Integrate with legacy monitoring systems")
        print("  4. Verify facility identity across different databases")
        print("  5. Trace data lineage back to source")

        # Example: Building a lookup table
        print("\n🔧 Example: Building a Lookup Table")
        print("-" * 60)

        lookup_table = {}
        lookup_table[dam['site_id']] = {
            'name': dam['site_name'],
            'type': 'dam',
            'original_code': dam.get('original_facility_code'),
            'basin': dam.get('basin')
        }

        for station in stations:
            lookup_table[station['site_id']] = {
                'name': station['site_name'],
                'type': 'water_level',
                'original_code': station.get('original_facility_code'),
                'basin': station.get('basin')
            }

        print(f"\nCreated lookup table with {len(lookup_table)} entries")
        print("\nExample lookup:")
        example_id = dam['site_id']
        print(f"  lookup_table[{example_id}] = {{")
        for key, value in lookup_table[example_id].items():
            print(f"    '{key}': '{value}'")
        print("  }")

    finally:
        await client.disconnect()
        print("\n✓ Disconnected from server")


async def example_upstream_search():
    """
    Example 5: Finding Upstream Stations

    While downstream is more common, you can also search for upstream stations.
    This is useful for understanding what affects the dam's inflow.
    """
    print("\n" + "=" * 60)
    print("Example 5: Finding Upstream Stations")
    print("=" * 60)

    client = KDMClient()

    try:
        await client.connect()
        print("\nConnected to KDM MCP Server")

        print("\n🔼 Searching for upstream stations of 소양강댐...")
        result = await client.find_related_stations(
            dam_name="소양강댐",
            direction="upstream",  # Look upstream instead of downstream
            station_type="water_level",
            max_distance_km=100.0,
            limit=5
        )

        dam = result['dam']
        stations = result['stations']

        print(f"\nDam: {dam['site_name']}")
        print(f"Found {len(stations)} upstream station(s):")

        if stations:
            for i, station in enumerate(stations, 1):
                print(f"\n{i}. {station['site_name']}")
                print(f"   Distance: {station.get('distance_km', 0):.1f} km upstream")
                print(f"   Match Type: {station.get('match_type', 'unknown')}")
        else:
            print("\n  No upstream stations found within search criteria")

        print("\nℹ️  Use Cases for Upstream Search:")
        print("  • Identify inflow monitoring points")
        print("  • Build watershed models")
        print("  • Understand upstream conditions affecting dam operations")

    finally:
        await client.disconnect()
        print("\n✓ Disconnected from server")


def main():
    """
    Run all examples
    """
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  KDM SDK - find_related_stations() Examples".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")

    print("\nThis example suite demonstrates how to find related monitoring")
    print("stations for dams using the find_related_stations() method.")
    print("\nPrerequisites:")
    print("  ✓ KDM MCP Server running on http://203.237.1.4:8080")
    print("  ✓ Network connectivity to the server")

    print("\n" + "=" * 60)
    input("\nPress Enter to start examples...")

    # Run examples
    asyncio.run(example_by_dam_name())
    input("\nPress Enter for next example...")

    asyncio.run(example_by_dam_id())
    input("\nPress Enter for next example...")

    asyncio.run(example_basin_vs_geographic())
    input("\nPress Enter for next example...")

    asyncio.run(example_original_codes())
    input("\nPress Enter for next example...")

    asyncio.run(example_upstream_search())

    print("\n" + "=" * 60)
    print("✓ All examples completed!")
    print("=" * 60)
    print("\nNext Steps:")
    print("  • Try with different dams (충주댐, 팔당댐, etc.)")
    print("  • Experiment with different search parameters")
    print("  • Build your own upstream-downstream analysis")
    print("  • Integrate original_facility_code with your systems")


if __name__ == "__main__":
    main()
