"""
Fluent API for building KDM queries

This module provides a chainable query builder for constructing
and executing KDM data queries with a clean, readable syntax.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from copy import deepcopy

from .client import KDMClient
from .results import QueryResult, BatchResult

logger = logging.getLogger(__name__)


class KDMQuery:
    """
    Fluent API for building KDM queries

    Example:
        >>> query = KDMQuery()
        >>> result = await query \\
        ...     .site("소양강댐", facility_type="dam") \\
        ...     .measurements(["저수율", "유입량"]) \\
        ...     .days(7) \\
        ...     .execute()
        >>> df = result.to_dataframe()
    """

    def __init__(self, client: Optional[KDMClient] = None):
        """
        Initialize KDMQuery

        Args:
            client: Optional KDMClient instance. If not provided, a new client
                   will be created and auto-connected on first query.
        """
        self._client = client
        self._batch_queries: List[Dict[str, Any]] = []

        # Reset all query parameters
        self.reset()

    def reset(self) -> "KDMQuery":
        """
        Reset all query parameters

        Returns:
            Self for method chaining
        """
        self._site_name: Optional[str] = None
        self._facility_type: Optional[str] = None
        self._measurement_items: List[str] = []
        self._time_key: Optional[str] = None
        self._days: Optional[int] = None
        self._start_date: Optional[str] = None
        self._end_date: Optional[str] = None
        self._comparison_mode: bool = False
        self._include_comparison: bool = False
        self._include_flood: bool = False
        self._include_drought: bool = False
        self._include_discharge: bool = False
        self._include_weather: bool = False
        self._include_quality: bool = False
        self._include_safety: bool = False
        self._include_related: bool = False

        return self

    def site(self, name: str, facility_type: str = "dam") -> "KDMQuery":
        """
        Set the facility/site to query

        Args:
            name: Facility name (e.g., "소양강댐")
            facility_type: Facility type (dam, water_level, rainfall, weather, water_quality)

        Returns:
            Self for method chaining

        Example:
            >>> query.site("소양강댐", facility_type="dam")
        """
        self._site_name = name
        self._facility_type = facility_type
        return self

    def measurements(self, items: List[str]) -> "KDMQuery":
        """
        Set measurement items to query

        Args:
            items: List of measurement items (e.g., ["저수율", "유입량"])

        Returns:
            Self for method chaining

        Example:
            >>> query.measurements(["저수율", "유입량"])
        """
        self._measurement_items = items
        return self

    def days(self, n: int) -> "KDMQuery":
        """
        Query data for the last N days

        Args:
            n: Number of days

        Returns:
            Self for method chaining

        Example:
            >>> query.days(7)  # Last 7 days
        """
        self._days = n
        # Clear date range if days is set
        self._start_date = None
        self._end_date = None
        return self

    def date_range(self, start_date: str, end_date: str) -> "KDMQuery":
        """
        Set specific date range

        Args:
            start_date: Start date (YYYYMMDD or YYYY-MM-DD)
            end_date: End date (YYYYMMDD or YYYY-MM-DD)

        Returns:
            Self for method chaining

        Example:
            >>> query.date_range("2024-01-01", "2024-01-07")
        """
        self._start_date = start_date
        self._end_date = end_date
        # Clear days if date range is set
        self._days = None
        return self

    def time_key(self, key: str) -> "KDMQuery":
        """
        Set time key (temporal resolution)

        Args:
            key: Time key (h_1, d_1, mt_1, or "auto" for fallback)

        Returns:
            Self for method chaining

        Example:
            >>> query.time_key("h_1")  # Hourly data
        """
        self._time_key = key
        return self

    def compare_with_previous_year(self) -> "KDMQuery":
        """
        Enable year-over-year comparison

        When enabled, the query will fetch data for both the current period
        and the same period in the previous year.

        Returns:
            Self for method chaining

        Example:
            >>> query.compare_with_previous_year()
        """
        self._comparison_mode = True
        self._include_comparison = True
        return self

    def include_comparison(self) -> "KDMQuery":
        """Include year-over-year comparison data"""
        self._include_comparison = True
        return self

    def include_flood(self) -> "KDMQuery":
        """Include flood-related data"""
        self._include_flood = True
        return self

    def include_drought(self) -> "KDMQuery":
        """Include drought-related data"""
        self._include_drought = True
        return self

    def include_discharge(self) -> "KDMQuery":
        """Include discharge details"""
        self._include_discharge = True
        return self

    def include_weather(self) -> "KDMQuery":
        """Include weather data"""
        self._include_weather = True
        return self

    def include_quality(self) -> "KDMQuery":
        """Include water quality data"""
        self._include_quality = True
        return self

    def include_safety(self) -> "KDMQuery":
        """Include dam safety data"""
        self._include_safety = True
        return self

    def include_related(self) -> "KDMQuery":
        """Include related facility data"""
        self._include_related = True
        return self

    def add(self) -> "KDMQuery":
        """
        Add current query to batch queue and reset for next query

        Returns:
            Self for method chaining

        Example:
            >>> query.site("소양강댐").measurements(["저수율"]).days(7).add()
            >>> query.site("충주댐").measurements(["저수율"]).days(7).add()
            >>> results = await query.execute_batch()
        """
        # Validate current query
        if not self._site_name:
            raise ValueError("site_name is required before adding to batch")

        # Store current query parameters
        query_params = {
            "site_name": self._site_name,
            "facility_type": self._facility_type,
            "measurement_items": (
                self._measurement_items.copy() if self._measurement_items else None
            ),
            "time_key": self._time_key,
            "days": self._days,
            "start_date": self._start_date,
            "end_date": self._end_date,
            "include_comparison": self._include_comparison,
            "include_flood": self._include_flood,
            "include_drought": self._include_drought,
            "include_discharge": self._include_discharge,
            "include_weather": self._include_weather,
            "include_quality": self._include_quality,
            "include_safety": self._include_safety,
            "include_related": self._include_related,
        }

        self._batch_queries.append(query_params)

        # Reset for next query (but keep client)
        client = self._client
        self.reset()
        self._client = client

        return self

    async def execute(self) -> QueryResult:
        """
        Execute the query and return results

        Returns:
            QueryResult with query results

        Raises:
            ValueError: If required parameters are missing

        Example:
            >>> result = await query.execute()
            >>> df = result.to_dataframe()
        """
        # Validate required parameters
        if not self._site_name:
            raise ValueError("site_name is required")

        # Auto-connect if needed
        if self._client is None:
            self._client = KDMClient()
            await self._client.connect()
        elif not self._client.is_connected():
            await self._client.connect()

        assert self._client is not None, "Client should be initialized"

        # Build arguments for get_water_data
        args: Dict[str, Any] = {
            "site_name": self._site_name,
        }

        if self._facility_type:
            args["facility_type"] = self._facility_type
        if self._measurement_items:
            args["measurement_items"] = self._measurement_items
        if self._time_key:
            args["time_key"] = self._time_key
        if self._days is not None:
            args["days"] = self._days
        if self._start_date:
            args["start_date"] = self._start_date
        if self._end_date:
            args["end_date"] = self._end_date

        # Add boolean flags
        if self._include_comparison:
            args["include_comparison"] = True
        if self._include_flood:
            args["include_flood"] = True
        if self._include_drought:
            args["include_drought"] = True
        if self._include_discharge:
            args["include_discharge"] = True
        if self._include_weather:
            args["include_weather"] = True
        if self._include_quality:
            args["include_quality"] = True
        if self._include_safety:
            args["include_safety"] = True
        if self._include_related:
            args["include_related"] = True

        try:
            logger.info(f"[KDMQuery] Executing query for {self._site_name}")

            # Execute query
            raw_result = await self._client.get_water_data(**args)

            # Handle comparison mode
            comparison_data = None
            if self._comparison_mode:
                comparison_data = await self._fetch_comparison_data(args)

            # Wrap in QueryResult
            result = QueryResult(
                raw_data=raw_result,
                site_name=self._site_name,
                facility_type=self._facility_type,
                measurement_items=self._measurement_items,
                comparison_data=comparison_data,
            )

            logger.info(f"[KDMQuery] Query completed: success={result.success}")

            return result

        except Exception as e:
            logger.error(f"[KDMQuery] Query failed: {e}")

            # Return QueryResult with error
            return QueryResult(
                raw_data={"success": False, "message": str(e), "data": []},
                site_name=self._site_name,
                facility_type=self._facility_type,
                measurement_items=self._measurement_items,
            )

    async def _fetch_comparison_data(
        self, current_args: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch comparison data for previous year

        Args:
            current_args: Arguments for current query

        Returns:
            Dictionary with current_year and previous_year data
        """
        assert self._client is not None, "Client should be initialized"
        try:
            # Calculate previous year dates
            if self._start_date and self._end_date:
                # Parse dates
                start_dt = datetime.strptime(
                    self._start_date.replace("-", ""), "%Y%m%d"
                )
                end_dt = datetime.strptime(self._end_date.replace("-", ""), "%Y%m%d")

                # Subtract one year
                prev_start_dt = start_dt.replace(year=start_dt.year - 1)
                prev_end_dt = end_dt.replace(year=end_dt.year - 1)

                # Format back to string
                prev_start = prev_start_dt.strftime("%Y-%m-%d")
                prev_end = prev_end_dt.strftime("%Y-%m-%d")

                # Query previous year data
                prev_args = current_args.copy()
                prev_args["start_date"] = prev_start
                prev_args["end_date"] = prev_end
                prev_args.pop("days", None)

                prev_result = await self._client.get_water_data(**prev_args)

                return {
                    "current_year": current_args.get("start_date", ""),
                    "previous_year": prev_start,
                    "previous_year_data": prev_result,
                }

            else:
                logger.warning(
                    "[KDMQuery] Comparison mode requires start_date and end_date"
                )
                return None

        except Exception as e:
            logger.error(f"[KDMQuery] Failed to fetch comparison data: {e}")
            return None

    async def execute_batch(self, parallel: bool = False) -> BatchResult:
        """
        Execute all queued queries

        Args:
            parallel: If True, execute queries in parallel. Default is False (sequential).

        Returns:
            BatchResult containing all query results

        Example:
            >>> query.site("소양강댐").days(7).add()
            >>> query.site("충주댐").days(7).add()
            >>> results = await query.execute_batch(parallel=True)
            >>> combined_df = results.aggregate()
        """
        # Auto-connect if needed
        if self._client is None:
            self._client = KDMClient()
            await self._client.connect()
        elif not self._client.is_connected():
            await self._client.connect()

        assert self._client is not None, "Client should be initialized"

        results: Dict[str, QueryResult] = {}

        if parallel:
            # Execute all queries in parallel
            tasks = []
            site_names = []

            for query_params in self._batch_queries:
                site_name = query_params["site_name"]
                site_names.append(site_name)

                # Build query
                task = self._execute_single_query(query_params)
                tasks.append(task)

            # Wait for all tasks
            logger.info(f"[KDMQuery] Executing {len(tasks)} queries in parallel")
            query_results: List[Union[QueryResult, BaseException]] = await asyncio.gather(
                *tasks, return_exceptions=True
            )

            # Collect results
            for site_name, result in zip(site_names, query_results):
                if isinstance(result, Exception):
                    logger.error(f"[KDMQuery] Query failed for {site_name}: {result}")
                    results[site_name] = QueryResult(
                        raw_data={"success": False, "message": str(result), "data": []},
                        site_name=site_name,
                    )
                elif isinstance(result, QueryResult):
                    results[site_name] = result

        else:
            # Execute sequentially
            logger.info(
                f"[KDMQuery] Executing {len(self._batch_queries)} queries sequentially"
            )

            for query_params in self._batch_queries:
                site_name = query_params["site_name"]

                try:
                    result = await self._execute_single_query(query_params)
                    results[site_name] = result

                except Exception as e:
                    logger.error(f"[KDMQuery] Query failed for {site_name}: {e}")
                    results[site_name] = QueryResult(
                        raw_data={"success": False, "message": str(e), "data": []},
                        site_name=site_name,
                    )

        # Clear batch queue
        self._batch_queries.clear()

        return BatchResult(results=results)

    async def _execute_single_query(self, query_params: Dict[str, Any]) -> QueryResult:
        """
        Execute a single query from batch

        Args:
            query_params: Query parameters

        Returns:
            QueryResult
        """
        assert self._client is not None, "Client should be initialized"
        # Build arguments
        args = {
            "site_name": query_params["site_name"],
        }

        # Add optional parameters
        for key in [
            "facility_type",
            "measurement_items",
            "time_key",
            "days",
            "start_date",
            "end_date",
            "include_comparison",
            "include_flood",
            "include_drought",
            "include_discharge",
            "include_weather",
            "include_quality",
            "include_safety",
            "include_related",
        ]:
            if query_params.get(key) is not None:
                args[key] = query_params[key]

        # Execute
        raw_result = await self._client.get_water_data(**args)

        # Wrap in QueryResult
        return QueryResult(
            raw_data=raw_result,
            site_name=query_params["site_name"],
            facility_type=query_params.get("facility_type"),
            measurement_items=query_params.get("measurement_items", []),
        )

    def clone(self) -> "KDMQuery":
        """
        Create a deep copy of this query

        Returns:
            New KDMQuery instance with same parameters

        Example:
            >>> query2 = query1.clone()
            >>> query2.site("충주댐")  # Doesn't affect query1
        """
        new_query = KDMQuery(client=self._client)

        # Deep copy all parameters
        new_query._site_name = self._site_name
        new_query._facility_type = self._facility_type
        new_query._measurement_items = self._measurement_items.copy()
        new_query._time_key = self._time_key
        new_query._days = self._days
        new_query._start_date = self._start_date
        new_query._end_date = self._end_date
        new_query._comparison_mode = self._comparison_mode
        new_query._include_comparison = self._include_comparison
        new_query._include_flood = self._include_flood
        new_query._include_drought = self._include_drought
        new_query._include_discharge = self._include_discharge
        new_query._include_weather = self._include_weather
        new_query._include_quality = self._include_quality
        new_query._include_safety = self._include_safety
        new_query._include_related = self._include_related
        new_query._batch_queries = deepcopy(self._batch_queries)

        return new_query
