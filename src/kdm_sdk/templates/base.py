"""
Template Base Class

Executable template with parameter support.
"""

from typing import Dict, Any, Optional
from ..query import KDMQuery
from ..facilities import FacilityPair
from ..client import KDMClient


class Template:
    """
    Executable query template.

    Templates can be created via TemplateBuilder or loaded from YAML/Python files.

    Example:
        >>> template = Template(config)
        >>> result = await template.execute(client=client, days=14)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize template from configuration.

        Args:
            config: Template configuration dictionary
        """
        self._config = config
        self.name = config.get("name", "Unnamed Template")
        self.description = config.get("description", "")
        self.tags = config.get("tags", [])

    async def execute(self, client: Optional[KDMClient] = None, **params):
        """
        Execute template with optional parameter overrides.

        Args:
            client: KDM client (creates new one if not provided)
            **params: Parameter overrides (e.g., days=14)

        Returns:
            QueryResult or PairResult depending on template type

        Example:
            >>> result = await template.execute(days=30)
            >>> df = result.to_dataframe()
        """
        # Merge config with params
        effective_config = self._merge_params(params)

        # Create client if not provided
        if client is None:
            client = KDMClient()
            await client.connect()

        # Execute based on template type
        if effective_config.get("pairs"):
            return await self._execute_pair(client, effective_config)
        else:
            return await self._execute_query(client, effective_config)

    async def _execute_pair(self, client: KDMClient, config: Dict[str, Any]):
        """
        Execute template with facility pair.

        Args:
            client: KDM client
            config: Effective configuration

        Returns:
            FacilityPair with fetched data
        """
        from ..query import KDMQuery
        from ..results import QueryResult

        pair_config = config["pairs"][0]
        period = config.get("period", {})
        time_key = config.get("time_key", "h_1")

        # Fetch upstream data
        upstream_query = KDMQuery(client=client)
        upstream_query.site(
            pair_config["upstream"],
            facility_type=pair_config.get("upstream_type", "dam"),
        )
        if pair_config.get("upstream_items"):
            upstream_query.measurements(pair_config["upstream_items"])

        if period.get("days"):
            upstream_query.days(period["days"])
        elif period.get("start_date") and period.get("end_date"):
            upstream_query.date_range(period["start_date"], period["end_date"])

        upstream_query.time_key(time_key)
        upstream_result = await upstream_query.execute()
        upstream_df = upstream_result.to_dataframe()

        # Fetch downstream data
        downstream_query = KDMQuery(client=client)
        downstream_query.site(
            pair_config["downstream"],
            facility_type=pair_config.get("downstream_type", "water_level"),
        )
        if pair_config.get("downstream_items"):
            downstream_query.measurements(pair_config["downstream_items"])

        if period.get("days"):
            downstream_query.days(period["days"])
        elif period.get("start_date") and period.get("end_date"):
            downstream_query.date_range(period["start_date"], period["end_date"])

        downstream_query.time_key(time_key)
        downstream_result = await downstream_query.execute()
        downstream_df = downstream_result.to_dataframe()

        # Create FacilityPair with data
        pair = FacilityPair(
            upstream_name=pair_config["upstream"],
            downstream_name=pair_config["downstream"],
            upstream_type=pair_config.get("upstream_type", "dam"),
            downstream_type=pair_config.get("downstream_type", "water_level"),
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        return pair

    async def _execute_query(self, client: KDMClient, config: Dict[str, Any]):
        """
        Execute template with KDMQuery.

        Args:
            client: KDM client
            config: Effective configuration

        Returns:
            QueryResult or BatchResult
        """
        query = KDMQuery(client=client)

        # Add sites
        for site in config.get("sites", []):
            query.site(
                site["site_name"], facility_type=site.get("facility_type", "dam")
            )

        # Add measurements
        if config.get("measurements"):
            query.measurements(config["measurements"])

        # Add period
        period = config.get("period", {})
        if period.get("days"):
            query.days(period["days"])
        elif period.get("start_date") and period.get("end_date"):
            query.date_range(period["start_date"], period["end_date"])

        # Set time_key if specified
        if config.get("time_key"):
            query.time_key(config["time_key"])

        # Execute
        return await query.execute()

    def _merge_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge template config with parameter overrides.

        Args:
            params: Parameter overrides

        Returns:
            Effective configuration
        """
        effective = self._config.copy()

        # Override period parameters
        if "days" in params:
            effective["period"]["days"] = params["days"]
        if "start_date" in params:
            effective["period"]["start_date"] = params["start_date"]
        if "end_date" in params:
            effective["period"]["end_date"] = params["end_date"]

        # Override time_key
        if "time_key" in params:
            effective["time_key"] = params["time_key"]

        # Override measurements
        if "measurements" in params:
            effective["measurements"] = params["measurements"]

        return effective

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert template to dictionary.

        Returns:
            Configuration dictionary
        """
        return self._config.copy()

    def save_yaml(self, filepath: str):
        """
        Save template as YAML file.

        Args:
            filepath: Path to YAML file

        Example:
            >>> template.save_yaml("my_template.yaml")
        """
        from .loaders import save_yaml

        save_yaml(self, filepath)

    def __repr__(self) -> str:
        """String representation"""
        return f"Template(name='{self.name}')"
