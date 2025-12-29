# KDM Query API Documentation

## Overview

The KDM Query API provides a fluent, chainable interface for building and executing queries against the KDM (K-water Data Model) MCP server. It follows the builder pattern and supports both single and batch queries with convenient result handling.

## Quick Start

```python
from kdm_sdk import KDMQuery

# Simple query
query = KDMQuery()
result = await query \
    .site("소양강댐", facility_type="dam") \
    .measurements(["저수율", "유입량"]) \
    .days(7) \
    .execute()

# Convert to DataFrame
df = result.to_dataframe()
print(df.head())
```

## KDMQuery Class

### Constructor

```python
KDMQuery(client: Optional[KDMClient] = None)
```

**Parameters:**
- `client`: Optional KDMClient instance. If not provided, a new client will be created and auto-connected.

### Methods

#### Site Selection

##### `.site(name: str, facility_type: str = "dam") -> KDMQuery`

Set the facility/site to query.

**Parameters:**
- `name`: Facility name (e.g., "소양강댐")
- `facility_type`: One of: `dam`, `water_level`, `rainfall`, `weather`, `water_quality`

**Example:**
```python
query.site("소양강댐", facility_type="dam")
```

#### Measurement Selection

##### `.measurements(items: List[str]) -> KDMQuery`

Set measurement items to query.

**Parameters:**
- `items`: List of measurement items (e.g., `["저수율", "유입량"]`)

**Example:**
```python
query.measurements(["저수율", "유입량", "방류량"])
```

#### Time Period

##### `.days(n: int) -> KDMQuery`

Query data for the last N days.

**Parameters:**
- `n`: Number of days

**Example:**
```python
query.days(7)  # Last 7 days
query.days(30)  # Last 30 days
```

##### `.date_range(start_date: str, end_date: str) -> KDMQuery`

Set specific date range.

**Parameters:**
- `start_date`: Start date (YYYYMMDD or YYYY-MM-DD)
- `end_date`: End date (YYYYMMDD or YYYY-MM-DD)

**Example:**
```python
query.date_range("2024-01-01", "2024-01-31")
query.date_range("20240101", "20240131")  # Also works
```

#### Time Resolution

##### `.time_key(key: str) -> KDMQuery`

Set time resolution (temporal granularity).

**Parameters:**
- `key`: Time key - one of:
  - `h_1`: Hourly
  - `d_1`: Daily
  - `mt_1`: Monthly
  - `auto`: Auto-fallback (tries hourly → daily → monthly)

**Example:**
```python
query.time_key("h_1")  # Hourly data
query.time_key("auto")  # Auto-fallback
```

#### Comparison

##### `.compare_with_previous_year() -> KDMQuery`

Enable year-over-year comparison. Fetches data for both current period and same period in previous year.

**Example:**
```python
query \
    .date_range("2024-06-01", "2024-06-30") \
    .compare_with_previous_year()
```

#### Additional Data Options

##### `.include_comparison() -> KDMQuery`
Include year-over-year comparison data.

##### `.include_weather() -> KDMQuery`
Include weather data.

##### `.include_related() -> KDMQuery`
Include related facility data.

##### `.include_flood() -> KDMQuery`
Include flood-related data.

##### `.include_drought() -> KDMQuery`
Include drought-related data.

##### `.include_discharge() -> KDMQuery`
Include discharge details.

##### `.include_quality() -> KDMQuery`
Include water quality data.

##### `.include_safety() -> KDMQuery`
Include dam safety data.

**Example:**
```python
query \
    .site("소양강댐") \
    .include_weather() \
    .include_related()
```

#### Execution

##### `await .execute() -> QueryResult`

Execute the query and return results.

**Returns:** `QueryResult` instance

**Raises:**
- `ValueError`: If required parameters are missing

**Example:**
```python
result = await query.execute()
```

#### Batch Operations

##### `.add() -> KDMQuery`

Add current query to batch queue and reset for next query.

**Example:**
```python
query.site("소양강댐").days(7).add()
query.site("충주댐").days(7).add()
query.site("팔당댐").days(7).add()
```

##### `await .execute_batch(parallel: bool = False) -> BatchResult`

Execute all queued queries.

