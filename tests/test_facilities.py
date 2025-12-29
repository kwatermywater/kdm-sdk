"""
Tests for FacilityPair and correlation analysis functionality

Following TDD methodology - these tests define the expected behavior
before implementation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from kdm_sdk.facilities import FacilityPair, PairResult


class TestFacilityPairInitialization:
    """Test FacilityPair initialization and basic properties"""

    def test_init_with_upstream_downstream_names(self):
        """Should initialize with upstream and downstream facility names"""
        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_type="dam",
            downstream_type="water_level",
        )

        assert pair.upstream_name == "소양강댐"
        assert pair.downstream_name == "춘천"
        assert pair.upstream_type == "dam"
        assert pair.downstream_type == "water_level"

    def test_init_with_dataframes(self):
        """Should accept pre-loaded DataFrames"""
        # Create sample data
        dates = pd.date_range("2024-01-01", periods=24, freq="h")
        upstream_df = pd.DataFrame({"방류량": np.random.rand(24) * 100}, index=dates)
        downstream_df = pd.DataFrame({"수위": np.random.rand(24) * 10}, index=dates)

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        assert pair.upstream_data is not None
        assert pair.downstream_data is not None
        assert len(pair.upstream_data) == 24
        assert len(pair.downstream_data) == 24

    def test_init_validation_requires_names(self):
        """Should require at least upstream and downstream names"""
        with pytest.raises(ValueError, match="upstream_name.*required"):
            FacilityPair(downstream_name="춘천")

        with pytest.raises(ValueError, match="downstream_name.*required"):
            FacilityPair(upstream_name="소양강댐")


class TestLagAlignment:
    """Test time series alignment with lag"""

    def test_align_with_lag_hours(self):
        """Should align time series with hourly lag"""
        # Create test data with known pattern
        dates = pd.date_range("2024-01-01", periods=48, freq="h")

        # Upstream: Simple step function
        upstream_df = pd.DataFrame(
            {"방류량": [0] * 24 + [100] * 24}, index=dates  # Release starts at hour 24
        )

        # Downstream: Same pattern but delayed by 2 hours
        downstream_df = pd.DataFrame(
            {"수위": [5] * 26 + [15] * 22}, index=dates  # Water level rises at hour 26
        )

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        # Align with 2-hour lag
        aligned = pair.align_with_lag(lag_hours=2)

        assert aligned is not None
        assert "upstream" in aligned.columns
        assert "downstream" in aligned.columns

        # Verify alignment: upstream[t] should align with downstream[t+2]
        # After alignment, they should be more correlated
        assert len(aligned) > 0

    def test_align_with_lag_days(self):
        """Should handle daily data with day-based lag"""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")

        upstream_df = pd.DataFrame(
            {"저수율": np.sin(np.arange(30) * 0.2) * 50 + 50}, index=dates
        )

        downstream_df = pd.DataFrame(
            {"유량": np.sin((np.arange(30) - 3) * 0.2) * 100 + 100},  # 3-day lag
            index=dates,
        )

        pair = FacilityPair(
            upstream_name="충주댐",
            downstream_name="여주",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        aligned = pair.align_with_lag(lag_hours=72)  # 3 days = 72 hours

        assert aligned is not None
        assert len(aligned) > 0

    def test_align_with_negative_lag(self):
        """Should handle negative lag (downstream leads upstream)"""
        dates = pd.date_range("2024-01-01", periods=24, freq="h")

        upstream_df = pd.DataFrame({"value": range(24)}, index=dates)
        downstream_df = pd.DataFrame({"value": range(24)}, index=dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        aligned = pair.align_with_lag(lag_hours=-2)

        assert aligned is not None
        # Should shift upstream forward instead of downstream back

    def test_align_handles_missing_values(self):
        """Should handle missing values in time series"""
        dates = pd.date_range("2024-01-01", periods=24, freq="h")

        upstream_df = pd.DataFrame(
            {"value": [1.0] * 10 + [np.nan] * 4 + [1.0] * 10}, index=dates
        )

        downstream_df = pd.DataFrame({"value": [2.0] * 24}, index=dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        aligned = pair.align_with_lag(lag_hours=1, dropna=True)

        # Should drop rows with NaN when dropna=True
        assert aligned is not None
        assert aligned["upstream"].isna().sum() == 0


class TestCorrelationCalculation:
    """Test correlation calculation between upstream and downstream"""

    def test_calculate_correlation_basic(self):
        """Should calculate correlation coefficient"""
        dates = pd.date_range("2024-01-01", periods=100, freq="h")

        # Perfect positive correlation
        values = np.random.rand(100)
        upstream_df = pd.DataFrame({"value": values}, index=dates)
        downstream_df = pd.DataFrame({"value": values * 2 + 1}, index=dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        result = pair.calculate_correlation(lag_hours=0)

        assert isinstance(result, PairResult)
        assert result.correlation > 0.99  # Should be nearly perfect
        assert result.lag_hours == 0
        assert result.upstream_name == "A"
        assert result.downstream_name == "B"

    def test_calculate_correlation_with_lag(self):
        """Should find optimal lag through correlation"""
        dates = pd.date_range("2024-01-01", periods=100, freq="h")

        # Create data with 3-hour lag
        values = np.sin(np.arange(100) * 0.1)
        upstream_df = pd.DataFrame({"value": values}, index=dates)
        downstream_df = pd.DataFrame(
            {"value": np.sin((np.arange(100) - 3) * 0.1)}, index=dates  # 3-hour delay
        )

        pair = FacilityPair(
            upstream_name="댐",
            downstream_name="관측소",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        result = pair.calculate_correlation(lag_hours=3)

        # Correlation with correct lag should be high
        assert result.correlation > 0.95

    def test_find_optimal_lag(self):
        """Should search for optimal lag value"""
        dates = pd.date_range("2024-01-01", periods=200, freq="h")

        # Create data with known 5-hour lag
        values = np.sin(np.arange(200) * 0.05)
        upstream_df = pd.DataFrame({"value": values}, index=dates)
        downstream_df = pd.DataFrame(
            {"value": np.sin((np.arange(200) - 5) * 0.05)}, index=dates
        )

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        # Search for optimal lag in range
        result = pair.find_optimal_lag(max_lag_hours=10)

        assert isinstance(result, PairResult)
        # Should find lag close to 5 hours
        assert abs(result.lag_hours - 5) <= 1
        assert result.correlation > 0.95

    def test_calculate_correlation_with_column_names(self):
        """Should allow specifying which columns to correlate"""
        dates = pd.date_range("2024-01-01", periods=50, freq="h")

        upstream_df = pd.DataFrame(
            {"방류량": np.random.rand(50), "저수율": np.random.rand(50)}, index=dates
        )

        downstream_df = pd.DataFrame(
            {"수위": np.random.rand(50), "유량": np.random.rand(50)}, index=dates
        )

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        result = pair.calculate_correlation(
            lag_hours=0, upstream_column="방류량", downstream_column="수위"
        )

        assert result is not None
        assert result.upstream_column == "방류량"
        assert result.downstream_column == "수위"


class TestPairResult:
    """Test PairResult data class"""

    def test_pair_result_attributes(self):
        """Should store correlation analysis results"""
        result = PairResult(
            upstream_name="소양강댐",
            downstream_name="춘천",
            correlation=0.85,
            lag_hours=2,
            sample_size=100,
            upstream_column="방류량",
            downstream_column="수위",
        )

        assert result.upstream_name == "소양강댐"
        assert result.downstream_name == "춘천"
        assert result.correlation == 0.85
        assert result.lag_hours == 2
        assert result.sample_size == 100
        assert result.upstream_column == "방류량"
        assert result.downstream_column == "수위"

    def test_pair_result_to_dict(self):
        """Should convert to dictionary"""
        result = PairResult(
            upstream_name="A",
            downstream_name="B",
            correlation=0.75,
            lag_hours=3,
            sample_size=50,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["correlation"] == 0.75
        assert result_dict["lag_hours"] == 3
        assert result_dict["sample_size"] == 50


class TestDataFrameExport:
    """Test DataFrame export functionality"""

    def test_to_dataframe_basic(self):
        """Should export aligned data to DataFrame"""
        dates = pd.date_range("2024-01-01", periods=24, freq="h")

        upstream_df = pd.DataFrame({"방류량": range(24)}, index=dates)
        downstream_df = pd.DataFrame({"수위": range(24)}, index=dates)

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        df = pair.to_dataframe(lag_hours=0)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        # Should have columns for both facilities
        assert any("소양강댐" in col or "upstream" in col.lower() for col in df.columns)
        assert any("춘천" in col or "downstream" in col.lower() for col in df.columns)

    def test_to_dataframe_with_lag(self):
        """Should include lag in DataFrame export"""
        dates = pd.date_range("2024-01-01", periods=48, freq="h")

        upstream_df = pd.DataFrame({"value": range(48)}, index=dates)
        downstream_df = pd.DataFrame({"value": range(48)}, index=dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        df = pair.to_dataframe(lag_hours=3)

        assert isinstance(df, pd.DataFrame)
        # Should have fewer rows due to lag alignment
        assert len(df) <= 48

    def test_to_dataframe_index_is_datetime(self):
        """Should preserve datetime index"""
        dates = pd.date_range("2024-01-01", periods=24, freq="h")

        upstream_df = pd.DataFrame({"value": range(24)}, index=dates)
        downstream_df = pd.DataFrame({"value": range(24)}, index=dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        df = pair.to_dataframe(lag_hours=0)

        assert isinstance(df.index, pd.DatetimeIndex)


class TestMissingValueHandling:
    """Test handling of missing values and edge cases"""

    def test_handle_gaps_in_time_series(self):
        """Should handle gaps in time series data"""
        # Create data with gaps
        dates1 = pd.date_range("2024-01-01", periods=10, freq="h")
        dates2 = pd.date_range("2024-01-01 15:00", periods=10, freq="h")
        all_dates = dates1.union(dates2)

        upstream_df = pd.DataFrame({"value": range(len(all_dates))}, index=all_dates)

        downstream_df = pd.DataFrame({"value": range(len(all_dates))}, index=all_dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        aligned = pair.align_with_lag(lag_hours=1)
        assert aligned is not None

    def test_handle_different_time_ranges(self):
        """Should handle different time ranges between upstream and downstream"""
        upstream_dates = pd.date_range("2024-01-01", periods=100, freq="h")
        downstream_dates = pd.date_range("2024-01-02", periods=80, freq="h")

        upstream_df = pd.DataFrame({"value": range(100)}, index=upstream_dates)

        downstream_df = pd.DataFrame({"value": range(80)}, index=downstream_dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        # Should find overlapping period
        aligned = pair.align_with_lag(lag_hours=0)
        assert aligned is not None
        assert len(aligned) > 0

    def test_handle_no_overlap(self):
        """Should handle case with no overlapping time range"""
        upstream_dates = pd.date_range("2024-01-01", periods=24, freq="h")
        downstream_dates = pd.date_range("2024-02-01", periods=24, freq="h")

        upstream_df = pd.DataFrame({"value": range(24)}, index=upstream_dates)

        downstream_df = pd.DataFrame({"value": range(24)}, index=downstream_dates)

        pair = FacilityPair(
            upstream_name="A",
            downstream_name="B",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        # Should return empty or raise error
        with pytest.raises(ValueError, match="No overlapping"):
            pair.align_with_lag(lag_hours=0)


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_dam_outflow_to_water_level(self):
        """Test typical dam outflow → downstream water level scenario"""
        # Simulate 7 days of hourly data
        dates = pd.date_range("2024-01-01", periods=7 * 24, freq="h")

        # Dam releases water (방류량)
        # Pattern: high during day, low at night
        hour_of_day = dates.hour
        dam_outflow = 100 + 50 * np.sin((hour_of_day - 6) * np.pi / 12)

        # Water level at downstream station (수위)
        # Same pattern but delayed by 2 hours and with noise
        water_level_base = 100 + 50 * np.sin((hour_of_day - 8) * np.pi / 12)
        water_level = water_level_base + np.random.normal(0, 5, len(dates))

        upstream_df = pd.DataFrame({"방류량": dam_outflow}, index=dates)
        downstream_df = pd.DataFrame({"수위": water_level}, index=dates)

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_type="dam",
            downstream_type="water_level",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        # Find optimal lag
        result = pair.find_optimal_lag(max_lag_hours=6)

        assert result is not None
        # Should find ~2 hour lag
        assert 1 <= result.lag_hours <= 3
        assert result.correlation > 0.7

    def test_multiple_measurement_items(self):
        """Should handle multiple measurement columns"""
        dates = pd.date_range("2024-01-01", periods=100, freq="h")

        upstream_df = pd.DataFrame(
            {
                "방류량": np.random.rand(100) * 100,
                "저수율": np.random.rand(100) * 100,
                "유입량": np.random.rand(100) * 50,
            },
            index=dates,
        )

        downstream_df = pd.DataFrame(
            {"수위": np.random.rand(100) * 10, "유량": np.random.rand(100) * 200},
            index=dates,
        )

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천",
            upstream_data=upstream_df,
            downstream_data=downstream_df,
        )

        # Should be able to analyze different column combinations
        result1 = pair.calculate_correlation(
            lag_hours=2, upstream_column="방류량", downstream_column="수위"
        )

        result2 = pair.calculate_correlation(
            lag_hours=2, upstream_column="방류량", downstream_column="유량"
        )

        assert result1 is not None
        assert result2 is not None
        assert result1.upstream_column == "방류량"
        assert result2.downstream_column == "유량"
