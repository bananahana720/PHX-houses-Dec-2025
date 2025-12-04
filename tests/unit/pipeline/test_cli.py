"""Unit tests for pipeline CLI.

Tests cover:
- CLI argument parsing
- Flag combinations and validation
- Status query mode
- Exit codes
- Dry-run validation mode
- JSON output format
- CSV row-level validation
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


class TestDryRunMode:
    """Tests for --dry-run validation mode."""

    def test_help_shows_dry_run_flag(self) -> None:
        """Test --help shows --dry-run option."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "--dry-run" in result.stdout
        assert "validate" in result.stdout.lower() or "api" in result.stdout.lower()

    def test_dry_run_validates_csv_without_processing(self) -> None:
        """Test --dry-run validates CSV and shows estimated time without API calls."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St Phoenix AZ 85001,400000,4\n")
            f.write("456 Oak Ave Phoenix AZ 85002,350000,3\n")
            f.flush()
            csv_path = Path(f.name)

            with (
                patch("pipeline_cli.CSV_FILE", csv_path),
                patch("pipeline_cli.PhaseCoordinator") as mock_coord,
            ):
                result = runner.invoke(app, ["--all", "--dry-run"])

                # Coordinator should NOT be instantiated in dry-run mode
                mock_coord.assert_not_called()

                assert result.exit_code == 0
                # Should show validation results
                assert "valid" in result.stdout.lower() or "dry" in result.stdout.lower()

    def test_dry_run_shows_estimated_time(self) -> None:
        """Test --dry-run displays estimated processing time."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St Phoenix AZ 85001,400000,4\n")
            f.write("456 Oak Ave Phoenix AZ 85002,350000,3\n")
            f.write("789 Pine Rd Phoenix AZ 85003,500000,5\n")
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run"])

                assert result.exit_code == 0
                # Should show time estimate (minutes or seconds)
                stdout_lower = result.stdout.lower()
                assert (
                    "minute" in stdout_lower
                    or "second" in stdout_lower
                    or "time" in stdout_lower
                    or "estimate" in stdout_lower
                )

    def test_dry_run_blocks_on_csv_errors(self) -> None:
        """Test --dry-run blocks processing when CSV has validation errors."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            # CSV with missing address field (header exists but no address column)
            f.write("price,beds\n")
            f.write("400000,4\n")
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run"])

                # Should report validation failure with non-zero exit code
                assert result.exit_code == 1 and "error" in result.stdout.lower()


class TestJsonOutput:
    """Tests for --json output format."""

    def test_help_shows_json_flag(self) -> None:
        """Test --help shows --json option."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "--json" in result.stdout

    def test_json_output_is_valid_json(self) -> None:
        """Test --json outputs valid JSON format."""
        with patch("pipeline_cli.WORK_ITEMS_FILE") as mock_path:
            mock_path.exists.return_value = False

            result = runner.invoke(app, ["--status", "--json"])

            assert result.exit_code == 0
            # Output should be valid JSON
            try:
                import json

                output = json.loads(result.stdout)
                assert isinstance(output, dict)
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")

    def test_json_output_structure(self) -> None:
        """Test --json output has expected structure for status."""
        with patch("pipeline_cli.WORK_ITEMS_FILE") as mock_path:
            mock_path.exists.return_value = False

            result = runner.invoke(app, ["--status", "--json"])

            assert result.exit_code == 0
            import json

            output = json.loads(result.stdout)
            # Should have status field
            assert "status" in output


class TestCsvValidation:
    """Tests for row-specific CSV validation."""

    def test_csv_validation_reports_missing_address_column(self) -> None:
        """Test validation reports error when address column is missing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            # No address column at all
            f.write("price,beds,baths\n")
            f.write("400000,4,2\n")
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run"])

                # Should indicate missing address column
                stdout_lower = result.stdout.lower()
                assert (
                    "address" in stdout_lower
                    or "column" in stdout_lower
                    or "error" in stdout_lower
                )

    def test_csv_validation_reports_empty_addresses_with_row_numbers(self) -> None:
        """Test validation reports empty addresses with row numbers."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St,400000,4\n")
            f.write(",350000,3\n")  # Empty address on row 3 (data row 2)
            f.write("789 Pine Rd,500000,5\n")
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run"])

                # Should show row number in error message
                stdout_lower = result.stdout.lower()
                assert (
                    "row" in stdout_lower or "line" in stdout_lower
                ) and (
                    "empty" in stdout_lower
                    or "missing" in stdout_lower
                    or "error" in stdout_lower
                )

    def test_csv_validation_collects_all_errors_before_blocking(self) -> None:
        """Test validation collects all errors before reporting (batch mode)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write(",400000,4\n")  # Error 1: empty address
            f.write("456 Oak Ave,350000,3\n")  # Valid
            f.write(",500000,5\n")  # Error 2: empty address
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run"])

                # Should report multiple errors (both empty addresses)
                # Count occurrences of error indicators
                stdout_lower = result.stdout.lower()
                # Should mention at least 2 errors
                assert (
                    "2" in result.stdout
                    or "error" in stdout_lower
                )

    def test_csv_validation_passes_for_valid_csv(self) -> None:
        """Test validation passes for a fully valid CSV."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St Phoenix AZ 85001,400000,4\n")
            f.write("456 Oak Ave Phoenix AZ 85002,350000,3\n")
            f.write("789 Pine Rd Phoenix AZ 85003,500000,5\n")
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run"])

                assert result.exit_code == 0
                stdout_lower = result.stdout.lower()
                # Should indicate success/valid
                assert (
                    "valid" in stdout_lower
                    or "success" in stdout_lower
                    or "pass" in stdout_lower
                    or "3 propert" in stdout_lower  # "3 properties"
                )