**Parameters:**
- `parallel`: If True, execute queries in parallel. Default is False (sequential).

**Returns:** `BatchResult` instance

**Example:**
```python
# Sequential
results = await query.execute_batch()

# Parallel (faster)
results = await query.execute_batch(parallel=True)
```

#### Utility Methods

##### `.reset() -> KDMQuery`

Reset all query parameters.

**Example:**
```python
query.reset()  # Clear all settings
```

##### `.clone() -> KDMQuery`

Create a deep copy of this query.

**Example:**
```python
base_query = KDMQuery().measurements(["저수율"]).days(7)
query1 = base_query.clone().site("소양강댐")
query2 = base_query.clone().site("충주댐")
```

## QueryResult Class

Represents the result of a single query.

### Properties

- `success: bool` - Whether query was successful
- `data: List[Dict]` - List of data records
- `site_name: Optional[str]` - Name of queried facility
- `facility_type: Optional[str]` - Type of facility
- `measurement_item: Optional[str]` - Primary measurement item
- `message: Optional[str]` - Result message (if any)
- `comparison_data: Optional[Dict]` - Year-over-year comparison data
- `metadata: Dict` - Query metadata

### Methods

#### `.to_dataframe() -> pd.DataFrame`

Convert result to pandas DataFrame.

**Returns:** pandas DataFrame with datetime column and measurement columns

**Example:**
```python
df = result.to_dataframe()
print(df.head())
df.plot(x="datetime", y="저수율")
```

#### `.to_dict() -> Dict[str, Any]`

Convert result to dictionary.

**Example:**
```python
data_dict = result.to_dict()
print(data_dict["success"])
print(data_dict["site_name"])
```

#### `.to_list() -> List[Dict[str, Any]]`

Convert result data to list.

**Example:**
```python
data_list = result.to_list()
for record in data_list:
    print(record["datetime"], record["values"])
```

### Special Methods

- `len(result)` - Number of data records
- `bool(result)` - True if query was successful
- `repr(result)` - String representation

## BatchResult Class

Represents the result of a batch query.

### Accessing Results

```python
# By index
result = batch_results["소양강댐"]

# Check if site exists
if "소양강댐" in batch_results:
    result = batch_results["소양강댐"]

# Get with default
result = batch_results.get("소양강댐", default_value)

# Iterate
for site_name, result in batch_results:
    print(site_name, result.success)
```

### Methods

#### `.aggregate() -> pd.DataFrame`

Aggregate all results into a single DataFrame.

**Returns:** Combined DataFrame with `site_name` and `facility_type` columns

**Example:**
```python
combined_df = batch_results.aggregate()
print(combined_df.groupby("site_name")["저수율"].mean())
```

#### `.to_dict() -> Dict[str, Dict[str, Any]]`

Convert all results to dictionary.

**Example:**
```python
all_results = batch_results.to_dict()
```

#### `.filter_successful() -> BatchResult`

Get only successful results.

**Example:**
```python
successful = batch_results.filter_successful()
print(f"Success rate: {len(successful)}/{len(batch_results)}")
```

#### `.filter_failed() -> BatchResult`

Get only failed results.

**Example:**
```python
failed = batch_results.filter_failed()
for site_name, result in failed:
    print(f"{site_name}: {result.message}")
```

### Special Methods

- `len(batch_results)` - Number of query results
- `iter(batch_results)` - Iterate over (site_name, result) pairs

## Complete Examples

### Example 1: Basic Query

```python
from kdm_sdk import KDMQuery

query = KDMQuery()

result = await query \
    .site("소양강댐", facility_type="dam") \
    .measurements(["저수율", "유입량"]) \
    .days(7) \
    .execute()

if result.success:
    df = result.to_dataframe()
    print(df.head())
```

### Example 2: Year-over-Year Comparison

```python
query = KDMQuery()

result = await query \
    .site("충주댐", facility_type="dam") \
    .measurements(["저수율"]) \
    .date_range("2024-06-01", "2024-06-30") \
    .compare_with_previous_year() \
    .execute()

if result.comparison_data:
    current_df = result.to_dataframe()
    prev_data = result.comparison_data["previous_year_data"]
    print(f"Current: {current_df['저수율'].mean():.1f}%")
```

