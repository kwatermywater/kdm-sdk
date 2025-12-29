"""
Template System Tests

Tests for Template Builder, Template execution, and template loaders.
Following TDD methodology: Red -> Green -> Refactor
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestTemplateBuilder:
    """Test TemplateBuilder class"""

    def test_builder_creation(self):
        """Test basic template builder creation"""
        from kdm_sdk.templates import TemplateBuilder

        builder = TemplateBuilder("Test Template")
        assert builder is not None
        assert builder._name == "Test Template"

    def test_builder_fluent_api_single_site(self):
        """Test fluent API for single site"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Dam Monitoring")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율", "유입량"])
            .days(7)
            .build()
        )

        assert template is not None
        assert template.name == "Dam Monitoring"

    def test_builder_with_multiple_sites(self):
        """Test builder with multiple sites"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Multi-Dam")
            .sites(["소양강댐", "충주댐", "팔당댐"], facility_type="dam")
            .measurements(["저수율"])
            .days(30)
            .build()
        )

        config = template.to_dict()
        assert len(config["sites"]) == 3
        assert config["sites"][0]["site_name"] == "소양강댐"

    def test_builder_with_facility_pair(self):
        """Test builder with upstream-downstream pair"""
        from kdm_sdk.templates import TemplateBuilder

        # Use the pair() method with direct parameters
        template = (
            TemplateBuilder("Downstream Analysis")
            .pair(upstream="소양강댐", downstream="의암댐", lag_hours=5.5)
            .days(365)
            .build()
        )

        config = template.to_dict()
        assert "pairs" in config
        assert len(config["pairs"]) == 1
        assert config["pairs"][0]["upstream"] == "소양강댐"

    def test_builder_with_date_range(self):
        """Test builder with specific date range"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Date Range Test")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .date_range("2024-01-01", "2024-12-31")
            .build()
        )

        config = template.to_dict()
        assert config["period"]["start_date"] == "2024-01-01"
        assert config["period"]["end_date"] == "2024-12-31"

    def test_builder_with_time_key(self):
        """Test builder with time_key specification"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Hourly Data")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .time_key("h_1")
            .build()
        )

        config = template.to_dict()
        assert config["time_key"] == "h_1"


class TestTemplate:
    """Test Template execution"""

    @pytest.mark.asyncio
    async def test_template_execution_basic(self, kdm_client):
        """Test basic template execution"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Test Execution")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .build()
        )

        result = await template.execute(client=kdm_client)
        assert result is not None

    @pytest.mark.asyncio
    async def test_template_execution_with_params(self, kdm_client):
        """Test template execution with parameter override"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Parameterized")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .build()
        )

        # Override days parameter
        result = await template.execute(client=kdm_client, days=14)
        assert result is not None

    @pytest.mark.asyncio
    async def test_template_with_pair_execution(self, kdm_client):
        """Test template execution with facility pair"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Pair Test")
            .pair(upstream="소양강댐", downstream="의암댐", lag_hours=5.5)
            .days(30)
            .build()
        )

        result = await template.execute(client=kdm_client)
        assert result is not None

    def test_template_to_dict(self):
        """Test template serialization to dict"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Serialization Test")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .build()
        )

        config = template.to_dict()
        assert config["name"] == "Serialization Test"
        assert "sites" in config
        assert "measurements" in config
        assert "period" in config


class TestYAMLLoader:
    """Test YAML template save/load"""

    def test_save_yaml(self):
        """Test saving template as YAML"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("YAML Test")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율", "유입량"])
            .days(7)
            .build()
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_template.yaml")
            template.save_yaml(filepath)

            assert os.path.exists(filepath)
            # Verify it's valid YAML
            import yaml

            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert data["name"] == "YAML Test"

    def test_load_yaml(self):
        """Test loading template from YAML"""
        from kdm_sdk.templates import TemplateBuilder, load_yaml

        # Create and save
        template = (
            TemplateBuilder("Load Test")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(30)
            .build()
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "load_test.yaml")
            template.save_yaml(filepath)

            # Load
            loaded = load_yaml(filepath)
            assert loaded is not None
            assert loaded.name == "Load Test"

            config = loaded.to_dict()
            assert config["sites"][0]["site_name"] == "소양강댐"
            assert "저수율" in config["measurements"]

    def test_yaml_with_pair(self):
        """Test YAML save/load with facility pair"""
        from kdm_sdk.templates import TemplateBuilder, load_yaml

        template = (
            TemplateBuilder("Pair YAML")
            .pair(
                upstream="소양강댐",
                downstream="의암댐",
                lag_hours=5.5,
                upstream_items=["방류량"],
                downstream_items=["수위"],
            )
            .days(365)
            .build()
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "pair_template.yaml")
            template.save_yaml(filepath)

            loaded = load_yaml(filepath)
            config = loaded.to_dict()

            assert len(config["pairs"]) == 1
            assert config["pairs"][0]["upstream"] == "소양강댐"
            assert config["pairs"][0]["downstream"] == "의암댐"
            assert config["pairs"][0]["lag_hours"] == 5.5


