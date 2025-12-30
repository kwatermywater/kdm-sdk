# Changelog

All notable changes to KDM SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1-beta] - 2025-12-30

### Fixed

- **Critical: disconnect() RuntimeError** - Fixed resource cleanup failures during disconnect
  - Added `finally` blocks to guarantee `_session` and `_sse_context` are set to `None` even when `__aexit__` raises exceptions
  - Changed cleanup error log level from `WARNING` to `DEBUG` (cleanup errors are expected during shutdown)
  - Fixes `RuntimeError: Attempted to exit cancel scope in a different task` and similar anyio TaskGroup errors
  - Test coverage: 5 new test cases covering exception handling, idempotent disconnect, and proper logging
  - File: `src/kdm_sdk/client.py` lines 127-145

- **Critical: Pylance type recognition failure** - Fixed IDE type inference and autocomplete
  - Added `TYPE_CHECKING` block to `__init__.py` for static type checkers
  - Imports all 11 exported symbols under `TYPE_CHECKING` guard (KDMClient, FacilityPair, KDMQuery, etc.)
  - Preserves lazy loading behavior at runtime (no performance impact)
  - Fixes VSCode/Pylance showing Union types instead of actual class types
  - Enables proper IDE autocomplete and type hints for all SDK classes
  - Test coverage: 6 new test cases verifying lazy loading still works (MCP not imported on module load)
  - File: `src/kdm_sdk/__init__.py` lines 7-14

- **Critical: Non-existent fetch_aligned() method** - Fixed incorrect documentation and test code
  - Removed 8 references to non-existent `FacilityPair.fetch_aligned()` method
  - Updated all code examples with correct pattern:
    1. Fetch upstream/downstream data separately using `KDMClient.get_water_data()`
    2. Convert to DataFrames
    3. Create `FacilityPair` with data
    4. Use `find_optimal_lag()` or `to_dataframe()` for analysis
  - Fixed files:
    - Tests: `test_integration.py`, `test_performance.py` (both now passing)
    - Docs: `README.md` (2 occurrences), `README.en.md` (2 occurrences), `examples/README.md` (2 occurrences)
  - All code examples are now executable and tested
  - Test status: ✅ Integration tests pass with real data

### Testing

- Added 11 new test cases (all passing)
- Full test suite: 84 unit tests passing in 5.29s
- No regressions detected
- TDD methodology: Tests written before implementation

## [0.2.0-beta] - 2025-12-30

### Added

- **find_related_stations()** - Automatically find upstream/downstream monitoring stations for dams
  - Supports search by `dam_name` or `dam_id` parameter
  - Uses Basin matching (priority) + Geographic search (fallback) algorithm
  - Returns both dam information and related stations with `original_facility_code`
  - Configurable `direction` (upstream/downstream), `max_distance_km`, and `limit` parameters
  - Basin matching uses watershed (유역) information for high accuracy
  - Geographic fallback uses Haversine distance + latitude-based direction detection
  - Test status: ✅ Tested and working with real data (소양강댐 → 3 downstream stations found)

- **original_facility_code field** - Original facility codes from source agencies
  - Exposed in all facility search results (`search_facilities`, `find_related_stations`)
  - Enables cross-referencing with external systems (K-water, Ministry of Environment)
  - Format: 7-10 digit string codes (e.g., "1012110" for 소양강댐, "8018703912" for environmental stations)
  - Codes starting with "1": K-water facilities (7 digits)
  - Codes starting with "8": Ministry of Environment facilities (10 digits)
  - Available in both dam info and station info in `find_related_stations()` results
  - Test status: ✅ Tested and verified with multiple facilities

### Changed

- **find_related_stations() return structure** - Enhanced return type with complete context (⚠️ BREAKING CHANGE)
  - **Old**: `List[Dict]` (stations only)
  - **New**: `Dict` with `'dam'` and `'stations'` keys
  - New structure provides complete context including:
    - Dam information with `site_id`, `site_name`, `original_facility_code`, `basin`, `location`
    - Related stations list with same metadata fields
    - Match type indicator (`'basin'` or `'geographic'`)
  - **Migration**: Update code to access `result['dam']` and `result['stations']` instead of treating result as a list
  - Example:
    ```python
    # Old (v0.1.0)
    stations = await client.find_related_stations(dam_name="소양강댐")
    for station in stations:
        print(station['site_name'])

    # New (v0.2.0-beta)
    result = await client.find_related_stations(dam_name="소양강댐")
    print(result['dam']['site_name'])  # Dam info
    for station in result['stations']:
        print(station['site_name'])
    ```

