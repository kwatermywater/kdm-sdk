# KDM SDK

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/kwatermywater/kdm-sdk)

> 🚀 **Beta Release** - Python SDK for easy access to K-water Data Model (KDM) data.

Python SDK for accessing K-water Data Model (KDM) through MCP Server.

K-water Data Model (KDM) is a water resource data service based on [water.or.kr/kdm](https://water.or.kr/kdm). This SDK provides easy access to dam operation data, river water levels, rainfall, and other water resource information.

## Features

- **Fluent Query API** - Chainable, intuitive query builder for KDM data
- **Batch Queries** - Execute multiple queries in parallel for better performance
- **Upstream-Downstream Analysis** - Analyze correlation between dam releases and downstream water levels
- **🆕 Automatic Station Discovery** - Find related monitoring stations using basin matching + geographic search
- **🆕 Original Facility Codes** - Access source agency codes (K-water, Ministry of Environment) for system integration
- **Template System** - Create reusable query templates in YAML or Python
- **pandas Integration** - Seamlessly convert results to pandas DataFrames
- **Easy Export** - One-line export to Excel, CSV, Parquet, JSON
- **Auto-fallback** - Automatically tries different time periods (hourly → daily → monthly)
- **Async/await Support** - Built with modern Python async patterns
- **Type Hints** - Full type annotation for better IDE support

## What This SDK Does (and Doesn't Do)

### ✅ SDK's Job
- **Data Access**: Easy querying of KDM water resource data
- **Data Transformation**: Convert to pandas DataFrame
- **Data Export**: Save to Excel, CSV, Parquet, JSON with proper Korean encoding

### ❌ NOT SDK's Job
- **Visualization**: Use matplotlib, seaborn, plotly, etc.
- **Statistical Analysis**: Use pandas, scipy, numpy, etc.
- **Data Cleaning**: Use pandas methods

**Philosophy**: This SDK gets KDM data into pandas. After that, use your existing data analysis skills!

See `examples/analyst_reference.py` for examples of what you can do with pandas after getting the data.

## Installation

```bash
# For data analysts (recommended)
pip install kdm-sdk[analyst]

# Or clone and install locally
git clone <repository-url>
cd kdm-sdk
pip install -e .[analyst]

# For development
pip install -e .[dev]
```

The `[analyst]` extra includes: pandas, jupyter, matplotlib, seaborn, plotly, openpyxl, pyarrow, scipy, statsmodels

## Requirements

- Python 3.10 or higher
- KDM MCP Server (Production: `http://203.237.1.4:8080`)
- pandas 2.0+

## Quick Start

### Basic Query with Fluent API

```python
import asyncio
from kdm_sdk import KDMQuery

async def main():
    # Simple query for dam storage data
    result = await KDMQuery() \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율", "유입량"]) \
        .days(7) \
        .execute()

    # Convert to pandas DataFrame
    df = result.to_dataframe()
    print(df.head())

asyncio.run(main())
```

### Batch Query (Multiple Facilities)

```python
from kdm_sdk import KDMQuery

async def batch_query():
    query = KDMQuery()

    # Add multiple facilities
    for dam in ["소양강댐", "충주댐", "팔당댐"]:
        query.site(dam, facility_type="dam") \
             .measurements(["저수율"]) \
             .days(7) \
             .add()

    # Execute in parallel
    results = await query.execute_batch(parallel=True)

    # Aggregate into single DataFrame
    combined_df = results.aggregate()
    print(combined_df.groupby("site_name")["저수율"].mean())

asyncio.run(batch_query())
```

### Upstream-Downstream Correlation

```python
from kdm_sdk import FacilityPair

async def correlation_analysis():
    # Analyze dam release impact on downstream water level
    from kdm_sdk import KDMClient
    import pandas as pd

    async with KDMClient() as client:
        # Fetch upstream data (dam)
        upstream_result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["방류량"],
            days=30,
            time_key="h_1"
        )

        # Fetch downstream data (water level station)
        downstream_result = await client.get_water_data(
            site_name="춘천시(춘천댐하류)",
            facility_type="water_level",
            measurement_items=["수위"],
            days=30,
            time_key="h_1"
        )

        # Convert to DataFrames
        def to_df(data):
            records = []
            for item in data:
                record = {"datetime": item.get("datetime")}
                if "values" in item:
                    for key, val in item["values"].items():
                        record[key] = val.get("value")
                records.append(record)
            df = pd.DataFrame(records)
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"])
                df.set_index("datetime", inplace=True)
            return df

        upstream_df = to_df(upstream_result.get("data", []))
        downstream_df = to_df(downstream_result.get("data", []))

        # Create FacilityPair
        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천시(춘천댐하류)",
            upstream_type="dam",
            downstream_type="water_level",
            upstream_data=upstream_df,
            downstream_data=downstream_df
        )

        # Find optimal lag time
        correlation = pair.find_optimal_lag(max_lag_hours=12)
        print(f"Optimal lag: {correlation.lag_hours:.1f} hours")
        print(f"Correlation: {correlation.correlation:.3f}")

asyncio.run(correlation_analysis())
```

### Template-Based Query

```python
from kdm_sdk.templates import TemplateBuilder

async def template_query():
    # Create reusable template
    template = TemplateBuilder("Weekly Dam Monitoring") \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율", "유입량", "방류량"]) \
        .days(7) \
        .time_key("h_1") \
        .build()

    # Execute template
    result = await template.execute()
    df = result.to_dataframe()

    # Save template for reuse
    template.save_yaml("templates/weekly_monitoring.yaml")

asyncio.run(template_query())
```

### Automatic Station Discovery (New Feature)

```python
from kdm_sdk import KDMClient

async def find_stations():
    async with KDMClient() as client:
        # Find downstream water level stations for a dam
        result = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            station_type="water_level"
        )

        # Dam information (with original facility code)
        dam = result['dam']
        print(f"Dam: {dam['site_name']}")
        print(f"Original Code: {dam['original_facility_code']}")  # K-water code

        # Related stations
        for station in result['stations']:
            print(f"- {station['site_name']}: {station['original_facility_code']}")
            print(f"  Match Type: {station['match_type']}")  # basin or geographic
            print(f"  Distance: {station['distance_km']:.1f} km")

asyncio.run(find_stations())
```

> ⚠️ **Known Limitations**
> - **Downstream** search: ✅ Works well (basin matching)
> - **Upstream** search: ⚠️ Limited basin data → falls back to geographic search (lower accuracy)
> - Number of linked stations varies by dam (e.g., Soyang Dam: 3, Paldang Dam: 1)
> - Only facilities registered in MCP server are searchable

## Documentation

- **[Quick Start](#quick-start)** - Installation, first query, and basic usage
- **[Features](#features)** - High-level architecture and component overview
- **[Data Guide](docs/DATA_GUIDE.md)** - Facility types, measurements, and API reference
- **[Examples](examples/)** - Comprehensive usage examples

## Project Structure

```
kdm-sdk/
├── src/
│   └── kdm_sdk/
│       ├── __init__.py           # Package exports
│       ├── client.py             # MCP client
│       ├── query.py              # Fluent query API
│       ├── results.py            # Result wrappers
│       ├── facilities.py         # FacilityPair
│       └── templates/            # Template system
│           ├── builder.py        # TemplateBuilder
│           ├── base.py           # Template base class
│           └── loaders.py        # YAML/Python loaders
├── tests/                        # Test suite
├── examples/                     # Usage examples
│   ├── basic_usage.py           # KDMClient examples
│   ├── query_usage.py           # Query API examples
│   ├── facility_pair_usage.py   # FacilityPair examples
│   └── templates/               # Template examples
├── docs/                         # Documentation
└── README.md                     # This file
```

## Examples

See the [examples/](examples/) directory for complete examples:

- **[basic_usage.py](examples/basic_usage.py)** - KDMClient basic usage
- **[query_usage.py](examples/query_usage.py)** - Fluent Query API examples
- **[facility_pair_usage.py](examples/facility_pair_usage.py)** - Upstream-downstream analysis
- **[templates/](examples/templates/)** - Template examples (YAML and Python)

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_query.py -v

# Run with coverage
pytest --cov=kdm_sdk --cov-report=html

# Run only unit tests
pytest -m unit

# Run integration tests (requires MCP server)
pytest -m integration
```

## Common Use Cases

### 1. Monitor Multiple Dams

```python
query = KDMQuery()
for dam in ["소양강댐", "충주댐", "팔당댐", "대청댐"]:
    query.site(dam).measurements(["저수율"]).days(30).add()

results = await query.execute_batch(parallel=True)
df = results.aggregate()
```

### 2. Year-over-Year Comparison

```python
result = await KDMQuery() \
    .site("장흥댐") \
    .measurements(["저수율"]) \
    .date_range("2024-06-01", "2024-06-30") \
    .compare_with_previous_year() \
    .execute()
```

### 3. Predict Downstream Water Levels

```python
from kdm_sdk import KDMClient, FacilityPair
import pandas as pd

async with KDMClient() as client:
    # Fetch upstream data (dam)
    upstream_result = await client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["방류량"],
        days=365,
        time_key="h_1"
    )

    # Fetch downstream data (dam)
    downstream_result = await client.get_water_data(
        site_name="의암댐",
        facility_type="dam",
        measurement_items=["수위"],
        days=365,
        time_key="h_1"
    )

    # Convert to DataFrames
    def to_df(data):
        records = []
        for item in data:
            record = {"datetime": item.get("datetime")}
            if "values" in item:
                for key, val in item["values"].items():
                    record[key] = val.get("value")
            records.append(record)
        df = pd.DataFrame(records)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
        return df

    upstream_df = to_df(upstream_result.get("data", []))
    downstream_df = to_df(downstream_result.get("data", []))

    # Create FacilityPair
    pair = FacilityPair(
        upstream_name="소양강댐",
        downstream_name="의암댐",
        upstream_data=upstream_df,
        downstream_data=downstream_df
    )

    # Create DataFrame with lag (water takes 5.5 hours to travel)
    df = pair.to_dataframe(lag_hours=5.5)

    # Use for ML model training
    X = df[["소양강댐_방류량"]]
    y = df["의암댐_수위"]
```

## Development

### TDD Approach

This project was developed using Test-Driven Development:

1. **Red** - Write failing tests first
2. **Green** - Implement minimal code to pass
3. **Refactor** - Improve code quality

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -v

# Format code
black src tests

# Type check
mypy src
```

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass: `pytest`
5. Format code: `black src tests`
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue in the repository
- See [documentation](docs/) for detailed guides
- Check [examples/](examples/) for usage patterns

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Acknowledgments

- Built for K-water's Korean Dam Management system
- Uses MCP (Model Context Protocol) for data access
- Developed with Test-Driven Development (TDD) methodology

---

## Beta Notice

⚠️ **This is a beta version.**

This SDK is in beta testing phase. Please conduct thorough testing before using in production environments.

**Known Limitations:**
- Some measurements may not be available depending on data availability
- MCP server response times may vary based on network conditions

**Feedback:**
- Please report bugs and feature suggestions via GitHub Issues
- Beta tester feedback is invaluable for SDK improvement

**Contact:** GitHub Issues or K-water support team.