### Example 3: Batch Query

```python
query = KDMQuery()

# Add multiple facilities
for dam in ["소양강댐", "충주댐", "팔당댐"]:
    query \
        .site(dam, facility_type="dam") \
        .measurements(["저수율"]) \
        .days(7) \
        .add()

# Execute all
results = await query.execute_batch(parallel=True)

# Aggregate
combined_df = results.aggregate()
print(combined_df.groupby("site_name")["저수율"].mean())
```

### Example 4: Error Handling

```python
query = KDMQuery()

result = await query \
    .site("NonExistentDam") \
    .measurements(["저수율"]) \
    .days(7) \
    .execute()

if not result.success:
    print(f"Error: {result.message}")
else:
    df = result.to_dataframe()
```

### Example 5: Query Clone

```python
# Create base query template
base_query = KDMQuery() \
    .measurements(["저수율"]) \
    .days(7) \
    .include_weather()

# Clone for different facilities
query1 = base_query.clone().site("소양강댐")
query2 = base_query.clone().site("충주댐")

result1 = await query1.execute()
result2 = await query2.execute()
```

## Type Hints

The Query API is fully typed. Example:

```python
from kdm_sdk import KDMQuery, QueryResult, BatchResult
from typing import List

async def fetch_dam_data(dam_name: str) -> QueryResult:
    query: KDMQuery = KDMQuery()
    result: QueryResult = await query \
        .site(dam_name, facility_type="dam") \
        .days(7) \
        .execute()
    return result

async def fetch_multiple_dams(dams: List[str]) -> BatchResult:
    query: KDMQuery = KDMQuery()
    for dam in dams:
        query.site(dam).days(7).add()
    results: BatchResult = await query.execute_batch(parallel=True)
    return results
```

## Best Practices

### 1. Use Auto-Connect

Let the query handle connection automatically:

```python
# Good - auto-connects
query = KDMQuery()
result = await query.site("소양강댐").days(7).execute()

# Also good - explicit client
client = KDMClient()
await client.connect()
query = KDMQuery(client=client)
```

### 2. Use Parallel Batch for Performance

```python
# Faster for multiple queries
results = await query.execute_batch(parallel=True)
```

### 3. Handle Errors Gracefully

```python
result = await query.execute()
if not result.success:
    print(f"Query failed: {result.message}")
    return

df = result.to_dataframe()
```

### 4. Use Query Clone for Templates

```python
# Create reusable template
template = KDMQuery().measurements(["저수율"]).days(7)

# Use for different sites
result1 = await template.clone().site("소양강댐").execute()
result2 = await template.clone().site("충주댐").execute()
```

### 5. Aggregate Batch Results

```python
results = await query.execute_batch()
combined_df = results.aggregate()

# Analyze across all sites
avg_by_site = combined_df.groupby("site_name")["저수율"].mean()
```

## Common Patterns

### Pattern 1: Multi-Site Comparison

```python
query = KDMQuery()

for dam in ["소양강댐", "충주댐", "팔당댐", "대청댐"]:
    query.site(dam).measurements(["저수율"]).days(30).add()

results = await query.execute_batch(parallel=True)
df = results.aggregate()

# Compare storage rates
pivot = df.pivot_table(
    index="datetime",
    columns="site_name",
    values="저수율"
)
pivot.plot(title="Dam Storage Rate Comparison")
```

### Pattern 2: Time Series Analysis

```python
result = await query \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(365) \
    .time_key("d_1") \
    .execute()

df = result.to_dataframe()
df.set_index("datetime", inplace=True)

# Calculate rolling average
df["rolling_avg"] = df["저수율"].rolling(window=7).mean()
df[["저수율", "rolling_avg"]].plot()
```

### Pattern 3: Data Export

```python
result = await query.execute()

# Export to CSV
df = result.to_dataframe()
df.to_csv("dam_data.csv", index=False)

# Export to JSON
data_dict = result.to_dict()
import json
with open("dam_data.json", "w") as f:
    json.dump(data_dict, f, ensure_ascii=False, indent=2)
```

## See Also

- [KDM Client Documentation](./CLIENT_API.md)
- [Example Scripts](../examples/)
- [Test Cases](../tests/test_query.py)