class TestPythonLoader:
    """Test Python template loader"""

    def test_load_python_with_template_variable(self):
        """Test loading Python file with 'template' variable"""
        from kdm_sdk.templates import load_python

        # Create temporary Python template file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_template.py")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    """
from kdm_sdk.templates import TemplateBuilder

template = TemplateBuilder("Python Template") \\
    .site("소양강댐", facility_type="dam") \\
    .measurements(["저수율"]) \\
    .days(7) \\
    .build()
"""
                )

            loaded = load_python(filepath)
            assert loaded is not None
            assert loaded.name == "Python Template"

    def test_load_python_with_function(self):
        """Test loading Python file with 'create_template' function"""
        from kdm_sdk.templates import load_python

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "func_template.py")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(
                    """
from kdm_sdk.templates import TemplateBuilder

def create_template():
    return TemplateBuilder("Function Template") \\
        .site("충주댐", facility_type="dam") \\
        .measurements(["저수율", "유입량"]) \\
        .days(30) \\
        .build()
"""
                )

            loaded = load_python(filepath)
            assert loaded is not None
            assert loaded.name == "Function Template"

            config = loaded.to_dict()
            assert config["sites"][0]["site_name"] == "충주댐"

    def test_load_python_invalid_file(self):
        """Test loading Python file without template"""
        from kdm_sdk.templates import load_python

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "invalid.py")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("# No template here\nprint('hello')\n")

            with pytest.raises(ValueError, match="No 'template' or 'create_template'"):
                load_python(filepath)


class TestTemplateValidation:
    """Test template validation"""

    def test_validation_missing_site(self):
        """Test validation fails when no site specified"""
        from kdm_sdk.templates import TemplateBuilder

        # Should raise error when building without site
        with pytest.raises(ValueError, match="at least one site"):
            TemplateBuilder("Invalid").measurements(["저수율"]).days(7).build()

    def test_validation_missing_measurements(self):
        """Test validation fails when no measurements specified"""
        from kdm_sdk.templates import TemplateBuilder

        with pytest.raises(ValueError, match="at least one measurement"):
            TemplateBuilder("Invalid").site("소양강댐", facility_type="dam").days(
                7
            ).build()

    def test_validation_missing_period(self):
        """Test validation fails when no period specified"""
        from kdm_sdk.templates import TemplateBuilder

        with pytest.raises(ValueError, match="period"):
            TemplateBuilder("Invalid").site(
                "소양강댐", facility_type="dam"
            ).measurements(["저수율"]).build()

    def test_validation_invalid_days(self):
        """Test validation fails for invalid days value"""
        from kdm_sdk.templates import TemplateBuilder

        with pytest.raises(ValueError, match="days must be positive"):
            TemplateBuilder("Invalid").site(
                "소양강댐", facility_type="dam"
            ).measurements(["저수율"]).days(-5).build()

    def test_validation_conflicting_period(self):
        """Test validation fails when both days and date_range specified"""
        from kdm_sdk.templates import TemplateBuilder

        with pytest.raises(ValueError, match="Cannot specify both"):
            TemplateBuilder("Invalid").site(
                "소양강댐", facility_type="dam"
            ).measurements(["저수율"]).days(7).date_range(
                "2024-01-01", "2024-12-31"
            ).build()


class TestTemplateDescription:
    """Test template description and metadata"""

    def test_template_with_description(self):
        """Test adding description to template"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Documented Template")
            .description("Monitor dam storage levels over time")
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .build()
        )

        config = template.to_dict()
        assert config["description"] == "Monitor dam storage levels over time"

    def test_template_with_tags(self):
        """Test adding tags to template"""
        from kdm_sdk.templates import TemplateBuilder

        template = (
            TemplateBuilder("Tagged Template")
            .description("Test template")
            .tags(["monitoring", "dam", "hourly"])
            .site("소양강댐", facility_type="dam")
            .measurements(["저수율"])
            .days(7)
            .build()
        )

        config = template.to_dict()
        assert "monitoring" in config["tags"]
        assert "dam" in config["tags"]
