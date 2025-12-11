"""Unit tests for kill-switch configuration loader.

Tests cover:
- CSV parsing with valid data
- Pydantic validation (HARD severity=0, SOFT severity>0, operators)
- Duplicate name rejection
- Comment line skipping
- Missing field handling
- File not found handling
"""

import tempfile
from pathlib import Path

import pytest

from phx_home_analysis.services.kill_switch.config_loader import (
    KillSwitchConfig,
    get_hard_configs,
    get_soft_configs,
    load_kill_switch_config,
)


class TestKillSwitchConfig:
    """Tests for KillSwitchConfig Pydantic model."""

    def test_hard_criterion_valid(self):
        """HARD criterion with severity 0.0 should be valid."""
        config = KillSwitchConfig(
            name="no_hoa",
            type="HARD",
            operator="==",
            threshold="0",
            severity=0.0,
            description="No HOA allowed",
        )
        assert config.name == "no_hoa"
        assert config.type == "HARD"
        assert config.severity == 0.0

    def test_soft_criterion_valid(self):
        """SOFT criterion with severity > 0.0 should be valid."""
        config = KillSwitchConfig(
            name="city_sewer",
            type="SOFT",
            operator="==",
            threshold="CITY",
            severity=2.5,
            description="City sewer required",
        )
        assert config.name == "city_sewer"
        assert config.type == "SOFT"
        assert config.severity == 2.5

    def test_hard_criterion_nonzero_severity_fails(self):
        """HARD criterion with non-zero severity should fail validation."""
        with pytest.raises(ValueError, match="HARD criterion.*must have severity 0.0"):
            KillSwitchConfig(
                name="bad_hard",
                type="HARD",
                operator=">=",
                threshold="4",
                severity=1.5,
                description="Bad HARD criterion",
            )

    def test_soft_criterion_zero_severity_fails(self):
        """SOFT criterion with severity 0.0 should fail validation."""
        with pytest.raises(ValueError, match="SOFT criterion.*must have severity >= 0.1"):
            KillSwitchConfig(
                name="bad_soft",
                type="SOFT",
                operator="==",
                threshold="value",
                severity=0.0,
                description="Bad SOFT criterion",
            )

    def test_invalid_operator_fails(self):
        """Invalid operator should fail validation."""
        with pytest.raises(ValueError):
            KillSwitchConfig(
                name="test",
                type="HARD",
                operator="INVALID",  # type: ignore[arg-type]
                threshold="0",
                severity=0.0,
                description="Test",
            )

    def test_invalid_type_fails(self):
        """Invalid type should fail validation."""
        with pytest.raises(ValueError):
            KillSwitchConfig(
                name="test",
                type="INVALID",  # type: ignore[arg-type]
                operator="==",
                threshold="0",
                severity=0.0,
                description="Test",
            )

    def test_severity_precision_rounding(self):
        """Severity should be rounded to 2 decimal places."""
        config = KillSwitchConfig(
            name="test",
            type="SOFT",
            operator="==",
            threshold="value",
            severity=2.567,
            description="Test",
        )
        assert config.severity == 2.57

    def test_all_valid_operators(self):
        """All valid operators should be accepted."""
        valid_operators = ["==", "!=", ">", "<", ">=", "<=", "range", "in", "not_in"]
        for op in valid_operators:
            config = KillSwitchConfig(
                name=f"test_{op}",
                type="HARD",
                operator=op,  # type: ignore[arg-type]
                threshold="0",
                severity=0.0,
                description=f"Test {op}",
            )
            assert config.operator == op

    def test_to_dict(self):
        """to_dict should return all fields."""
        config = KillSwitchConfig(
            name="test",
            type="SOFT",
            operator=">=",
            threshold="10",
            severity=1.5,
            description="Test description",
        )
        d = config.to_dict()
        assert d["name"] == "test"
        assert d["type"] == "SOFT"
        assert d["operator"] == ">="
        assert d["threshold"] == "10"
        assert d["severity"] == 1.5
        assert d["description"] == "Test description"

    def test_str_hard(self):
        """String representation for HARD criterion."""
        config = KillSwitchConfig(
            name="no_hoa",
            type="HARD",
            operator="==",
            threshold="0",
            severity=0.0,
            description="No HOA",
        )
        assert "[HARD]" in str(config)
        assert "no_hoa" in str(config)

    def test_str_soft(self):
        """String representation for SOFT criterion."""
        config = KillSwitchConfig(
            name="city_sewer",
            type="SOFT",
            operator="==",
            threshold="CITY",
            severity=2.5,
            description="City sewer",
        )
        assert "[SOFT severity=2.5]" in str(config)
        assert "city_sewer" in str(config)


class TestLoadKillSwitchConfig:
    """Tests for load_kill_switch_config function."""

    def test_load_valid_csv(self):
        """Load a valid CSV with HARD and SOFT criteria."""
        csv_content = """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,No HOA allowed
city_sewer,SOFT,==,CITY,2.5,City sewer required
min_bedrooms,HARD,>=,4,0.0,Minimum 4 bedrooms
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            configs = load_kill_switch_config(path)
            assert len(configs) == 3
            assert configs[0].name == "no_hoa"
            assert configs[0].type == "HARD"
            assert configs[1].name == "city_sewer"
            assert configs[1].type == "SOFT"
            assert configs[1].severity == 2.5
        finally:
            path.unlink()

    def test_skip_comment_lines(self):
        """Comment lines starting with # should be skipped."""
        csv_content = """\
name,type,operator,threshold,severity,description
# This is a comment
no_hoa,HARD,==,0,0.0,No HOA allowed
# Another comment
city_sewer,SOFT,==,CITY,2.5,City sewer required
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            configs = load_kill_switch_config(path)
            assert len(configs) == 2
            assert configs[0].name == "no_hoa"
            assert configs[1].name == "city_sewer"
        finally:
            path.unlink()

    def test_file_not_found(self):
        """FileNotFoundError raised for missing file."""
        with pytest.raises(FileNotFoundError, match="Kill-switch config file not found"):
            load_kill_switch_config(Path("/nonexistent/path.csv"))

    def test_missing_header(self):
        """ValueError raised if CSV has no header."""
        # Create empty file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="no header row"):
                load_kill_switch_config(path)
        finally:
            path.unlink()

    def test_missing_required_field(self):
        """ValueError raised if CSV is missing required fields."""
        csv_content = """\
