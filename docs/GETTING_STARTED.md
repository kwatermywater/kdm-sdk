# Getting Started with KDM SDK

This guide will help you get started with the KDM SDK, from installation to your first query.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Starting the MCP Server](#starting-the-mcp-server)
4. [Your First Query](#your-first-query)
5. [Common Patterns](#common-patterns)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or higher** installed
- **KDM MCP Server** accessible at `http://localhost:8001`
- Basic understanding of Python async/await patterns
- (Optional) Familiarity with pandas for data analysis

Check your Python version:

```bash
python --version
# Should show Python 3.10.x or higher
```

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd kdm-sdk
```

### Step 2: Install Dependencies

```bash
# Install the SDK
pip install -e .

# Or install with development dependencies
pip install -e .
pip install -r requirements-dev.txt
```

### Step 3: Verify Installation

```python
# In Python interpreter or script
import kdm_sdk
print(kdm_sdk.__version__)
# Should print: 0.1.0
```

## Starting the MCP Server

Before using the SDK, you need to have the KDM MCP Server running.

### Check Server Status

```bash
# Test if server is running
curl http://localhost:8001/health
```

If you get a response, the server is ready. If not, refer to the KDM MCP Server documentation to start it.

## Your First Query

Let's fetch some dam storage data!

### Example 1: Simple Query

Create a file called `first_query.py`:

```python
"""
Your first KDM SDK query
"""
import asyncio
from kdm_sdk import KDMQuery


async def main():
    # Create a query for Soyang Dam storage rate
    result = await KDMQuery() \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율"]) \
        .days(7) \
        .execute()

    # Check if query was successful
    if result.success:
        print(f"✓ Successfully fetched data for {result.site_name}")
        print(f"  Records: {len(result)}")

        # Convert to pandas DataFrame
        df = result.to_dataframe()
        print(f"\nFirst few rows:")
        print(df.head())
    else:
        print(f"✗ Query failed: {result.message}")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python first_query.py
```

You should see output like:

```
✓ Successfully fetched data for 소양강댐
  Records: 168

First few rows:
                      저수율
datetime
2024-12-17 00:00:00   45.2
2024-12-17 01:00:00   45.3
2024-12-17 02:00:00   45.3
...
```

### Example 2: Multiple Measurements

```python
import asyncio
from kdm_sdk import KDMQuery


async def main():
    # Fetch multiple measurement items
    result = await KDMQuery() \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율", "유입량", "방류량"]) \
        .days(7) \
        .execute()

    if result.success:
        df = result.to_dataframe()
        print(f"Columns: {list(df.columns)}")
        print(f"\nAverage values:")
        print(df.mean())


asyncio.run(main())
```

### Example 3: Date Range Query

```python
import asyncio
from kdm_sdk import KDMQuery


async def main():
    # Query specific date range
    result = await KDMQuery() \
        .site("충주댐", facility_type="dam") \
        .measurements(["저수율"]) \
        .date_range("2024-01-01", "2024-01-31") \
        .time_key("d_1") \
        .execute()

    if result.success:
        df = result.to_dataframe()
        print(f"January 2024 data: {len(df)} days")
        print(f"Average storage: {df['저수율'].mean():.1f}%")


asyncio.run(main())
```

## Common Patterns

### Pattern 1: Search for Facilities

Before querying, you might want to find the exact facility name:

```python
import asyncio
from kdm_sdk import KDMClient


async def search_facilities():
    client = KDMClient()
    await client.connect()

    # Search for facilities containing "소양"
    results = await client.search_facilities(
        query="소양",
        facility_type="dam",
        limit=5
    )

    print("Found facilities:")
    for facility in results:
        site = facility.get('site', facility)
        print(f"  - {site.get('site_name')}")

    await client.disconnect()


asyncio.run(search_facilities())
```

### Pattern 2: List Available Measurements

Find out what measurements are available for a facility:

```python
import asyncio
from kdm_sdk import KDMClient


async def list_measurements():
    client = KDMClient()
    await client.connect()

    # Get measurements for Soyang Dam
    result = await client.list_measurements(
        site_name="소양강댐",
        facility_type="dam"
    )

    if result.get("success"):
        items = result.get("measurements", [])
        print(f"Available measurements for 소양강댐:")
        for item in items[:10]:  # Show first 10
            print(f"  - {item.get('measurement_item')}: {item.get('unit')}")

    await client.disconnect()


asyncio.run(list_measurements())
```

### Pattern 3: Query Multiple Dams

```python
import asyncio
from kdm_sdk import KDMQuery


async def query_multiple_dams():
    query = KDMQuery()

    # Add multiple dams to batch
    for dam in ["소양강댐", "충주댐", "팔당댐"]:
        query.site(dam, facility_type="dam") \
             .measurements(["저수율"]) \
             .days(7) \
             .add()

    # Execute all queries in parallel
    results = await query.execute_batch(parallel=True)

    # Show results
    print(f"Queried {len(results)} dams:")
    for site_name, result in results:
        if result.success:
            df = result.to_dataframe()
            avg_storage = df["저수율"].mean()
            print(f"  {site_name}: {avg_storage:.1f}%")


asyncio.run(query_multiple_dams())
```

### Pattern 4: Export to CSV

```python
import asyncio
from kdm_sdk import KDMQuery


async def export_to_csv():
    result = await KDMQuery() \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율", "유입량", "방류량"]) \
        .days(30) \
        .execute()

    if result.success:
        df = result.to_dataframe()

        # Save to CSV
        df.to_csv("soyang_dam_data.csv", encoding="utf-8-sig")
        print("✓ Data exported to soyang_dam_data.csv")


asyncio.run(export_to_csv())
```

### Pattern 5: Using Context Manager

For automatic connection management:

```python
import asyncio
from kdm_sdk import KDMClient


async def with_context_manager():
    # Client automatically connects and disconnects
    async with KDMClient() as client:
        result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["저수율"],
            days=7
        )
        print(f"Success: {result.get('success')}")
    # Connection automatically closed


asyncio.run(with_context_manager())
```

## Troubleshooting

### Problem: "Connection refused" Error

**Solution**: Make sure the KDM MCP Server is running:

```bash
curl http://localhost:8001/health
```

If the server is not running, start it according to the KDM MCP Server documentation.

### Problem: "Site not found" Error

**Solution**: Search for the exact facility name first:

```python
client = KDMClient()
await client.connect()
results = await client.search_facilities(query="your-search-term")
```

Use the exact `site_name` from the search results.

### Problem: No Data Returned

**Solution**: Try different time periods:

```python
# Try daily data instead of hourly
result = await query.time_key("d_1").execute()

# Or use auto-fallback
result = await query.time_key("auto").execute()
```

### Problem: Import Error

**Solution**: Make sure you installed the package:

```bash
pip install -e .
```

And check that you're in the correct Python environment.

### Problem: Slow Queries

**Solution**: Use parallel batch execution:

```python
# Faster - runs queries in parallel
results = await query.execute_batch(parallel=True)
```

## Next Steps

Now that you've completed your first queries, explore more advanced features:

1. **[Query API Documentation](QUERY_API.md)** - Learn all query builder methods
2. **[Template System](TEMPLATES_API.md)** - Create reusable query templates
3. **[FacilityPair Guide](FACILITY_PAIR_QUICKSTART.md)** - Analyze upstream-downstream relationships
4. **[API Overview](API_OVERVIEW.md)** - Understand the SDK architecture
5. **[Examples](../examples/)** - See comprehensive usage examples

### Recommended Learning Path

1. Master basic queries (you're here!)
2. Learn batch queries for multiple facilities
3. Explore template system for reusable queries
4. Try FacilityPair for correlation analysis
5. Build your own data analysis workflows

### Example Projects to Try

1. **Dam Storage Dashboard**: Monitor multiple dams' storage rates
2. **Year-over-Year Comparison**: Compare current year with previous year
3. **Downstream Impact Analysis**: Analyze how dam releases affect downstream water levels
4. **Flood Risk Monitoring**: Track water levels and rainfall together
5. **Water Quality Trends**: Analyze water quality measurements over time

## Getting Help

- **Documentation**: Check the [docs/](../docs/) directory
- **Examples**: See working code in [examples/](../examples/)
- **Tests**: Look at [tests/](../tests/) for usage patterns
- **Issues**: Report bugs or ask questions in the repository issues

Happy querying!
