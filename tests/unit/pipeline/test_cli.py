"""Unit tests for pipeline CLI.

Tests cover:
- CLI argument parsing
- Flag combinations and validation
- Status query mode
- Exit codes
"""
from __future__ import annotations

# Import the CLI app
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pipeline_cli import (
    app,
    load_addresses_from_csv,
    validate_exclusive_modes,
    validate_skip_phase,
)

runner = CliRunner()


class TestCLIArgumentValidation:
    """Tests for CLI argument validation functions."""

    def test_validate_exclusive_modes_address_only(self) -> None:
        """Test validation passes with address only."""
        # Should not raise
        validate_exclusive_modes(
            address="123 Main St",
            all_properties=False,
            test=False,
            status=False,
        )

    def test_validate_exclusive_modes_all_only(self) -> None:
        """Test validation passes with --all only."""
        validate_exclusive_modes(
            address=None,
            all_properties=True,
            test=False,
            status=False,
        )

    def test_validate_exclusive_modes_test_only(self) -> None:
        """Test validation passes with --test only."""
        validate_exclusive_modes(
            address=None,
            all_properties=False,
            test=True,
            status=False,
        )

    def test_validate_exclusive_modes_status_only(self) -> None:
        """Test validation passes with --status only."""
        validate_exclusive_modes(
            address=None,
            all_properties=False,
            test=False,
            status=True,
        )

    def test_multiple_modes_rejected(self) -> None:
        """Test validation fails with multiple modes."""
        import typer

        with pytest.raises(typer.BadParameter):
            validate_exclusive_modes(
                address="123 Main St",
                all_properties=True,
                test=False,
                status=False,
            )

    def test_no_mode_rejected(self) -> None:
        """Test validation fails with no mode specified."""
        import typer

        with pytest.raises(typer.BadParameter):
            validate_exclusive_modes(
                address=None,
                all_properties=False,
                test=False,
                status=False,
            )

    def test_skip_phase_validates_range_valid(self) -> None:
        """Test skip_phase accepts valid range 0-4."""
        assert validate_skip_phase(0) == 0
        assert validate_skip_phase(1) == 1
        assert validate_skip_phase(2) == 2
        assert validate_skip_phase(3) == 3
        assert validate_skip_phase(4) == 4

    def test_skip_phase_validates_range_invalid(self) -> None:
        """Test skip_phase rejects invalid values."""
        import typer

        with pytest.raises(typer.BadParameter):
            validate_skip_phase(5)

        with pytest.raises(typer.BadParameter):
            validate_skip_phase(-1)

    def test_skip_phase_none_returns_none(self) -> None:
        """Test skip_phase returns None when input is None."""
        assert validate_skip_phase(None) is None


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_help_shows_all_options(self) -> None:
        """Test --help shows all available options."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "--all" in result.stdout
        assert "--test" in result.stdout
        assert "--status" in result.stdout
        assert "--resume" in result.stdout
        assert "--fresh" in result.stdout
        assert "--strict" in result.stdout
        assert "--skip-phase" in result.stdout

    def test_all_flag_description(self) -> None:
        """Test --all flag has correct description."""
        result = runner.invoke(app, ["--help"])

        # Rich wraps long lines, so check for key parts
        assert "--all" in result.stdout
        assert "properties" in result.stdout.lower()
        assert "csv" in result.stdout.lower()

    def test_test_flag_description(self) -> None:
        """Test --test flag has correct description."""
        result = runner.invoke(app, ["--help"])

        # Check for key parts of the description
        assert "--test" in result.stdout
        assert "5" in result.stdout
        assert "validation" in result.stdout.lower()


class TestLoadAddressesFromCSV:
    """Tests for CSV loading function."""

    def test_load_addresses_from_csv_success(self) -> None:
        """Test loading addresses from valid CSV."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St,400000,4\n")
            f.write("456 Oak Ave,350000,3\n")
            f.write("789 Pine Rd,500000,5\n")
            f.flush()

            addresses = load_addresses_from_csv(Path(f.name))

            assert len(addresses) == 3
            assert "123 Main St" in addresses
            assert "456 Oak Ave" in addresses
            assert "789 Pine Rd" in addresses

    def test_load_addresses_from_csv_with_limit(self) -> None:
        """Test loading addresses with limit."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St,400000,4\n")
            f.write("456 Oak Ave,350000,3\n")
            f.write("789 Pine Rd,500000,5\n")
            f.flush()

            addresses = load_addresses_from_csv(Path(f.name), limit=2)

            assert len(addresses) == 2

    def test_load_addresses_from_csv_not_found(self) -> None:
        """Test loading from non-existent CSV raises exit."""
        from click.exceptions import Exit

        with pytest.raises(Exit):
            # Typer.Exit raises click.Exit
            load_addresses_from_csv(Path("/nonexistent/path.csv"))

    def test_load_addresses_alternative_column_names(self) -> None:
        """Test loading with alternative column names."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("Address,price,beds\n")  # Capital A
            f.write("123 Main St,400000,4\n")
            f.flush()

            addresses = load_addresses_from_csv(Path(f.name))

            assert len(addresses) == 1
            assert "123 Main St" in addresses


class TestCLIExecution:
    """Tests for CLI execution modes."""

    def test_status_flag_query_only(self) -> None:
        """Test --status shows status without processing."""
        with patch("pipeline_cli.WORK_ITEMS_FILE") as mock_path:
            mock_path.exists.return_value = False

            result = runner.invoke(app, ["--status"])

            # Should complete without error
            assert result.exit_code == 0
            assert "No pipeline state found" in result.stdout

    def test_exit_codes_success(self) -> None:
        """Test exit code 0 on success."""
        with patch("pipeline_cli.WORK_ITEMS_FILE") as mock_path:
            mock_path.exists.return_value = False

            result = runner.invoke(app, ["--status"])

            assert result.exit_code == 0

    def test_strict_flag_parsed(self) -> None:
        """Test --strict flag is correctly parsed."""
        # This test verifies the flag parsing via help
        result = runner.invoke(app, ["--help"])

        assert "--strict" in result.stdout
        assert "Fail fast" in result.stdout
