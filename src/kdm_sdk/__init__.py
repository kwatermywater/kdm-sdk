"""
KDM SDK - Python Client for KDM MCP Server
"""

__version__ = "0.1.0"


# Lazy imports to avoid MCP dependency during template-only usage
def __getattr__(name):
    if name == "KDMClient":
        from .client import KDMClient

        return KDMClient
    elif name == "FacilityPair":
        from .facilities import FacilityPair

        return FacilityPair
    elif name == "PairResult":
        from .facilities import PairResult

        return PairResult
    elif name == "KDMQuery":
        from .query import KDMQuery

        return KDMQuery
    elif name == "QueryResult":
        from .results import QueryResult

        return QueryResult
    elif name == "BatchResult":
        from .results import BatchResult

        return BatchResult
    elif name == "TemplateBuilder":
        from .templates import TemplateBuilder

        return TemplateBuilder
    elif name == "Template":
        from .templates import Template

        return Template
    elif name == "load_yaml":
        from .templates import load_yaml

        return load_yaml
    elif name == "load_python":
        from .templates import load_python

        return load_python
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "KDMClient",
    "FacilityPair",
    "PairResult",
    "KDMQuery",
    "QueryResult",
    "BatchResult",
    "TemplateBuilder",
    "Template",
    "load_yaml",
    "load_python",
    "__version__",
]
