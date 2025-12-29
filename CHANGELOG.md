# Changelog

All notable changes to KDM SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-24

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