- **Server URL** - Migrated to production environment
  - Default server: `http://203.237.1.4:8080/sse` (changed from `http://localhost:8001/sse`)
  - All examples and tests updated to use production server
  - Backward compatible with custom server URLs via `KDMClient(server_url="...")`
  - Environment-specific configuration still supported

### Fixed

- **Server connection handling** - Improved connection management in examples
  - Fixed connection pooling in long-running examples
  - Added proper error handling for connection failures
  - Updated all examples to use production server URL

- **Documentation inconsistencies** - Corrected facility examples and references
  - Fixed rainfall station example from "의암댐(FTP)" to "광주시(남한산초교)" in DATA_GUIDE.md
  - Updated all localhost references to production server
  - Corrected API endpoint references across documentation

### Testing

All features in this release have been tested and verified:
- ✅ `find_related_stations()` with real dam data (소양강댐, 충주댐)
- ✅ Basin matching algorithm with facilities that have basin information
- ✅ Geographic fallback with facilities without basin information
- ✅ `original_facility_code` exposure in all search operations
- ✅ Server URL migration across all examples and tests
- ✅ Return structure change validated with integration tests

### Known Issues

- None reported for this beta release

### Migration Guide (v0.1.0 → v0.2.0-beta)

**Breaking Change: find_related_stations() return structure**

If you're using `find_related_stations()`, update your code:

```python
# Before (v0.1.0)
stations = await client.find_related_stations(dam_name="소양강댐")
for station in stations:
    process_station(station)

# After (v0.2.0-beta)
result = await client.find_related_stations(dam_name="소양강댐")
dam_info = result['dam']  # Access dam information
stations = result['stations']  # Access stations list
for station in stations:
    process_station(station)
    # Now also has access to original_facility_code
    print(station['original_facility_code'])
```

**Server URL Change**

No code changes required unless you hardcoded `localhost:8001`:

```python
# If you hardcoded the old URL
client = KDMClient(server_url="http://localhost:8001/sse")  # Old

# Update to
client = KDMClient()  # Uses production server by default
# Or explicitly specify
client = KDMClient(server_url="http://203.237.1.4:8080/sse")  # New
```

---

## [0.1.0] - 2025-12-24

### Added

#### Core Components
- **KDMClient**: Low-level MCP client for KDM server communication
  - Async connection management with SSE transport
  - MCP tool invocation (`get_kdm_data`, `search_catalog`, `list_measurements`)
  - Auto-fallback mechanism (hourly → daily → monthly)
  - Retry logic and error handling
  - Health check functionality
  - Context manager support (`async with`)

#### Query API
- **KDMQuery**: Fluent query builder with chainable methods
  - Site selection (`.site()`, `.sites()`)
  - Measurement selection (`.measurements()`)
  - Time period selection (`.days()`, `.date_range()`)
  - Time resolution (`.time_key()`)
  - Batch query support (`.add()`, `.execute_batch()`)
  - Parallel execution for batch queries
  - Query cloning (`.clone()`)
  - Year-over-year comparison (`.compare_with_previous_year()`)
  - Additional data options (`.include_weather()`, etc.)

#### Result Wrappers
- **QueryResult**: Single query result wrapper
  - pandas DataFrame conversion (`.to_dataframe()`)
  - Dictionary conversion (`.to_dict()`)
  - List conversion (`.to_list()`)
  - Success/failure status
  - Metadata access
  - Comparison data support

- **BatchResult**: Batch query result wrapper
  - Dictionary-like access by site name
  - Iteration support
  - Result aggregation (`.aggregate()`)
  - Success/failure filtering
  - Combined DataFrame export

#### FacilityPair
- **FacilityPair**: Upstream-downstream facility analysis
  - Automatic data fetching for paired facilities
  - Time lag alignment
  - Correlation calculation
  - Optimal lag detection
  - Multiple measurement support
  - DataFrame export with aligned data

- **PairResult**: FacilityPair result wrapper
  - Aligned data access
  - Correlation analysis
  - Lag optimization
  - DataFrame conversion

