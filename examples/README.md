# KDM SDK Examples

This directory contains comprehensive examples demonstrating KDM SDK usage.

## Table of Contents

1. [Basic Examples](#basic-examples)
2. [Related Stations Discovery](#related-stations-discovery)
3. [Query API Examples](#query-api-examples)
4. [FacilityPair Examples](#facilitypair-examples)
5. [Template Examples](#template-examples)
6. [Running Examples](#running-examples)

## Basic Examples

### basic_usage.py

Demonstrates basic KDMClient usage with direct MCP server interaction.

**Features Covered**:
- Client initialization and connection
- Facility search
- Listing available measurements
- Fetching water data
- Auto-fallback mechanism
- Health checks
- Proper connection cleanup

**Run**:
```bash
python examples/basic_usage.py
```

**Expected Output**:
```
Connected to KDM MCP Server

=== Searching for '소양강' facilities ===
- 소양강댐 (강원)

=== Available measurements for 소양강댐 ===
- 저수율: %
- 저수량: 백만톤
- 유입량: m³/s
...

=== Getting water data (last 7 days) ===
Site: 소양강댐
Data points: 168

2024-12-17 00:00:00:
  저수율: 45.2 %
  저수량: 1234.5 백만톤
...
```

## Related Stations Discovery

### find_related_stations_usage.py

Demonstrates automatic discovery of upstream/downstream monitoring stations related to dams.

**Features Covered**:
1. **Find by Dam Name**: Discover downstream stations using dam name with automatic basin matching
2. **Find by Dam ID**: Search using internal site_id for faster, more reliable queries
3. **Basin vs Geographic Matching**: Understand the two-stage search algorithm (basin priority → geographic fallback)
4. **Original Facility Codes**: Access and use source agency codes (K-water, Ministry of Environment) for system integration
5. **Upstream Search**: Find upstream stations to understand inflow sources

**Run**:
```bash
python examples/find_related_stations_usage.py
```

**Expected Output**:
```
Example 1: Find Downstream Stations by Dam Name

📍 Dam Information:
  Name: 소양강댐
  Site ID: 50548
  Original Code: 1012110
  Basin: 소양강댐하류

🌊 Found 3 downstream water level station(s):

1. 춘천
   Site ID: 1822
   Original Code: 1018680001
   Match Type: BASIN
   Distance: 25.3 km

2. 의암댐
   Site ID: 1825
   Original Code: 1018680002
   Match Type: BASIN
   Distance: 42.1 km

3. 춘천시(춘천댐하류)
   Site ID: 50552
   Original Code: 1018680003
   Match Type: GEOGRAPHIC
   Distance: 28.7 km
```

**Key Concepts**:
- **Basin Matching**: Uses watershed (유역) information for high-confidence matches
  - When dam and station share the same basin, they're likely in an upstream-downstream relationship
  - Example: "소양강댐하류" basin contains stations directly affected by the dam

- **Geographic Search**: Fallback using Haversine distance + direction detection
  - Used when basin information is unavailable or incomplete
  - Considers both distance and relative position (upstream/downstream based on latitude)

- **Original Facility Code**: Source agency identifier for external system integration
  - Format: 7-digit (K-water) or 10-digit (Ministry of Environment)
  - Enables cross-referencing with WAMIS, water quality databases, etc.
  - Different from internal `site_id` (integer)

**Use Cases**:
- Build upstream-downstream analysis datasets for impact studies
- Create facility relationship maps for watershed modeling
- Integrate with external monitoring systems using original codes
- Automate monitoring station discovery for dam operations

## Query API Examples

### query_usage.py

Comprehensive demonstration of the Fluent Query API.

**Features Covered**:
1. **Basic Query**: Simple single-facility query
2. **Date Range Query**: Specific date range with daily data
3. **Year-over-Year Comparison**: Compare current vs previous year
4. **Batch Query**: Sequential batch execution
5. **Parallel Batch**: Parallel execution for better performance
6. **Aggregate Results**: Combine batch results into single DataFrame
7. **Additional Options**: Include weather, comparison, related data
8. **Error Handling**: Handle non-existent facilities gracefully
9. **Data Conversion**: Convert results to dict, list, DataFrame
10. **Query Clone**: Clone and modify base query

**Run All Examples**:
```bash
python examples/query_usage.py
```

**Run Specific Example**:
```python
import asyncio
from examples.query_usage import example_basic_query

asyncio.run(example_basic_query())
```

**Key Techniques**:

#### Batch Query Pattern
```python
query = KDMQuery()
for dam in ["소양강댐", "충주댐", "팔당댐"]:
    query.site(dam).measurements(["저수율"]).days(7).add()

results = await query.execute_batch(parallel=True)
```

#### Aggregation Pattern
```python
combined_df = results.aggregate()
avg_by_site = combined_df.groupby("site_name")["저수율"].mean()
```

#### Query Clone Pattern
```python
base = KDMQuery().measurements(["저수율"]).days(7)
query1 = base.clone().site("소양강댐")
query2 = base.clone().site("충주댐")
```

## FacilityPair Examples

### facility_pair_usage.py

Demonstrates upstream-downstream relationship analysis.

**Features Covered**:
1. **Real Data Analysis**: Analyze actual dam-downstream relationship
2. **Synthetic Data**: Demonstrate lag detection with known lag
3. **Multiple Measurements**: Analyze different measurement combinations

**Run**:
```bash
python examples/facility_pair_usage.py
```

**Key Techniques**:

#### Basic Correlation Analysis
```python
from kdm_sdk import KDMClient, FacilityPair
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

    # Fetch downstream data (water level)
    downstream_result = await client.get_water_data(
        site_name="춘천",
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
        downstream_name="춘천",
        upstream_type="dam",
        downstream_type="water_level",
        upstream_data=upstream_df,
        downstream_data=downstream_df
    )

    # Find optimal lag
    correlation = pair.find_optimal_lag(max_lag_hours=12)

    print(f"Optimal lag: {correlation.lag_hours:.1f} hours")
    print(f"Correlation: {correlation.correlation:.3f}")
```

#### Lag Detection
```python
# Test different lags
for lag in [0, 2, 4, 6, 8]:
    r = pair.calculate_correlation(lag_hours=lag)
    print(f"Lag {lag}h: correlation = {r.correlation:+.3f}")
```

#### ML Model Preparation
```python
df = result.to_dataframe()
X = df[["소양강댐_방류량"]]
y = df["춘천_수위"]

from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor()
model.fit(X, y)
```

## Template Examples

### templates/soyang_downstream.py

Python template for analyzing Soyang Dam's downstream impact.

**Features**:
- FacilityPair template
- Parameterized lag hours
- Executable as standalone script

**Usage**:
```python
from kdm_sdk.templates import load_python

template = load_python("examples/templates/soyang_downstream.py")
result = await template.execute()
```

**Or run directly**:
```bash
python examples/templates/soyang_downstream.py
```

### templates/jangheung_comparison.yaml

YAML template for year-over-year comparison at Jangheung Dam.

**Features**:
- Year-over-year comparison
- YAML configuration format
- Easy to edit and share

**Usage**:
```python
from kdm_sdk.templates import load_yaml

template = load_yaml("examples/templates/jangheung_comparison.yaml")
result = await template.execute()

# Override parameters
result = await template.execute(days=180)
```

**YAML Structure**:
```yaml
name: "장흥댐 전년 대비 비교"
type: "comparison"
facilities:
  - site_name: "장흥댐"
    facility_type: "dam"
measurements:
  - "저수율"
  - "유입량"
period:
  days: 365
comparison:
  type: "year_over_year"
  base_year: 2024
```

### templates/han_river_batch.py

Python template for batch monitoring of Han River basin dams.

**Features**:
- Multi-dam batch query
- Han River system monitoring
- Weekly data collection

**Usage**:
```python
from examples.templates.han_river_batch import template

result = await template.execute()
dfs = result.to_dataframes()  # One DataFrame per dam
combined = result.aggregate()  # Combined DataFrame
```

**Customize**:
```python
# Modify dam list
from kdm_sdk.templates import TemplateBuilder

template = TemplateBuilder("Custom Batch") \
    .sites(["소양강댐", "충주댐", "팔당댐"]) \
    .measurements(["저수율", "유입량"]) \
    .days(30) \
    .build()
```

## Running Examples

### Prerequisites

1. **Start KDM MCP Server**:
```bash
# Make sure server is running
curl http://203.237.1.4:8080/health
```

2. **Install Dependencies**:
```bash
cd kdm-sdk
pip install -e .
```

### Run All Examples

```bash
# Basic client usage
python examples/basic_usage.py

# Query API examples
python examples/query_usage.py

# FacilityPair examples
python examples/facility_pair_usage.py

# Template examples
python examples/templates/soyang_downstream.py
python examples/templates/han_river_batch.py
```

### Run in Jupyter Notebook

```python
import asyncio
from examples.query_usage import example_basic_query

# Run async function in notebook
await example_basic_query()
```

Or use `asyncio.run()`:
```python
asyncio.run(example_basic_query())
```

### Import and Use Functions

```python
from examples.facility_pair_usage import example_with_synthetic_data

# Run the synthetic data example
example_with_synthetic_data()
```

## Example Output Files

Some examples generate output files:

- `soyang_chuncheon_aligned.csv` - Aligned upstream-downstream data from FacilityPair
- `soyang_dam_data.csv` - Exported dam data from query examples
- `*.yaml` - Saved template configurations

## Troubleshooting

### "Connection refused" Error

**Problem**: Cannot connect to MCP server.

**Solution**:
```bash
# Check if server is running
curl http://203.237.1.4:8080/health

# If not, start the server (refer to KDM MCP Server docs)
```

### "Site not found" Error

**Problem**: Facility name doesn't match catalog.

**Solution**:
```python
# Search for correct name
from kdm_sdk import KDMClient

async with KDMClient() as client:
    results = await client.search_facilities(query="your-search")
    for r in results:
        print(r.get('site', {}).get('site_name'))
```

### Import Errors

**Problem**: Cannot import kdm_sdk.

**Solution**:
```bash
# Make sure SDK is installed
pip install -e .

# Check installation
python -c "import kdm_sdk; print(kdm_sdk.__version__)"
```

### No Data Returned

**Problem**: Query returns empty results.

**Solution**:
```python
# Try different time period
result = await query.time_key("d_1").execute()  # Daily instead of hourly

# Or use auto-fallback
result = await query.time_key("auto").execute()
```

## Learning Path

### Beginner
1. Start with `basic_usage.py` - Understand MCP client
2. Try simple queries from `query_usage.py` (Examples 1-3)
3. Learn batch queries (Examples 4-6)

### Intermediate
1. Explore `facility_pair_usage.py` - Correlation analysis
2. Create your first template using TemplateBuilder
3. Try parallel batch execution for performance

### Advanced
1. Build custom templates in YAML/Python
2. Implement ML models with FacilityPair data
3. Create automated monitoring workflows
4. Integrate with data pipelines

## Example Projects

### Project 1: Dam Storage Dashboard
```python
# Monitor multiple dams, create daily reports
query = KDMQuery()
for dam in MONITORED_DAMS:
    query.site(dam).measurements(["저수율"]).days(1).add()

results = await query.execute_batch(parallel=True)
df = results.aggregate()
df.to_csv(f"daily_report_{date.today()}.csv")
```

### Project 2: Flood Early Warning
```python
# Monitor water levels and rainfall
template = TemplateBuilder("Flood Monitoring") \
    .sites(CRITICAL_POINTS, facility_type="water_level") \
    .measurements(["수위"]) \
    .days(1) \
    .time_key("h_1") \
    .include_weather() \
    .build()

result = await template.execute()
# Check thresholds, send alerts
```

### Project 3: Downstream Prediction
```python
# Train ML model to predict downstream levels
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

    # Fetch downstream data (water level)
    downstream_result = await client.get_water_data(
        site_name="춘천",
        facility_type="water_level",
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
        downstream_name="춘천",
        upstream_data=upstream_df,
        downstream_data=downstream_df
    )

    # Get aligned data
    df = pair.to_dataframe(lag_hours=0)

    # Train model
    from sklearn.ensemble import RandomForestRegressor
    X = df[["upstream_flow"]]
    y = df["downstream_level"]
    model = RandomForestRegressor()
    model.fit(X, y)
```

## Next Steps

- Read [API Overview](../docs/API_OVERVIEW.md) for architecture understanding
- Check [Query API](../docs/QUERY_API.md) for complete API reference
- Review [Templates API](../docs/TEMPLATES_API.md) for template system details
- See [Getting Started](../docs/GETTING_STARTED.md) for step-by-step tutorial

## Contributing Examples

To add new examples:

1. Create example file in `examples/`
2. Add comprehensive comments
3. Include error handling
4. Update this README
5. Add entry to main README
6. Test example works standalone

Example template:
```python
"""
Brief description of what this example demonstrates

Key concepts covered:
- Concept 1
- Concept 2
"""

import asyncio
from kdm_sdk import KDMQuery


async def main():
    """
    Main example function with clear steps
    """
    # Step 1: Setup
    query = KDMQuery()

    # Step 2: Execute
    result = await query.site("소양강댐").days(7).execute()

    # Step 3: Process results
    if result.success:
        print(f"Success: {len(result)} records")


if __name__ == "__main__":
    asyncio.run(main())
```

Happy coding!
