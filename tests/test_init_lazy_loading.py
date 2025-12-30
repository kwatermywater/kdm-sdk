"""
Test lazy loading behavior in __init__.py

These tests verify that:
1. MCP dependencies are NOT imported on module load
2. Lazy imports return correct classes
3. Repeated imports return same object (idempotent)
4. All exported symbols are accessible
"""

import pytest
import sys


def test_lazy_loading_mcp_not_imported():
    """Verify MCP not imported on module load"""
    # Remove kdm_sdk from sys.modules to get fresh import
    modules_to_remove = [key for key in sys.modules if key.startswith('kdm_sdk')]
    for mod in modules_to_remove:
        del sys.modules[mod]

    # Remove mcp if present
    if 'mcp' in sys.modules:
        del sys.modules['mcp']

    # Import kdm_sdk
    import kdm_sdk

    # Verify mcp is NOT imported yet (lazy loading working)
    assert 'mcp' not in sys.modules, "MCP should not be imported on module load"


def test_lazy_import_returns_correct_class():
    """Verify lazy imports work and return correct classes"""
    import kdm_sdk

    # Test that we can access the class
    assert kdm_sdk.KDMClient is not None
    assert hasattr(kdm_sdk.KDMClient, '__init__')
    assert hasattr(kdm_sdk.KDMClient, 'connect')
    assert hasattr(kdm_sdk.KDMClient, 'disconnect')

    # Test FacilityPair
    assert kdm_sdk.FacilityPair is not None
    assert hasattr(kdm_sdk.FacilityPair, '__init__')

    # Test KDMQuery
    assert kdm_sdk.KDMQuery is not None
    assert hasattr(kdm_sdk.KDMQuery, 'site')
    assert hasattr(kdm_sdk.KDMQuery, 'execute')


def test_lazy_import_idempotent():
    """Verify repeated imports return same object"""
    import kdm_sdk

    # Get references twice
    client1 = kdm_sdk.KDMClient
    client2 = kdm_sdk.KDMClient

    # Should be the exact same object
    assert client1 is client2

    # Same for other exports
    query1 = kdm_sdk.KDMQuery
    query2 = kdm_sdk.KDMQuery
    assert query1 is query2


def test_all_symbols_accessible():
    """Verify all __all__ symbols work"""
    import kdm_sdk

    # Get all exported symbols (excluding __version__)
    expected_symbols = [
        "KDMClient",
        "KDMQuery",
        "QueryResult",
        "BatchResult",
        "FacilityPair",
        "PairResult",
        "TemplateBuilder",
        "Template",
        "load_yaml",
        "load_python",
    ]

    for name in expected_symbols:
        # Should not raise AttributeError
        obj = getattr(kdm_sdk, name)
        assert obj is not None, f"Symbol {name} should be accessible"


def test_invalid_attribute_raises_error():
    """Verify accessing invalid attribute raises AttributeError"""
    import kdm_sdk

    with pytest.raises(AttributeError) as exc_info:
        _ = kdm_sdk.NonExistentClass

    assert "NonExistentClass" in str(exc_info.value)


def test_version_accessible():
    """Verify __version__ is accessible"""
    import kdm_sdk

    assert hasattr(kdm_sdk, '__version__')
    assert isinstance(kdm_sdk.__version__, str)
    assert len(kdm_sdk.__version__) > 0
