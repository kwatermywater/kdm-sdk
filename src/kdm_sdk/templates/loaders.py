"""
Template Loaders

YAML and Python template loading/saving utilities.
"""

import yaml  # type: ignore
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Template


def load_yaml(filepath: str) -> "Template":
    """
    Load template from YAML file.

    Args:
        filepath: Path to YAML file

    Returns:
        Template instance

    Example:
        >>> template = load_yaml("my_template.yaml")
        >>> result = await template.execute()
    """
    from .base import Template

    with open(filepath, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return Template(config)


def save_yaml(template: "Template", filepath: str):
    """
    Save template to YAML file.

    Args:
        template: Template instance
        filepath: Path to save YAML file

    Example:
        >>> save_yaml(template, "my_template.yaml")
    """
    config = template.to_dict()

    with open(filepath, "w", encoding="utf-8") as f:
        yaml.dump(
            config, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


def load_python(filepath: str) -> "Template":
    """
    Load template from Python file.

    The Python file should either:
    1. Define a 'template' variable with a Template instance
    2. Define a 'create_template()' function that returns a Template

    Args:
        filepath: Path to Python file

    Returns:
        Template instance

    Raises:
        ValueError: If file doesn't contain 'template' or 'create_template'

    Example:
        >>> template = load_python("my_template.py")
        >>> result = await template.execute()
    """
    # Load Python module from file
    spec = importlib.util.spec_from_file_location("template_module", filepath)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load Python file: {filepath}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Look for 'template' variable
    if hasattr(module, "template"):
        return module.template

    # Look for 'create_template' function
    if hasattr(module, "create_template"):
        template = module.create_template()
        return template

    # Error if neither found
    raise ValueError(
        f"No 'template' or 'create_template' found in {filepath}. "
        "Python template files must define one of these."
    )
