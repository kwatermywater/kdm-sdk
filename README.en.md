# KDM SDK

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

Python SDK for accessing K-water Data Model (KDM) through MCP Server.

## Features

- **Fluent Query API** - Chainable, intuitive query builder for KDM data
- **Batch Queries** - Execute multiple queries in parallel for better performance
- **Upstream-Downstream Analysis** - Analyze correlation between dam releases and downstream water levels
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

### ❌ NOT SDK's Job (You Already Know How!)
- **Visualization**: Use matplotlib, seaborn, plotly (you know these already)
- **Statistical Analysis**: Use pandas, scipy, numpy (you know these already)
- **Data Cleaning**: Use pandas methods (you know these already)

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
    pair = FacilityPair(
        upstream_name="소양강댐",
        downstream_name="춘천",
        upstream_type="dam",
        downstream_type="water_level"
    )

    # Fetch aligned data
    result = await pair.fetch_aligned(days=30, time_key="h_1")

    # Find optimal lag time
    correlation = result.find_optimal_lag(max_lag_hours=12)
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

## Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - Installation, first query, and basic usage
- **[API Overview](docs/API_OVERVIEW.md)** - High-level architecture and component overview
- **[Query API](docs/QUERY_API.md)** - Complete KDMQuery API reference
- **[Templates API](docs/TEMPLATES_API.md)** - Template system documentation
- **[FacilityPair Guide](docs/FACILITY_PAIR_QUICKSTART.md)** - Upstream-downstream analysis guide
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
pair = FacilityPair(
    upstream_name="소양강댐",
    downstream_name="의암댐",
    lag_hours=5.5  # Water takes 5.5 hours to travel
)

result = await pair.fetch_aligned(days=365, time_key="h_1")
df = result.to_dataframe()

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