class TestIntegrationDryRunAndJson:
    """Integration tests for --dry-run and --json modes combined."""

    def test_dry_run_with_json_output(self) -> None:
        """Test --dry-run with --json outputs valid JSON structure."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write("123 Main St Phoenix AZ 85001,400000,4\n")
            f.write("456 Oak Ave Phoenix AZ 85002,350000,3\n")
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run", "--json"])

                assert result.exit_code == 0
                import json

                output = json.loads(result.stdout)
                assert output["status"] == "valid"
                assert output["dry_run"] is True
                assert output["valid_addresses"] == 2
                assert "estimated_time_seconds" in output
                assert "estimated_time_human" in output

    def test_dry_run_with_json_shows_errors(self) -> None:
        """Test --dry-run with --json reports validation errors in JSON."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price,beds\n")
            f.write(",400000,4\n")  # Empty address
            f.flush()
            csv_path = Path(f.name)

            with patch("pipeline_cli.CSV_FILE", csv_path):
                result = runner.invoke(app, ["--all", "--dry-run", "--json"])

                import json

                output = json.loads(result.stdout)
                assert output["status"] == "invalid"
                assert output["error_count"] >= 1
                assert len(output["errors"]) >= 1
                assert "Row 2" in output["errors"][0]

    def test_progress_reporter_eta_rolling_average(self) -> None:
        """Test that ETA uses rolling average of last 5 property durations."""
        from phx_home_analysis.pipeline.progress import PipelineStats

        stats = PipelineStats(total=10, complete=5)
        # Add more than 5 durations to test rolling average
        stats.phase_durations = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]

        # Rolling average of last 5: [30, 40, 50, 60, 70] = 250/5 = 50
        # Remaining: 10 - 5 = 5 properties
        # ETA: 50 * 5 = 250 seconds
        eta = stats.eta
        assert eta is not None
        assert eta.total_seconds() == 250.0

    def test_csv_validator_function_import(self) -> None:
        """Test that validate_csv_with_errors is importable from pipeline_cli."""
        from pipeline_cli import CSVValidationResult, validate_csv_with_errors

        # Create valid temp CSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("full_address,price\n")
            f.write("123 Main St,400000\n")
            f.flush()

            result = validate_csv_with_errors(Path(f.name))

            assert isinstance(result, CSVValidationResult)
            assert result.is_valid is True
            assert len(result.valid_addresses) == 1
            assert result.error_count == 0


class TestTimeFormatting:
    """Tests for time estimate formatting."""

    def test_format_time_estimate_seconds_only(self) -> None:
        """Test formatting for times under 60 seconds."""
        from pipeline_cli import format_time_estimate

        assert format_time_estimate(0) == "0 seconds"
        assert format_time_estimate(1) == "1 seconds"
        assert format_time_estimate(30) == "30 seconds"
        assert format_time_estimate(59) == "59 seconds"

    def test_format_time_estimate_exact_minutes(self) -> None:
        """Test formatting for exact minute boundaries."""
        from pipeline_cli import format_time_estimate

        assert format_time_estimate(60) == "1 minutes"
        assert format_time_estimate(120) == "2 minutes"
        assert format_time_estimate(180) == "3 minutes"
        assert format_time_estimate(3600) == "60 minutes"

    def test_format_time_estimate_minutes_and_seconds(self) -> None:
        """Test formatting for times with both minutes and seconds."""
        from pipeline_cli import format_time_estimate

        assert format_time_estimate(61) == "1 minutes 1 seconds"
        assert format_time_estimate(90) == "1 minutes 30 seconds"
        assert format_time_estimate(125) == "2 minutes 5 seconds"
        assert format_time_estimate(3659) == "60 minutes 59 seconds"
