"""
Query result classes for KDM SDK

This module provides classes for handling query results with convenient
conversion methods to various formats (DataFrame, dict, list).
"""

import logging
from typing import Any, Dict, List, Optional, Iterator, Tuple

logger = logging.getLogger(__name__)


class QueryResult:
    """
    Result of a single KDM query

    Provides convenient access to query results and conversion methods.

    Example:
        >>> result = await query.execute()
        >>> df = result.to_dataframe()
        >>> data_dict = result.to_dict()
        >>> data_list = result.to_list()
    """

    def __init__(
        self,
        raw_data: Dict[str, Any],
        site_name: Optional[str] = None,
        facility_type: Optional[str] = None,
        measurement_items: Optional[List[str]] = None,
        comparison_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize QueryResult

        Args:
            raw_data: Raw response from KDM MCP server
            site_name: Name of queried facility
            facility_type: Type of facility
            measurement_items: List of measurement items
            comparison_data: Optional year-over-year comparison data
        """
        self._raw_data = raw_data
        self._site_name = site_name
        self._facility_type = facility_type
        self._measurement_items = measurement_items or []
        self._comparison_data = comparison_data

    @property
    def success(self) -> bool:
        """Whether the query was successful"""
        return self._raw_data.get("success", False)

    @property
    def data(self) -> List[Dict[str, Any]]:
        """List of data records"""
        return self._raw_data.get("data", [])

    @property
    def site_name(self) -> Optional[str]:
        """Name of queried facility"""
        # Try to get from raw data first, fallback to stored value
        if self._raw_data.get("site"):
            return self._raw_data["site"].get("site_name")
        return self._site_name

    @property
    def facility_type(self) -> Optional[str]:
        """Type of facility"""
        if self._raw_data.get("site"):
            return self._raw_data["site"].get("facility_type")
        return self._facility_type

    @property
    def measurement_item(self) -> Optional[str]:
        """Primary measurement item"""
        # Get from raw data
        if self._raw_data.get("measurement_item"):
            return self._raw_data["measurement_item"]

        # Or from measurement_items list
        if self._measurement_items and len(self._measurement_items) > 0:
            return self._measurement_items[0]

        return None

    @property
    def message(self) -> Optional[str]:
        """Result message (if any)"""
        return self._raw_data.get("message")

    @property
    def comparison_data(self) -> Optional[Dict[str, Any]]:
        """Year-over-year comparison data (if requested)"""
        return self._comparison_data

    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata about the query and results"""
        return self._raw_data.get("metadata", {})

    def __len__(self) -> int:
        """Number of data records"""
        return len(self.data)

    def __bool__(self) -> bool:
        """True if query was successful"""
        return self.success

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary

        Returns:
            Dictionary containing all result data

        Example:
            >>> result_dict = result.to_dict()
            >>> print(result_dict["success"])
        """
        return {
            "success": self.success,
            "data": self.data,
            "site_name": self.site_name,
            "facility_type": self.facility_type,
            "measurement_item": self.measurement_item,
            "message": self.message,
            "metadata": self.metadata,
            "comparison_data": self.comparison_data,
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """
        Convert result data to list

        Returns:
            List of data records

        Example:
            >>> data_list = result.to_list()
            >>> for record in data_list:
            ...     print(record["datetime"], record["values"])
        """
        return self.data

    def to_dataframe(self):
        """
        Convert result to pandas DataFrame

        The DataFrame will have a datetime column and columns for each
        measurement item with their values.

        Returns:
            pandas.DataFrame with query results

        Raises:
            ImportError: If pandas is not installed

        Example:
            >>> df = result.to_dataframe()
            >>> print(df.head())
            >>> df.plot(x="datetime", y="저수율")
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for DataFrame conversion. "
                "Install with: pip install pandas"
            )

        if not self.success or len(self.data) == 0:
            # Return empty DataFrame with expected structure
            return pd.DataFrame(columns=["datetime"])

        # Convert data to DataFrame
        # Handle V4 data structure: { datetime, values: { "측정항목": { value, unit } } }
        rows = []

        for record in self.data:
            row = {}

            # Add datetime
            if "datetime" in record:
                row["datetime"] = record["datetime"]
            elif "time_key" in record:
                row["datetime"] = record["time_key"]

            # Extract values
            if "values" in record and isinstance(record["values"], dict):
                # V4 structure
                for measurement_name, measurement_data in record["values"].items():
                    if isinstance(measurement_data, dict):
                        # Store value with measurement name as column
                        row[measurement_name] = measurement_data.get("value")

                        # Store unit in separate column (optional)
                        unit = measurement_data.get("unit")
                        if unit:
                            row[f"{measurement_name}_unit"] = unit
                    else:
                        # Simple value
                        row[measurement_name] = measurement_data

            # Handle simple structure (legacy)
            elif "value" in record:
                measurement_name = self.measurement_item or "value"
                row[measurement_name] = record["value"]

                if "unit" in record:
                    row[f"{measurement_name}_unit"] = record["unit"]

            rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(rows)

        # Try to convert datetime column to datetime type
        if "datetime" in df.columns:
            try:
                df["datetime"] = pd.to_datetime(df["datetime"])
            except Exception as e:
                logger.warning(f"Failed to convert datetime column: {e}")

        return df

    def to_csv(self, filepath: str, **kwargs):
        """
        Export result data to CSV file

        Args:
            filepath: Path to output CSV file
            **kwargs: Additional arguments passed to pandas.to_csv()

        Example:
            >>> result.to_csv('soyang_data.csv')
            >>> result.to_csv('data.csv', index=False, encoding='utf-8-sig')

        Note:
            Uses 'utf-8-sig' encoding by default for proper Korean text handling in Excel.
        """
        df = self.to_dataframe()

        # Set default encoding for Korean text if not specified
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8-sig"

        # Don't save index by default if not specified
        if "index" not in kwargs:
            kwargs["index"] = False

        df.to_csv(filepath, **kwargs)
        logger.info(f"Exported {len(df)} records to {filepath}")

    def to_excel(self, filepath: str, sheet_name: str = "Data", **kwargs):
        """
        Export result data to Excel file

        Args:
            filepath: Path to output Excel file (.xlsx)
            sheet_name: Name of the Excel sheet (default: 'Data')
            **kwargs: Additional arguments passed to pandas.to_excel()

        Raises:
            ImportError: If openpyxl is not installed

        Example:
            >>> result.to_excel('soyang_data.xlsx')
            >>> result.to_excel('data.xlsx', sheet_name='소양강댐', index=False)
        """
        try:
            df = self.to_dataframe()
        except ImportError:
            raise

        try:
            # Don't save index by default if not specified
            if "index" not in kwargs:
                kwargs["index"] = False

            df.to_excel(filepath, sheet_name=sheet_name, engine="openpyxl", **kwargs)
            logger.info(f"Exported {len(df)} records to {filepath}")
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel export. "
                "Install with: pip install openpyxl or pip install kdm-sdk[analyst]"
            )

    def to_parquet(self, filepath: str, **kwargs):
        """
        Export result data to Parquet file (efficient columnar storage)

        Args:
            filepath: Path to output Parquet file (.parquet)
            **kwargs: Additional arguments passed to pandas.to_parquet()

        Raises:
            ImportError: If pyarrow is not installed

        Example:
            >>> result.to_parquet('soyang_data.parquet')
            >>> result.to_parquet('data.parquet', compression='snappy')

        Note:
            Parquet format is more efficient than CSV for large datasets
            and preserves data types.
        """
        try:
            df = self.to_dataframe()
        except ImportError:
            raise

        try:
            df.to_parquet(filepath, engine="pyarrow", **kwargs)
            logger.info(f"Exported {len(df)} records to {filepath}")
        except ImportError:
            raise ImportError(
                "pyarrow is required for Parquet export. "
                "Install with: pip install pyarrow or pip install kdm-sdk[analyst]"
            )

    def to_json(self, filepath: str, orient: str = "records", **kwargs):
        """
        Export result data to JSON file

        Args:
            filepath: Path to output JSON file
            orient: JSON orientation ('records', 'index', 'columns', etc.)
            **kwargs: Additional arguments passed to pandas.to_json()

        Example:
            >>> result.to_json('soyang_data.json')
            >>> result.to_json('data.json', orient='records', indent=2)

        Note:
            Uses force_ascii=False by default for proper Korean text.
        """
        df = self.to_dataframe()

        # Don't escape Korean characters
        if "force_ascii" not in kwargs:
            kwargs["force_ascii"] = False

        df.to_json(filepath, orient=orient, **kwargs)
        logger.info(f"Exported {len(df)} records to {filepath}")

    def __repr__(self) -> str:
        """String representation"""
        status = "success" if self.success else "failed"
        count = len(self.data)
        return f"<QueryResult {status} site={self.site_name} records={count}>"


