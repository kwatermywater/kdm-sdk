"""
Template Builder

Fluent API for creating reusable query templates.
"""

from typing import List, Optional, Union, Dict, Any, TYPE_CHECKING
from ..facilities import FacilityPair

if TYPE_CHECKING:
    from .base import Template


class TemplateBuilder:
    """
    Fluent API for building query templates.

    Example:
        >>> template = TemplateBuilder("Dam Monitoring") \\
        ...     .site("소양강댐", facility_type="dam") \\
        ...     .measurements(["저수율", "유입량"]) \\
        ...     .days(7) \\
        ...     .build()
    """

    def __init__(self, name: str):
        """
        Initialize template builder.

        Args:
            name: Template name
        """
        self._name = name
        self._config: Dict[str, Any] = {
            "name": name,
            "description": "",
            "tags": [],
            "sites": [],
            "pairs": [],
            "measurements": [],
            "period": {},
            "time_key": "auto",
        }

    def description(self, text: str) -> "TemplateBuilder":
        """
        Add description to template.

        Args:
            text: Description text

        Returns:
            Self for chaining
        """
        self._config["description"] = text
        return self

    def tags(self, tags: List[str]) -> "TemplateBuilder":
        """
        Add tags to template.

        Args:
            tags: List of tags

        Returns:
            Self for chaining
        """
        self._config["tags"] = tags
        return self

    def site(self, name: str, facility_type: str = "dam") -> "TemplateBuilder":
        """
        Add a single site.

        Args:
            name: Site name (e.g., "소양강댐")
            facility_type: Facility type (dam, water_level, etc.)

        Returns:
            Self for chaining
        """
        self._config["sites"].append(
            {"site_name": name, "facility_type": facility_type}
        )
        return self

    def sites(self, names: List[str], facility_type: str = "dam") -> "TemplateBuilder":
        """
        Add multiple sites.

        Args:
            names: List of site names
            facility_type: Facility type for all sites

        Returns:
            Self for chaining
        """
        for name in names:
            self.site(name, facility_type)
        return self

    def pair(
        self,
        upstream: Optional[str] = None,
        downstream: Optional[str] = None,
        lag_hours: Optional[float] = None,
        upstream_type: str = "dam",
        downstream_type: str = "water_level",
        upstream_items: Optional[List[str]] = None,
        downstream_items: Optional[List[str]] = None,
        facility_pair: Optional[FacilityPair] = None,
    ) -> "TemplateBuilder":
        """
        Add upstream-downstream facility pair.

        Can either accept individual parameters or a FacilityPair instance.

        Args:
            upstream: Upstream facility name (e.g., "소양강댐")
            downstream: Downstream facility name (e.g., "의암댐")
            lag_hours: Time lag in hours
            upstream_type: Upstream facility type (default: "dam")
            downstream_type: Downstream facility type (default: "water_level")
            upstream_items: Measurement items for upstream (default: ["방류량"])
            downstream_items: Measurement items for downstream (default: ["수위"])
            facility_pair: FacilityPair instance (alternative to individual params)

        Returns:
            Self for chaining
        """
        if facility_pair is not None:
            # Use FacilityPair instance (note: FacilityPair uses upstream_name/downstream_name)
            self._config["pairs"].append(
                {
                    "upstream": getattr(
                        facility_pair, "upstream_name", upstream or ""
                    ),
                    "downstream": getattr(
                        facility_pair, "downstream_name", downstream or ""
                    ),
                    "lag_hours": (
                        getattr(facility_pair, "lag_hours", lag_hours)
                        if hasattr(facility_pair, "lag_hours")
                        else lag_hours
                    ),
                    "upstream_type": getattr(
                        facility_pair, "upstream_type", upstream_type
                    ),
                    "downstream_type": getattr(
                        facility_pair, "downstream_type", downstream_type
                    ),
                    "upstream_items": getattr(
                        facility_pair, "upstream_items", upstream_items
                    ),
                    "downstream_items": getattr(
                        facility_pair, "downstream_items", downstream_items
                    ),
                }
            )
        else:
            # Use individual parameters
            self._config["pairs"].append(
                {
                    "upstream": upstream,
                    "downstream": downstream,
                    "lag_hours": lag_hours,
                    "upstream_type": upstream_type,
                    "downstream_type": downstream_type,
                    "upstream_items": upstream_items or ["방류량"],
                    "downstream_items": downstream_items or ["수위"],
                }
            )
        return self

    def measurements(self, items: List[str]) -> "TemplateBuilder":
        """
        Set measurement items.

        Args:
            items: List of measurement items (e.g., ["저수율", "유입량"])

        Returns:
            Self for chaining
        """
        self._config["measurements"] = items
        return self

    def days(self, n: int) -> "TemplateBuilder":
        """
        Set period to last N days.

        Args:
            n: Number of days

        Returns:
            Self for chaining
        """
        if n <= 0:
            raise ValueError("days must be positive")

        if (
            "start_date" in self._config["period"]
            or "end_date" in self._config["period"]
        ):
            raise ValueError("Cannot specify both days and date_range")

        self._config["period"]["days"] = n
        return self

    def date_range(self, start_date: str, end_date: str) -> "TemplateBuilder":
        """
        Set specific date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Self for chaining
        """
        if "days" in self._config["period"]:
            raise ValueError("Cannot specify both days and date_range")

        self._config["period"]["start_date"] = start_date
        self._config["period"]["end_date"] = end_date
        return self

    def time_key(self, key: str) -> "TemplateBuilder":
        """
        Set time key (hourly, daily, monthly).

        Args:
            key: Time key (h_1, d_1, mt_1, or auto)

        Returns:
            Self for chaining
        """
        self._config["time_key"] = key
        return self

    def build(self) -> "Template":
        """
        Build and validate template.

        Returns:
            Template instance

        Raises:
            ValueError: If validation fails
        """
        # Import here to avoid circular dependency
        from .base import Template

        # Validation
        self._validate()

        return Template(self._config.copy())

    def _validate(self):
        """
        Validate template configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        # Must have at least one site or pair
        if not self._config["sites"] and not self._config["pairs"]:
            raise ValueError("Template must specify at least one site or facility pair")

        # Must have measurements (unless it's a pair, which has default measurements)
        if not self._config["measurements"] and not self._config["pairs"]:
            raise ValueError("Template must specify at least one measurement")

        # Must have period
        if not self._config["period"]:
            raise ValueError("Template must specify a period (days or date_range)")

        # Validate days if specified
        if "days" in self._config["period"]:
            days = self._config["period"]["days"]
            if not isinstance(days, int) or days <= 0:
                raise ValueError("days must be positive")
