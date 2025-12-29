# Template System API Reference

## Overview

The Template System provides reusable query templates for common KDM data access patterns. Templates can be created programmatically via `TemplateBuilder` or loaded from YAML/Python files.

## TemplateBuilder

Fluent API for creating templates.

### Constructor

```python
TemplateBuilder(name: str)
```

Creates a new template builder with the given name.

### Methods

#### `.description(text: str) -> TemplateBuilder`

Add a description to the template.

```python
template = TemplateBuilder("My Template") \
    .description("Monitors dam storage levels")
```

#### `.tags(tags: List[str]) -> TemplateBuilder`

Add tags for categorization.

```python
template = TemplateBuilder("My Template") \
    .tags(["monitoring", "dam", "hourly"])
```

#### `.site(name: str, facility_type: str = "dam") -> TemplateBuilder`

Add a single site to query.

```python
template = TemplateBuilder("My Template") \
    .site("소양강댐", facility_type="dam")
```

#### `.sites(names: List[str], facility_type: str = "dam") -> TemplateBuilder`

Add multiple sites for batch queries.

```python
template = TemplateBuilder("Han River Monitoring") \
    .sites(["소양강댐", "춘천댐", "팔당댐"], facility_type="dam")
```

#### `.pair(upstream: str, downstream: str, lag_hours: float = None, ...) -> TemplateBuilder`

Add upstream-downstream facility pair for correlation analysis.

```python
template = TemplateBuilder("Downstream Analysis") \
    .pair(
        upstream="소양강댐",
        downstream="의암댐",
        lag_hours=5.5,
        upstream_items=["방류량"],
        downstream_items=["수위"]
    )
```

#### `.measurements(items: List[str]) -> TemplateBuilder`

Set measurement items to retrieve.

```python
template = TemplateBuilder("My Template") \
    .measurements(["저수율", "유입량", "방류량"])
```

#### `.days(n: int) -> TemplateBuilder`

Set period to last N days.

```python
template = TemplateBuilder("Weekly Report") \
    .days(7)
```

#### `.date_range(start_date: str, end_date: str) -> TemplateBuilder`

Set specific date range.

```python
template = TemplateBuilder("Annual Report") \
    .date_range("2024-01-01", "2024-12-31")
```

#### `.time_key(key: str) -> TemplateBuilder`

Set time resolution (h_1, d_1, mt_1, or auto).

```python
template = TemplateBuilder("Hourly Data") \
    .time_key("h_1")
```

#### `.build() -> Template`

Build and validate the template.

```python
template = TemplateBuilder("My Template") \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(30) \
    .build()
```

## Template

Executable template with parameter override support.

### Methods

#### `async execute(client: KDMClient = None, **params) -> QueryResult | FacilityPair`

Execute template with optional parameter overrides.

```python
# Basic execution
result = await template.execute()

# Override days parameter
result = await template.execute(days=14)

# Use specific client
result = await template.execute(client=my_client, time_key="d_1")
```

#### `to_dict() -> Dict[str, Any]`

Convert template to dictionary representation.

```python
config = template.to_dict()
print(config["name"])
print(config["measurements"])
```

#### `save_yaml(filepath: str)`

Save template to YAML file.

```python
template.save_yaml("my_template.yaml")
```

## Template Loaders

### `load_yaml(filepath: str) -> Template`

Load template from YAML file.

```python
from kdm_sdk.templates import load_yaml

template = load_yaml("jangheung_comparison.yaml")
result = await template.execute()
```

**YAML Format:**

```yaml
name: "Template Name"
description: "Optional description"
tags:
  - tag1
  - tag2

sites:
  - site_name: "소양강댐"
    facility_type: "dam"

measurements:
  - "저수율"
  - "유입량"

period:
  days: 30

time_key: "h_1"
```

### `load_python(filepath: str) -> Template`

Load template from Python file.

```python
from kdm_sdk.templates import load_python

template = load_python("soyang_downstream.py")
result = await template.execute()
```

**Python Format:**

Python templates must define either:
1. A `template` variable, or
2. A `create_template()` function

```python
from kdm_sdk.templates import TemplateBuilder

def create_template():
    return TemplateBuilder("My Template") \
        .site("소양강댐") \
        .measurements(["저수율"]) \
        .days(30) \
        .build()

template = create_template()
```

### `save_yaml(template: Template, filepath: str)`

Save template to YAML file (alternative to `template.save_yaml()`).

```python
from kdm_sdk.templates import save_yaml

save_yaml(template, "output.yaml")
```

## Validation

Templates are validated when built. The following validations are performed:

1. **Must have at least one site or pair**: Template must specify data source
2. **Must have measurements** (unless using pair with defaults)
3. **Must have period** (days or date_range)
4. **Days must be positive**
5. **Cannot specify both days and date_range**

Validation errors raise `ValueError` with descriptive messages.

## Examples

### 1. Simple Dam Monitoring

```python
from kdm_sdk.templates import TemplateBuilder

template = TemplateBuilder("소양강댐 주간 모니터링") \
    .description("저수율과 유입량 주간 모니터링") \
    .site("소양강댐", facility_type="dam") \
    .measurements(["저수율", "유입량"]) \
    .days(7) \
    .time_key("h_1") \
    .build()

result = await template.execute()
df = result.to_dataframe()
```

### 2. Batch Query (Multiple Dams)

```python
template = TemplateBuilder("한강 수계 모니터링") \
    .sites(["소양강댐", "춘천댐", "팔당댐"], facility_type="dam") \
    .measurements(["저수율"]) \
    .days(30) \
    .build()

batch_result = await template.execute()
dfs = batch_result.to_dataframes()
combined = batch_result.aggregate()
```

### 3. Upstream-Downstream Analysis

```python
template = TemplateBuilder("소양강댐 하류 영향 분석") \
    .pair(
        upstream="소양강댐",
        downstream="의암댐",
        lag_hours=5.5,
        upstream_items=["방류량"],
        downstream_items=["수위"]
    ) \
    .days(365) \
    .time_key("h_1") \
    .build()

pair_result = await template.execute()
corr = pair_result.calculate_correlation(lag_hours=5.5)
print(f"Correlation: {corr.correlation:.3f}")
```

### 4. Load from YAML

```python
from kdm_sdk.templates import load_yaml

template = load_yaml("templates/weekly_report.yaml")

# Override parameters
result = await template.execute(days=14, time_key="d_1")
```

### 5. Save Template for Reuse

```python
template = TemplateBuilder("Custom Template") \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(30) \
    .build()

# Save as YAML
template.save_yaml("custom_template.yaml")

# Later, load and use
loaded = load_yaml("custom_template.yaml")
result = await loaded.execute()
```

## Best Practices

1. **Use descriptive names**: Template names should clearly indicate their purpose
2. **Add descriptions and tags**: Helps with organization and discovery
3. **Use pairs for correlation analysis**: When analyzing upstream-downstream relationships
4. **Save common queries as templates**: Reuse templates across projects
5. **Use parameter overrides**: Modify template behavior without creating new templates
6. **Validate before saving**: Build templates to catch configuration errors early

## Integration with Query API

Templates are built on top of `KDMQuery` and `FacilityPair`. They provide:

- **Reusability**: Save common queries for repeated use
- **Parameterization**: Override parameters at execution time
- **Validation**: Catch configuration errors at build time
- **Portability**: Share templates as YAML/Python files
- **Documentation**: Self-documenting via descriptions and tags