class BatchResult:
    """
    Result of a batch query

    Provides access to multiple query results by site name.

    Example:
        >>> results = await query.execute_batch()
        >>> for site_name, result in results:
        ...     print(f"{site_name}: {len(result)} records")
        >>> combined_df = results.aggregate()
    """

    def __init__(self, results: Dict[str, QueryResult]):
        """
        Initialize BatchResult

        Args:
            results: Dictionary mapping site names to QueryResult instances
        """
        self.results = results

    def __getitem__(self, site_name: str) -> QueryResult:
        """
        Get result by site name

        Args:
            site_name: Name of facility

        Returns:
            QueryResult for that facility

        Example:
            >>> result = batch_results["소양강댐"]
        """
        return self.results[site_name]

    def __contains__(self, site_name: str) -> bool:
        """
        Check if site is in results

        Args:
            site_name: Name of facility

        Returns:
            True if site has results

        Example:
            >>> if "소양강댐" in batch_results:
            ...     print("Found!")
        """
        return site_name in self.results

    def __len__(self) -> int:
        """Number of query results"""
        return len(self.results)

    def __iter__(self) -> Iterator[Tuple[str, QueryResult]]:
        """
        Iterate over results

        Yields:
            Tuple of (site_name, QueryResult)

        Example:
            >>> for site_name, result in batch_results:
            ...     print(site_name, result.success)
        """
        return iter(self.results.items())

    def get(
        self, site_name: str, default: Optional[QueryResult] = None
    ) -> Optional[QueryResult]:
        """
        Get result by site name with default

        Args:
            site_name: Name of facility
            default: Default value if not found

        Returns:
            QueryResult or default

        Example:
            >>> result = batch_results.get("소양강댐")
        """
        return self.results.get(site_name, default)

    def keys(self) -> List[str]:
        """Get all site names"""
        return list(self.results.keys())

    def values(self) -> List[QueryResult]:
        """Get all QueryResult instances"""
        return list(self.results.values())

    def items(self) -> List[Tuple[str, QueryResult]]:
        """Get all (site_name, QueryResult) pairs"""
        return list(self.results.items())

    def aggregate(self):
        """
        Aggregate all results into a single DataFrame

        Each site's data will be included with a column indicating the site name.

        Returns:
            pandas.DataFrame with combined data from all sites

        Example:
            >>> combined_df = batch_results.aggregate()
            >>> print(combined_df.groupby("site_name").mean())
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for DataFrame aggregation. "
                "Install with: pip install pandas"
            )

        dfs = []

        for site_name, result in self.results.items():
            if result.success and len(result.data) > 0:
                df = result.to_dataframe()

                # Add site_name column
                df["site_name"] = site_name

                # Add facility_type column
                if result.facility_type:
                    df["facility_type"] = result.facility_type

                dfs.append(df)

        if len(dfs) == 0:
            # Return empty DataFrame
            return pd.DataFrame()

        # Concatenate all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)

        return combined_df

    def to_csv(self, filepath: str, **kwargs):
        """
        Export aggregated batch results to CSV file

        Combines all site data with site_name column and exports to CSV.

        Args:
            filepath: Path to output CSV file
            **kwargs: Additional arguments passed to pandas.to_csv()

        Example:
            >>> batch_results.to_csv('all_dams.csv')
            >>> batch_results.to_csv('dams.csv', index=False)
        """
        df = self.aggregate()

        # Set default encoding for Korean text if not specified
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8-sig"

        # Don't save index by default if not specified
        if "index" not in kwargs:
            kwargs["index"] = False

        df.to_csv(filepath, **kwargs)
        logger.info(
            f"Exported {len(df)} records from {len(self.results)} sites to {filepath}"
        )

    def to_excel(self, filepath: str, sheet_name: str = "Data", **kwargs):
        """
        Export aggregated batch results to Excel file

        Combines all site data with site_name column and exports to Excel.

        Args:
            filepath: Path to output Excel file (.xlsx)
            sheet_name: Name of the Excel sheet (default: 'Data')
            **kwargs: Additional arguments passed to pandas.to_excel()

        Raises:
            ImportError: If openpyxl is not installed

        Example:
            >>> batch_results.to_excel('all_dams.xlsx')
            >>> batch_results.to_excel('dams.xlsx', sheet_name='댐 비교')
        """
        try:
            df = self.aggregate()
        except ImportError:
            raise

        try:
            # Don't save index by default if not specified
            if "index" not in kwargs:
                kwargs["index"] = False

            df.to_excel(filepath, sheet_name=sheet_name, engine="openpyxl", **kwargs)
            logger.info(
                f"Exported {len(df)} records from {len(self.results)} sites to {filepath}"
            )
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel export. "
                "Install with: pip install openpyxl or pip install kdm-sdk[analyst]"
            )

    def to_parquet(self, filepath: str, **kwargs):
        """
        Export aggregated batch results to Parquet file

        Combines all site data with site_name column and exports to Parquet.

        Args:
            filepath: Path to output Parquet file (.parquet)
            **kwargs: Additional arguments passed to pandas.to_parquet()

        Raises:
            ImportError: If pyarrow is not installed

        Example:
            >>> batch_results.to_parquet('all_dams.parquet')
        """
        try:
            df = self.aggregate()
        except ImportError:
            raise

        try:
            df.to_parquet(filepath, engine="pyarrow", **kwargs)
            logger.info(
                f"Exported {len(df)} records from {len(self.results)} sites to {filepath}"
            )
        except ImportError:
            raise ImportError(
                "pyarrow is required for Parquet export. "
                "Install with: pip install pyarrow or pip install kdm-sdk[analyst]"
            )

    def to_json(self, filepath: str, orient: str = "records", **kwargs):
        """
        Export aggregated batch results to JSON file

        Combines all site data with site_name column and exports to JSON.

        Args:
            filepath: Path to output JSON file
            orient: JSON orientation ('records', 'index', 'columns', etc.)
            **kwargs: Additional arguments passed to pandas.to_json()

        Example:
            >>> batch_results.to_json('all_dams.json')
            >>> batch_results.to_json('dams.json', orient='records', indent=2)
        """
        df = self.aggregate()

        # Don't escape Korean characters
        if "force_ascii" not in kwargs:
            kwargs["force_ascii"] = False

        df.to_json(filepath, orient=orient, **kwargs)
        logger.info(
            f"Exported {len(df)} records from {len(self.results)} sites to {filepath}"
        )

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert all results to dictionary

        Returns:
            Dictionary mapping site names to result dictionaries

        Example:
            >>> all_results = batch_results.to_dict()
            >>> print(all_results["소양강댐"]["success"])
        """
        return {
            site_name: result.to_dict() for site_name, result in self.results.items()
        }

    def filter_successful(self) -> "BatchResult":
        """
        Get only successful results

        Returns:
            New BatchResult containing only successful queries

        Example:
            >>> successful = batch_results.filter_successful()
            >>> print(f"Success rate: {len(successful)}/{len(batch_results)}")
        """
        successful_results = {
            site_name: result
            for site_name, result in self.results.items()
            if result.success
        }

        return BatchResult(results=successful_results)

    def filter_failed(self) -> "BatchResult":
        """
        Get only failed results

        Returns:
            New BatchResult containing only failed queries

        Example:
            >>> failed = batch_results.filter_failed()
            >>> for site_name, result in failed:
            ...     print(f"{site_name}: {result.message}")
        """
        failed_results = {
            site_name: result
            for site_name, result in self.results.items()
            if not result.success
        }

        return BatchResult(results=failed_results)

    def __repr__(self) -> str:
        """String representation"""
        total = len(self.results)
        successful = sum(1 for r in self.results.values() if r.success)
        return f"<BatchResult total={total} successful={successful}>"