name,type,operator,threshold
no_hoa,HARD,==,0
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="missing required fields"):
                load_kill_switch_config(path)
        finally:
            path.unlink()

    def test_duplicate_name_rejected(self):
        """ValueError raised if duplicate criterion names found."""
        csv_content = """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,No HOA allowed
no_hoa,HARD,>=,4,0.0,Duplicate name
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Duplicate criterion name"):
                load_kill_switch_config(path)
        finally:
            path.unlink()

    def test_invalid_type_skipped(self):
        """Rows with invalid type (not HARD/SOFT) should be skipped with warning."""
        csv_content = """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,No HOA allowed
bad_type,INVALID,==,0,0.0,Should be skipped
city_sewer,SOFT,==,CITY,2.5,City sewer required
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            configs = load_kill_switch_config(path)
            assert len(configs) == 2
            names = [c.name for c in configs]
            assert "bad_type" not in names
        finally:
            path.unlink()

    def test_hard_with_nonzero_severity_fails(self):
        """HARD criterion with non-zero severity should fail."""
        csv_content = """\
name,type,operator,threshold,severity,description
bad_hard,HARD,==,0,1.5,Bad HARD with severity
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="HARD criterion.*must have severity 0.0"):
                load_kill_switch_config(path)
        finally:
            path.unlink()

    def test_soft_with_zero_severity_fails(self):
        """SOFT criterion with zero severity should fail."""
        csv_content = """\
name,type,operator,threshold,severity,description
bad_soft,SOFT,==,CITY,0.0,Bad SOFT with zero severity
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="SOFT criterion.*must have severity >= 0.1"):
                load_kill_switch_config(path)
        finally:
            path.unlink()

    def test_invalid_operator_fails(self):
        """Invalid operator should fail validation."""
        csv_content = """\
name,type,operator,threshold,severity,description
bad_op,HARD,BADOP,0,0.0,Bad operator
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError):
                load_kill_switch_config(path)
        finally:
            path.unlink()

    def test_load_real_config_file(self):
        """Load the actual config/kill_switch.csv file from project."""
        config_path = (
            Path(__file__).parent.parent.parent.parent.parent / "config" / "kill_switch.csv"
        )
        if not config_path.exists():
            pytest.skip("config/kill_switch.csv not found")

        configs = load_kill_switch_config(config_path)

        # Should have 5 HARD + 4 SOFT = 9 total
        assert len(configs) == 9

        hard_configs = [c for c in configs if c.type == "HARD"]
        soft_configs = [c for c in configs if c.type == "SOFT"]

        assert len(hard_configs) == 5
        assert len(soft_configs) == 4

        # Check expected criteria names
        hard_names = {c.name for c in hard_configs}
        assert "no_hoa" in hard_names
        assert "min_bedrooms" in hard_names
        assert "min_bathrooms" in hard_names
        assert "min_sqft" in hard_names
        assert "no_solar_lease" in hard_names

        soft_names = {c.name for c in soft_configs}
        assert "city_sewer" in soft_names
        assert "no_new_build" in soft_names
        assert "min_garage" in soft_names
        assert "lot_size" in soft_names


class TestFilterFunctions:
    """Tests for get_hard_configs and get_soft_configs helper functions."""

    def test_get_hard_configs(self):
        """get_hard_configs should return only HARD criteria."""
        configs = [
            KillSwitchConfig(
                name="hard1",
                type="HARD",
                operator="==",
                threshold="0",
                severity=0.0,
                description="Hard 1",
            ),
            KillSwitchConfig(
                name="soft1",
                type="SOFT",
                operator=">=",
                threshold="10",
                severity=1.5,
                description="Soft 1",
            ),
            KillSwitchConfig(
                name="hard2",
                type="HARD",
                operator=">=",
                threshold="4",
                severity=0.0,
                description="Hard 2",
            ),
        ]

        hard = get_hard_configs(configs)
        assert len(hard) == 2
        assert all(c.type == "HARD" for c in hard)

    def test_get_soft_configs(self):
        """get_soft_configs should return only SOFT criteria."""
        configs = [
            KillSwitchConfig(
                name="hard1",
                type="HARD",
                operator="==",
                threshold="0",
                severity=0.0,
                description="Hard 1",
            ),
            KillSwitchConfig(
                name="soft1",
                type="SOFT",
                operator=">=",
                threshold="10",
                severity=1.5,
                description="Soft 1",
            ),
            KillSwitchConfig(
                name="soft2",
                type="SOFT",
                operator="==",
                threshold="CITY",
                severity=2.5,
                description="Soft 2",
            ),
        ]

        soft = get_soft_configs(configs)
        assert len(soft) == 2
        assert all(c.type == "SOFT" for c in soft)
