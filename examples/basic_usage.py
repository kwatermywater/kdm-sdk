"""
KDM SDK Basic Usage Example

This example demonstrates the basic usage of KDMClient for direct MCP server interaction.

Key Concepts:
- Client initialization and connection management
- Searching for facilities in the KDM catalog
- Listing available measurements for a facility
- Fetching water data with different time periods
- Auto-fallback mechanism for time periods
- Health checking
- Proper resource cleanup

Prerequisites:
- KDM MCP Server (Production: http://203.237.1.4:8080)
- Python 3.10+
- kdm-sdk installed (pip install -e .)

Run:
    python examples/basic_usage.py
"""

import asyncio
from kdm_sdk import KDMClient


async def main():
    """
    Main example function demonstrating KDMClient usage.

    This function shows:
    1. How to initialize and connect to the MCP server
    2. How to search for facilities
    3. How to list available measurements
    4. How to fetch water data
    5. How to use auto-fallback for time periods
    6. How to check server health
    7. How to properly disconnect
    """
    # Initialize client
    # The server_url points to the KDM MCP Server's SSE endpoint
    # Default is http://203.237.1.4:8080/sse (production server)
    client = KDMClient()  # Uses default production server

    try:
        # Connect to MCP server
        # This establishes the SSE connection to the MCP server
        # The connection is reused for all subsequent requests
        await client.connect()
        print("Connected to KDM MCP Server\n")

        # ============================================================
        # 1. SEARCH FOR FACILITIES
        # ============================================================
        # Before querying data, you often need to find the exact facility name.
        # The search_facilities method helps you discover facilities in the catalog.
        print("=== Searching for '소양강' facilities ===")
        facilities = await client.search_facilities(
            query="소양강",  # Search term
            facility_type="dam",  # Filter by type (optional)
            limit=5,  # Maximum results to return
        )
        # Display search results
        for facility in facilities:
            site = facility.get("site", facility)
            print(f"- {site.get('site_name')} ({site.get('region', 'N/A')})")
        print()

        # ============================================================
        # 2. LIST AVAILABLE MEASUREMENTS
        # ============================================================
        # Each facility has different measurement items available.
        # Use list_measurements to discover what data you can query.
        print("=== Available measurements for 소양강댐 ===")
        measurements = await client.list_measurements(
            site_name="소양강댐",  # Exact facility name
            facility_type="dam",  # Facility type
        )
        # Display measurement items (first 10)
        if measurements.get("success"):
            items = measurements.get("measurements", [])[:10]
            for item in items:
                # Each item has a name and unit of measurement
                print(f"- {item.get('measurement_item')}: {item.get('unit')}")
        print()

        # ============================================================
        # 3. GET WATER DATA
        # ============================================================
        # Fetch actual water data for a facility.
        # This is the core functionality of the SDK.
        print("=== Getting water data (last 7 days) ===")
        result = await client.get_water_data(
            site_name="소양강댐",  # Facility name
            facility_type="dam",  # Facility type
            measurement_items=["저수율", "저수량"],  # What to measure
            days=7,  # Last 7 days
            time_key="d_1",  # Daily data (d_1)
        )
        # time_key options:
        # - "h_1": Hourly data
        # - "d_1": Daily data
        # - "mt_1": Monthly data
        # - "auto": Auto-fallback (tries h_1 → d_1 → mt_1)

        # Process and display results
        if result.get("success"):
            print(f"Site: {result.get('site_name')}")
            print(f"Data points: {result.get('count')}")

            # Show first 3 data points
            # Each data point has a datetime and values dictionary
            data = result.get("data", [])[:3]
            for point in data:
                print(f"\n{point['datetime']}:")
                # Values are stored as {measurement_item: {value, unit}}
                for item_name, value_obj in point["values"].items():
                    print(f"  {item_name}: {value_obj['value']} {value_obj['unit']}")
        print()

        # ============================================================
        # 4. AUTO-FALLBACK EXAMPLE
        # ============================================================
        # When requesting long time periods, hourly data may not be available.
        # The auto-fallback mechanism tries different time resolutions:
        # 1. Try hourly (h_1)
        # 2. If fails, try daily (d_1)
        # 3. If fails, try monthly (mt_1)
        print("=== Auto-fallback for 730 days ===")
        result_auto = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["저수율"],
            days=730,  # 2 years - hourly won't work
            time_key="auto",  # Enable auto-fallback
        )
        # The SDK automatically chooses the best available time resolution

        # Display which time resolution was used
        if result_auto.get("success"):
            print(f"Used time_key: {result_auto.get('used_time_key')}")
            print(f"Data points: {result_auto.get('count')}")
            # For 730 days, it likely used d_1 (daily) or mt_1 (monthly)
        print()

        # ============================================================
        # 5. HEALTH CHECK
        # ============================================================
        # Check if the MCP server is responding correctly
        is_healthy = await client.health_check()
        print(f"Server health: {'OK' if is_healthy else 'ERROR'}")

    finally:
        # ============================================================
        # CLEANUP
        # ============================================================
        # Always disconnect to free resources
        # This closes the SSE connection properly
        await client.disconnect()
        print("\nDisconnected from server")


# ============================================================
# ALTERNATIVE: Using Context Manager
# ============================================================
# For automatic connection management, use async with:
#
# async def main_with_context():
#     async with KDMClient() as client:
#         result = await client.get_water_data(...)
#         # Process result
#     # Connection automatically closed


if __name__ == "__main__":
    asyncio.run(main())