#### Template System
- **TemplateBuilder**: Programmatic template creation
  - Fluent builder interface
  - Site/pair configuration
  - Measurement configuration
  - Period configuration
  - Description and tagging
  - Validation on build

- **Template**: Executable query template
  - Parameter override support
  - Async execution
  - Dictionary conversion
  - YAML serialization

- **Template Loaders**: File-based template management
  - YAML template loading (`.load_yaml()`)
  - Python template loading (`.load_python()`)
  - YAML template saving (`.save_yaml()`)

#### Testing Infrastructure
- pytest configuration with async support
- Test markers (unit, integration, slow)
- Comprehensive test fixtures
- Mock data generators
- Test coverage reporting
- TDD-based development workflow

#### Documentation
- Complete README with quick start examples
- Getting Started guide with step-by-step tutorial
- API Overview with architecture diagrams
- Query API reference documentation
- Templates API reference documentation
- FacilityPair quickstart guide
- Comprehensive code examples
- Troubleshooting guides

#### Examples
- `basic_usage.py`: KDMClient usage examples
- `query_usage.py`: Query API demonstrations (10 examples)
- `facility_pair_usage.py`: FacilityPair analysis examples
- Template examples:
  - `soyang_downstream.py`: Python template
  - `jangheung_comparison.yaml`: YAML template
  - `han_river_batch.py`: Batch query template

#### Development Tools
- Makefile with common commands
- pytest configuration
- Code coverage setup (.coveragerc)
- Black formatter configuration
- mypy type checking
- Requirements files (runtime and dev)

### Features

#### Data Access
- Support for multiple facility types (dam, water_level, rainfall, weather, water_quality)
- Flexible time period specification (days, date ranges)
- Multiple time resolutions (hourly, daily, monthly, auto)
- Batch queries with parallel execution
- Year-over-year comparison support

#### Data Processing
- Automatic pandas DataFrame conversion
- Time series alignment for facility pairs
- Correlation analysis with lag detection
- Result aggregation across multiple facilities
- Missing data handling

#### Developer Experience
- Fluent API for readable code
- Full type hints for IDE support
- Comprehensive error messages
- Auto-complete support
- Extensive documentation
- Working code examples

#### Performance
- Async I/O for non-blocking operations
- Parallel batch execution
- Connection pooling
- Auto-retry with exponential backoff
- Efficient data conversion

### Technical Details

#### Dependencies
- Python 3.10+
- mcp >= 0.1.0 (MCP protocol SDK)
- pandas >= 2.0.0 (data analysis)
- httpx (async HTTP)
- pyyaml (template serialization)

#### Testing
- 100+ test cases
- Unit and integration tests
- Mock data generators
- Test coverage > 80%
- TDD methodology

#### Documentation
- 5 comprehensive guides
- API reference documentation
- 15+ working examples
- Troubleshooting guides
- Architecture diagrams

### Known Limitations

- Requires KDM MCP Server to be running
- Korean facility names required
- Limited to facilities in KDM catalog
- No offline caching yet
- No batch template execution yet

### Future Roadmap

#### Planned for v0.2.0
- Caching layer for offline access
- Batch template execution
- Data export to multiple formats (Excel, JSON, Parquet)
- Advanced filtering and aggregation
- Custom measurement calculations
- Async template execution

#### Planned for v0.3.0
- CLI tool for quick queries
- Interactive query builder
- Data visualization helpers
- Anomaly detection
- Forecast helpers
- Database export support

---

## Release Notes

### v0.1.0 - Initial Release

This is the first stable release of KDM SDK. All core features are implemented and tested:

- ✅ Complete MCP client implementation
- ✅ Fluent Query API with batch support
- ✅ FacilityPair for correlation analysis
- ✅ Template system (YAML + Python)
- ✅ pandas integration
- ✅ Comprehensive documentation
- ✅ Working examples
- ✅ Test suite with >80% coverage

The SDK is ready for production use in data analysis workflows, monitoring systems, and ML pipelines.

**Breaking Changes**: None (initial release)

**Migration Guide**: N/A (initial release)

**Contributors**: KDM SDK Development Team

---

[0.1.0]: https://github.com/your-org/kdm-sdk/releases/tag/v0.1.0
