# KDM SDK API Overview

This document provides a high-level overview of the KDM SDK architecture and its core components.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Common Use Cases](#common-use-cases)
5. [Design Principles](#design-principles)

## Architecture Overview

The KDM SDK is built in layers, from low-level MCP communication to high-level query interfaces:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Application Layer                    │
│  (Your Python scripts, Jupyter notebooks, data pipelines)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   High-Level API Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Templates  │  │  KDMQuery    │  │  FacilityPair    │   │
│  │  (Builder)  │  │  (Fluent)    │  │  (Correlation)   │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Result Wrappers                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ QueryResult  │  │ BatchResult  │  │   PairResult     │  │
│  │ (DataFrame)  │  │ (Aggregate)  │  │  (Correlation)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client Layer                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               KDMClient (MCP Protocol)                │  │
│  │  - Connection management                              │  │
│  │  - Tool invocation (get_kdm_data, search_catalog)    │  │
│  │  - Auto-fallback (hourly → daily → monthly)          │  │
│  │  - Error handling & retries                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   KDM MCP Server (SSE)                       │
│              http://localhost:8001/sse                       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. KDMClient

**Purpose**: Low-level MCP protocol client for direct server communication.

**Key Features**:
- Async connection management
- MCP tool invocation
- Auto-fallback for time periods
- Retry logic and error handling
- Health checks

**When to Use**:
- When you need fine-grained control
- For custom tool invocations
- When building higher-level abstractions

**Example**:
```python
from kdm_sdk import KDMClient

async with KDMClient() as client:
    result = await client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["저수율"],
        days=7
    )
```

**API Reference**: [Client Documentation](../README.md#kdmclient)

### 2. KDMQuery

**Purpose**: Fluent query builder for constructing and executing queries.

**Key Features**:
- Chainable method calls (fluent API)
- Batch query support
- Parallel execution
- Result aggregation
- Query cloning

**When to Use**:
- For most data retrieval tasks
- When you want readable, expressive code
- For batch operations on multiple facilities

**Example**:
```python
from kdm_sdk import KDMQuery

result = await KDMQuery() \
    .site("소양강댐", facility_type="dam") \
    .measurements(["저수율", "유입량"]) \
    .days(7) \
    .execute()
```

**API Reference**: [Query API Documentation](QUERY_API.md)

### 3. FacilityPair

**Purpose**: Analyze relationships between upstream and downstream facilities.

**Key Features**:
- Automatic data fetching and alignment
- Time lag calculation
- Correlation analysis
- Optimal lag detection

**When to Use**:
- Analyzing dam release impacts on downstream water levels
- Finding travel time between facilities
- Building prediction models
- Correlation studies

**Example**:
```python
from kdm_sdk import FacilityPair

pair = FacilityPair(
    upstream_name="소양강댐",
    downstream_name="춘천",
    upstream_type="dam",
    downstream_type="water_level"
)

result = await pair.fetch_aligned(days=30)
correlation = result.find_optimal_lag(max_lag_hours=12)
```

**API Reference**: [FacilityPair Quickstart](FACILITY_PAIR_QUICKSTART.md)

### 4. Template System

**Purpose**: Create reusable query configurations.

**Key Features**:
- Programmatic template building (TemplateBuilder)
- YAML/Python template storage
- Parameter override at execution time
- Template validation

**When to Use**:
- Repeating the same queries regularly
- Sharing query configurations across team
- Building query libraries
- Parameterized reports

**Example**:
```python
from kdm_sdk.templates import TemplateBuilder

template = TemplateBuilder("Weekly Monitoring") \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(7) \
    .build()

# Execute with default parameters
result = await template.execute()

# Override parameters
result = await template.execute(days=30)
```

**API Reference**: [Templates API Documentation](TEMPLATES_API.md)

## Data Flow

### Single Query Flow

```
User Code
   │
   ▼
KDMQuery.site("소양강댐").days(7).execute()
   │
   ▼
KDMClient.get_water_data(...)
   │
   ▼
MCP Tool Call: "get_kdm_data"
   │
   ▼
KDM MCP Server (HTTP SSE)
   │
   ▼
KDMClient (receives response)
   │
   ▼
QueryResult (wraps data)
   │
   ▼
QueryResult.to_dataframe()
   │
   ▼
pandas DataFrame
```

### Batch Query Flow

```
User Code
   │
   ▼
KDMQuery.add().add().add().execute_batch(parallel=True)
   │
   ├──────────┬──────────┬──────────┐
   ▼          ▼          ▼          ▼
  Task1     Task2     Task3     Task4  (parallel)
   │          │          │          │
   └──────────┴──────────┴──────────┘
                    │
                    ▼
              BatchResult
                    │
                    ▼
        BatchResult.aggregate()
                    │
                    ▼
          Combined DataFrame
```

### FacilityPair Flow

```
User Code
   │
   ▼
FacilityPair.fetch_aligned(days=30)
   │
   ├─────────────────┬─────────────────┐
   ▼                 ▼
Fetch Upstream    Fetch Downstream
   │                 │
   └─────────────────┘
            │
            ▼
   Align with Time Lag
            │
            ▼
      PairResult
            │
            ▼
find_optimal_lag(max_lag_hours=12)
            │
            ▼
   CorrelationResult
```

## Common Use Cases

### Use Case 1: Monitor Single Dam

**Components**: KDMQuery, QueryResult

```python
result = await KDMQuery() \
    .site("소양강댐") \
    .measurements(["저수율", "유입량"]) \
    .days(7) \
    .execute()

df = result.to_dataframe()
```

**Why this approach**: Simple, straightforward, good for single facility monitoring.

### Use Case 2: Monitor Multiple Dams

**Components**: KDMQuery (batch), BatchResult

```python
query = KDMQuery()
for dam in ["소양강댐", "충주댐", "팔당댐"]:
    query.site(dam).measurements(["저수율"]).days(7).add()

results = await query.execute_batch(parallel=True)
combined = results.aggregate()
```

**Why this approach**: Parallel execution for better performance, easy aggregation.

### Use Case 3: Analyze Downstream Impact

**Components**: FacilityPair, PairResult

```python
pair = FacilityPair(
    upstream_name="소양강댐",
    downstream_name="춘천",
    lag_hours=5.5
)

result = await pair.fetch_aligned(days=365)
df = result.to_dataframe()
```

**Why this approach**: Automatic time alignment, correlation analysis built-in.

### Use Case 4: Reusable Monitoring Template

**Components**: TemplateBuilder, Template

```python
template = TemplateBuilder("Weekly Report") \
    .sites(["소양강댐", "충주댐"]) \
    .measurements(["저수율"]) \
    .days(7) \
    .build()

template.save_yaml("weekly_report.yaml")

# Later...
template = load_yaml("weekly_report.yaml")
result = await template.execute()
```

**Why this approach**: Reusability, configuration sharing, parameterization.

### Use Case 5: Year-over-Year Comparison

**Components**: KDMQuery (comparison), QueryResult

```python
result = await KDMQuery() \
    .site("장흥댐") \
    .measurements(["저수율"]) \
    .date_range("2024-06-01", "2024-06-30") \
    .compare_with_previous_year() \
    .execute()

if result.comparison_data:
    current = result.to_dataframe()
    previous = result.comparison_data["previous_year_data"]
```

**Why this approach**: Built-in comparison logic, aligned time periods.

## Design Principles

### 1. Fluent Interface

All major APIs use method chaining for readable code:

```python
# Reads like natural language
result = await query \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(7) \
    .execute()
```

### 2. Async-First

All I/O operations are async for better performance:

```python
# Non-blocking I/O
async with KDMClient() as client:
    result = await client.get_water_data(...)
```

### 3. pandas Integration

Results convert seamlessly to pandas DataFrames:

```python
df = result.to_dataframe()
df.plot(y="저수율")
```

### 4. Type Safety

Full type hints for IDE support and error prevention:

```python
from kdm_sdk import KDMQuery, QueryResult

query: KDMQuery = KDMQuery()
result: QueryResult = await query.execute()
```

### 5. Error Handling

Graceful error handling with informative messages:

```python
result = await query.execute()
if not result.success:
    print(f"Error: {result.message}")
```

### 6. Testability

TDD-driven development with comprehensive test coverage:

```bash
pytest tests/ -v --cov=kdm_sdk
```

## Component Comparison

| Component | Use When | Complexity | Flexibility |
|-----------|----------|------------|-------------|
| KDMClient | Direct MCP access needed | Low | High |
| KDMQuery | Standard data queries | Medium | Medium |
| FacilityPair | Upstream-downstream analysis | Medium | Low |
| Templates | Reusable configurations | Low | High |

## Integration Patterns

### Pattern 1: Client → Query

```python
# Custom client configuration
client = KDMClient(timeout=60.0, max_retries=5)
query = KDMQuery(client=client)
```

### Pattern 2: Query → DataFrame → Analysis

```python
result = await query.execute()
df = result.to_dataframe()
df.to_csv("output.csv")
```

### Pattern 3: Batch → Aggregate → Visualization

```python
results = await query.execute_batch(parallel=True)
df = results.aggregate()
df.groupby("site_name")["저수율"].plot(kind="bar")
```

### Pattern 4: Template → Parameterized Execution

```python
template = load_yaml("monitoring.yaml")
result = await template.execute(days=30)  # Override default
```

### Pattern 5: FacilityPair → ML Model

```python
result = await pair.fetch_aligned(days=365)
df = result.to_dataframe()

X = df[["upstream_flow"]]
y = df["downstream_level"]

from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor()
model.fit(X, y)
```

## Performance Considerations

### 1. Use Parallel Batch

```python
# Slow - sequential
results = await query.execute_batch(parallel=False)

# Fast - parallel
results = await query.execute_batch(parallel=True)
```

### 2. Reuse Clients

```python
# Good - reuse client
async with KDMClient() as client:
    query1 = KDMQuery(client=client)
    query2 = KDMQuery(client=client)
```

### 3. Use Appropriate Time Keys

```python
# Use daily for long periods
query.days(365).time_key("d_1")

# Use hourly for short periods
query.days(7).time_key("h_1")
```

## Next Steps

- **[Getting Started](GETTING_STARTED.md)** - Basic usage tutorial
- **[Query API](QUERY_API.md)** - Complete query API reference
- **[Templates API](TEMPLATES_API.md)** - Template system guide
- **[FacilityPair](FACILITY_PAIR_QUICKSTART.md)** - Correlation analysis guide
- **[Examples](../examples/)** - Working code examples
