"""
FacilityPair and correlation analysis for upstream-downstream relationships

This module provides tools for analyzing relationships between upstream facilities
(e.g., dams) and downstream monitoring stations (e.g., water level stations).

Example:
    Analyze how 소양강댐 dam outflow affects 춘천 water level station:

    >>> pair = FacilityPair(
    ...     upstream_name="소양강댐",
    ...     downstream_name="춘천",
    ...     upstream_data=dam_df,
    ...     downstream_data=station_df
    ... )
    >>> result = pair.find_optimal_lag(max_lag_hours=10)
    >>> print(f"Optimal lag: {result.lag_hours} hours, correlation: {result.correlation:.3f}")
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class PairResult:
    """
    Results from correlation analysis between upstream and downstream facilities

    Attributes:
        upstream_name: Name of upstream facility (e.g., "소양강댐")
        downstream_name: Name of downstream facility (e.g., "춘천")
        correlation: Correlation coefficient (-1 to 1)
        lag_hours: Time lag in hours (positive = downstream lags upstream)
        sample_size: Number of data points used in calculation
        upstream_column: Name of upstream measurement column
        downstream_column: Name of downstream measurement column
        p_value: Statistical significance (if calculated)
    """

    upstream_name: str
    downstream_name: str
    correlation: float
    lag_hours: float
    sample_size: int
    upstream_column: Optional[str] = None
    downstream_column: Optional[str] = None
    p_value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"PairResult(upstream={self.upstream_name}, "
            f"downstream={self.downstream_name}, "
            f"correlation={self.correlation:.3f}, "
            f"lag={self.lag_hours}h, "
            f"n={self.sample_size})"
        )


class FacilityPair:
    """
    Analyzes relationship between upstream and downstream water facilities

    This class handles time series alignment with lag, correlation calculation,
    and data export for analysis of cause-effect relationships.

    Example:
        >>> # Analyze dam outflow effect on downstream water level
        >>> pair = FacilityPair(
        ...     upstream_name="소양강댐",
        ...     downstream_name="춘천",
        ...     upstream_type="dam",
        ...     downstream_type="water_level",
        ...     upstream_data=dam_outflow_df,
        ...     downstream_data=water_level_df
        ... )
        >>> # Find optimal time lag
        >>> result = pair.find_optimal_lag(max_lag_hours=12)
        >>> print(f"Water from dam reaches station in {result.lag_hours} hours")
        >>> # Export aligned data for further analysis
        >>> df = pair.to_dataframe(lag_hours=result.lag_hours)
        >>> df.to_csv('aligned_data.csv')
    """

    def __init__(
        self,
        upstream_name: Optional[str] = None,
        downstream_name: Optional[str] = None,
        upstream_type: Optional[str] = None,
        downstream_type: Optional[str] = None,
        upstream_data: Optional[pd.DataFrame] = None,
        downstream_data: Optional[pd.DataFrame] = None,
    ):
        """
        Initialize FacilityPair

        Args:
            upstream_name: Name of upstream facility (required)
            downstream_name: Name of downstream facility (required)
            upstream_type: Type of upstream facility (dam, water_level, etc.)
            downstream_type: Type of downstream facility
            upstream_data: DataFrame with upstream measurements (datetime index)
            downstream_data: DataFrame with downstream measurements (datetime index)

        Raises:
            ValueError: If required parameters are missing
        """
        if upstream_name is None:
            raise ValueError("upstream_name is required")
        if downstream_name is None:
            raise ValueError("downstream_name is required")

        self.upstream_name = upstream_name
        self.downstream_name = downstream_name
        self.upstream_type = upstream_type
        self.downstream_type = downstream_type
        self.upstream_data = upstream_data
        self.downstream_data = downstream_data

        # Validate DataFrames if provided
        if upstream_data is not None and not isinstance(
            upstream_data.index, pd.DatetimeIndex
        ):
            logger.warning(
                f"upstream_data for {upstream_name} does not have DatetimeIndex"
            )

        if downstream_data is not None and not isinstance(
            downstream_data.index, pd.DatetimeIndex
        ):
            logger.warning(
                f"downstream_data for {downstream_name} does not have DatetimeIndex"
            )

    def align_with_lag(
        self,
        lag_hours: float = 0,
        upstream_column: Optional[str] = None,
        downstream_column: Optional[str] = None,
        dropna: bool = True,
    ) -> pd.DataFrame:
        """
        Align upstream and downstream time series with specified lag

        The lag represents the travel time from upstream to downstream.
        For example, with lag_hours=2:
        - upstream[10:00] will be aligned with downstream[12:00]
        - This models the 2-hour delay for water to travel downstream

        Args:
            lag_hours: Time lag in hours (positive = downstream lags upstream)
            upstream_column: Column name to use from upstream data (auto-detect if None)
            downstream_column: Column name to use from downstream data (auto-detect if None)
            dropna: If True, drop rows with missing values

        Returns:
            DataFrame with columns 'upstream' and 'downstream', datetime index

        Raises:
            ValueError: If no overlapping time range exists
        """
        if self.upstream_data is None or self.downstream_data is None:
            raise ValueError("Both upstream_data and downstream_data must be provided")

        # Select columns
        upstream_series = self._select_column(
            self.upstream_data, upstream_column, "upstream"
        )
        downstream_series = self._select_column(
            self.downstream_data, downstream_column, "downstream"
        )

        # Apply lag by shifting downstream index backward
        # or equivalently, shifting upstream index forward
        lag_offset = pd.Timedelta(hours=lag_hours)

        if lag_hours >= 0:
            # Positive lag: shift upstream forward
            # upstream[t] aligns with downstream[t + lag]
            upstream_shifted = upstream_series.copy()
            upstream_shifted.index = upstream_shifted.index + lag_offset
            downstream_shifted = downstream_series.copy()
        else:
            # Negative lag: shift downstream forward
            # upstream[t + |lag|] aligns with downstream[t]
            upstream_shifted = upstream_series.copy()
            downstream_shifted = downstream_series.copy()
            downstream_shifted.index = downstream_shifted.index - lag_offset

        # Find common time range using nearest matching
        # For non-exact matches (e.g., fractional hour lags), use reindex with nearest
        try:
            # First try exact intersection
            common_index = upstream_shifted.index.intersection(downstream_shifted.index)

            if len(common_index) == 0:
                # Check if there's any temporal overlap at all
                upstream_start = upstream_shifted.index.min()
                upstream_end = upstream_shifted.index.max()
                downstream_start = downstream_shifted.index.min()
                downstream_end = downstream_shifted.index.max()

                # If no overlap in time ranges, raise error
                if upstream_end < downstream_start or downstream_end < upstream_start:
                    raise ValueError(
                        f"No overlapping time range between {self.upstream_name} and {self.downstream_name} "
                        f"after applying {lag_hours}h lag"
                    )

                # Fall back to reindexing with nearest neighbor (for fractional hour lags)
                # Use the smaller index range as base
                if len(upstream_shifted) <= len(downstream_shifted):
                    base_index = upstream_shifted.index
                    downstream_shifted = downstream_shifted.reindex(
                        base_index, method="nearest", tolerance=pd.Timedelta(hours=1)
                    )
                    common_index = base_index
                else:
                    base_index = downstream_shifted.index
                    upstream_shifted = upstream_shifted.reindex(
                        base_index, method="nearest", tolerance=pd.Timedelta(hours=1)
                    )
                    common_index = base_index

            if len(common_index) == 0:
                raise ValueError(
                    f"No overlapping time range between {self.upstream_name} and {self.downstream_name} "
                    f"after applying {lag_hours}h lag"
                )
        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to align time series for {self.upstream_name} and {self.downstream_name}: {e}"
            )

        # Create aligned DataFrame
        aligned = pd.DataFrame(
            {
                "upstream": upstream_shifted.loc[common_index],
                "downstream": downstream_shifted.loc[common_index],
            },
            index=common_index,
        )

        if dropna:
            aligned = aligned.dropna()

        logger.debug(
            f"Aligned {self.upstream_name} and {self.downstream_name} "
            f"with {lag_hours}h lag: {len(aligned)} points"
        )

        return aligned

    def calculate_correlation(
        self,
        lag_hours: float = 0,
        upstream_column: Optional[str] = None,
        downstream_column: Optional[str] = None,
        method: str = "pearson",
    ) -> PairResult:
        """
        Calculate correlation between upstream and downstream with specified lag

        Args:
            lag_hours: Time lag in hours
            upstream_column: Column name from upstream data
            downstream_column: Column name from downstream data
            method: Correlation method ('pearson', 'spearman', 'kendall')

        Returns:
            PairResult with correlation coefficient and metadata

        Example:
            >>> result = pair.calculate_correlation(lag_hours=2)
            >>> if result.correlation > 0.7:
            ...     print(f"Strong correlation with {result.lag_hours}h lag")
        """
        # Align time series with lag
        aligned = self.align_with_lag(
            lag_hours=lag_hours,
            upstream_column=upstream_column,
            downstream_column=downstream_column,
            dropna=True,
        )

        # Calculate correlation
        correlation = aligned["upstream"].corr(aligned["downstream"], method=method)

        # Get actual column names used
        if upstream_column is None and self.upstream_data is not None:
            upstream_column = (
                self.upstream_data.columns[0]
                if len(self.upstream_data.columns) > 0
                else None
            )

        if downstream_column is None and self.downstream_data is not None:
            downstream_column = (
                self.downstream_data.columns[0]
                if len(self.downstream_data.columns) > 0
                else None
            )

        return PairResult(
            upstream_name=self.upstream_name,
            downstream_name=self.downstream_name,
            correlation=correlation,
            lag_hours=lag_hours,
            sample_size=len(aligned),
            upstream_column=upstream_column,
            downstream_column=downstream_column,
        )

    def find_optimal_lag(
        self,
        max_lag_hours: float = 24,
        step_hours: float = 1,
        upstream_column: Optional[str] = None,
        downstream_column: Optional[str] = None,
        method: str = "pearson",
    ) -> PairResult:
        """
        Search for optimal lag that maximizes correlation

        This method tests different lag values and returns the one with
        the highest correlation coefficient.

        Args:
            max_lag_hours: Maximum lag to test (in hours)
            step_hours: Step size for lag search (in hours)
            upstream_column: Column name from upstream data
            downstream_column: Column name from downstream data
            method: Correlation method

        Returns:
            PairResult with optimal lag and correlation

        Example:
            >>> # Find how long it takes for dam release to affect downstream
            >>> result = pair.find_optimal_lag(max_lag_hours=10)
            >>> print(f"Optimal lag: {result.lag_hours} hours")
            >>> print(f"Correlation: {result.correlation:.3f}")
        """
        best_correlation = -np.inf
        best_result = None

        # Test lags from 0 to max_lag_hours
        test_lags = np.arange(0, max_lag_hours + step_hours, step_hours)

        logger.info(
            f"Searching for optimal lag between {self.upstream_name} and {self.downstream_name} "
            f"(testing {len(test_lags)} lag values)"
        )

        for lag in test_lags:
            try:
                result = self.calculate_correlation(
                    lag_hours=lag,
                    upstream_column=upstream_column,
                    downstream_column=downstream_column,
                    method=method,
                )

                if result.correlation > best_correlation:
                    best_correlation = result.correlation
                    best_result = result

            except Exception as e:
                logger.debug(f"Failed to calculate correlation at lag={lag}h: {e}")
                continue

        if best_result is None:
            raise ValueError(
                f"Could not find valid correlation for any lag between "
                f"{self.upstream_name} and {self.downstream_name}"
            )

        logger.info(
            f"Optimal lag found: {best_result.lag_hours}h "
            f"(correlation={best_result.correlation:.3f})"
        )

        return best_result

    def to_dataframe(
        self,
        lag_hours: float = 0,
        upstream_column: Optional[str] = None,
        downstream_column: Optional[str] = None,
        include_raw: bool = False,
    ) -> pd.DataFrame:
        """
        Export aligned data to DataFrame for analysis

        Args:
            lag_hours: Time lag to apply
            upstream_column: Column name from upstream data
            downstream_column: Column name from downstream data
            include_raw: If True, include non-aligned raw data as well

        Returns:
            DataFrame with aligned data, datetime index

        Example:
            >>> df = pair.to_dataframe(lag_hours=2)
            >>> df.to_csv('aligned_data.csv')
            >>> # Use for visualization or further analysis
            >>> df.plot(title='Dam Release vs Downstream Water Level')
        """
        # Get aligned data
        aligned = self.align_with_lag(
            lag_hours=lag_hours,
            upstream_column=upstream_column,
            downstream_column=downstream_column,
            dropna=True,
        )

        # Rename columns to be more descriptive
        upstream_col_name = upstream_column or (
            self.upstream_data.columns[0]
            if self.upstream_data is not None and len(self.upstream_data.columns) > 0
            else "value"
        )
        downstream_col_name = downstream_column or (
            self.downstream_data.columns[0]
            if self.downstream_data is not None
            and len(self.downstream_data.columns) > 0
            else "value"
        )

        result_df = aligned.rename(
            columns={
                "upstream": f"{self.upstream_name}_{upstream_col_name}",
                "downstream": f"{self.downstream_name}_{downstream_col_name}",
            }
        )

        return result_df

    def _select_column(
        self, df: pd.DataFrame, column_name: Optional[str], source: str
    ) -> pd.Series:
        """
        Helper to select column from DataFrame

        Args:
            df: DataFrame to select from
            column_name: Column name (None = auto-select first column)
            source: Source name for error messages

        Returns:
            Selected column as Series

        Raises:
            ValueError: If column not found or DataFrame is empty
        """
        if df is None or len(df.columns) == 0:
            raise ValueError(f"No data available for {source}")

        if column_name is None:
            # Auto-select first column
            column_name = df.columns[0]
            logger.debug(f"Auto-selected column '{column_name}' for {source}")

        if column_name not in df.columns:
            raise ValueError(
                f"Column '{column_name}' not found in {source} data. "
                f"Available: {list(df.columns)}"
            )

        return df[column_name]

    def __repr__(self) -> str:
        data_status = ""
        if self.upstream_data is not None:
            data_status += f", upstream_data={len(self.upstream_data)} rows"
        if self.downstream_data is not None:
            data_status += f", downstream_data={len(self.downstream_data)} rows"

        return (
            f"FacilityPair("
            f"upstream={self.upstream_name}, "
            f"downstream={self.downstream_name}"
            f"{data_status})"
        )
