"""Integration tests for KillSwitchFilter with CSV configuration.

Tests cover:
- Loading filter from CSV config path
- reload_config() method
- Default behavior when no config_path
- ConfigWatcher integration
- Change detection
"""

import time
from pathlib import Path

import pytest

from phx_home_analysis.services.kill_switch import (
    ConfigWatcher,
    KillSwitchFilter,
    KillSwitchVerdict,
)


class TestKillSwitchFilterConfigPath:
    """Tests for KillSwitchFilter initialization with config_path."""

    @pytest.fixture
    def valid_config_csv(self) -> str:
        """Valid CSV configuration content."""
        return """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
min_bedrooms,HARD,>=,4,0.0,Minimum 4 bedrooms
city_sewer,SOFT,==,CITY,2.5,City sewer required
"""

    @pytest.fixture
    def config_file(self, valid_config_csv: str, tmp_path: Path) -> Path:
        """Create a temporary config file."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(valid_config_csv, encoding="utf-8")
        return config_path

    def test_init_with_config_path(self, config_file: Path):
        """KillSwitchFilter should load criteria from config_path."""
        filter_svc = KillSwitchFilter(config_path=config_file)

        names = filter_svc.get_kill_switch_names()
        assert "no_hoa" in names
        assert "min_bedrooms" in names
        assert "city_sewer" in names
        assert len(names) == 3

    def test_init_with_config_path_string(self, config_file: Path):
        """KillSwitchFilter should accept config_path as string."""
        filter_svc = KillSwitchFilter(config_path=str(config_file))

        names = filter_svc.get_kill_switch_names()
        assert len(names) == 3

    def test_init_default_no_config_path(self):
        """KillSwitchFilter should use defaults when no config_path."""
        filter_svc = KillSwitchFilter()

        # Should have all 9 default criteria (5 HARD + 4 SOFT)
        names = filter_svc.get_kill_switch_names()
        assert len(names) == 9
        assert "no_hoa" in names
        assert "min_bedrooms" in names
        assert "city_sewer" in names

    def test_init_kill_switches_takes_precedence(self, config_file: Path):
        """Explicit kill_switches should take precedence over config_path."""
        from phx_home_analysis.services.kill_switch import NoHoaKillSwitch

        custom_switches = [NoHoaKillSwitch()]
        filter_svc = KillSwitchFilter(
            kill_switches=custom_switches,
            config_path=config_file,
        )

        names = filter_svc.get_kill_switch_names()
        assert names == ["no_hoa"]

    def test_init_config_file_not_found(self, tmp_path: Path):
        """FileNotFoundError when config file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.csv"

        with pytest.raises(FileNotFoundError):
            KillSwitchFilter(config_path=nonexistent)


class TestKillSwitchFilterReloadConfig:
    """Tests for reload_config() method."""

    @pytest.fixture
    def initial_config(self) -> str:
        """Initial configuration with 2 criteria."""
        return """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
city_sewer,SOFT,==,CITY,2.5,City sewer required
"""

    @pytest.fixture
    def updated_config(self) -> str:
        """Updated configuration with 3 criteria."""
        return """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
city_sewer,SOFT,==,CITY,2.5,City sewer required
min_bedrooms,HARD,>=,4,0.0,Minimum 4 bedrooms
"""

    def test_reload_config_detects_added_criterion(
        self, initial_config: str, updated_config: str, tmp_path: Path
    ):
        """reload_config should detect added criteria."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(initial_config, encoding="utf-8")

        filter_svc = KillSwitchFilter(config_path=config_path)
        assert len(filter_svc.get_kill_switch_names()) == 2

        # Update config file
        config_path.write_text(updated_config, encoding="utf-8")

        # Reload
        changed = filter_svc.reload_config()

        assert "min_bedrooms" in changed
        assert len(filter_svc.get_kill_switch_names()) == 3

    def test_reload_config_detects_removed_criterion(self, initial_config: str, tmp_path: Path):
        """reload_config should detect removed criteria."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(initial_config, encoding="utf-8")

        filter_svc = KillSwitchFilter(config_path=config_path)
        assert len(filter_svc.get_kill_switch_names()) == 2

        # Remove city_sewer
        reduced_config = """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
"""
        config_path.write_text(reduced_config, encoding="utf-8")

        changed = filter_svc.reload_config()

        assert "city_sewer" in changed
        assert len(filter_svc.get_kill_switch_names()) == 1

    def test_reload_config_no_changes(self, initial_config: str, tmp_path: Path):
        """reload_config should return empty list when no changes."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(initial_config, encoding="utf-8")

        filter_svc = KillSwitchFilter(config_path=config_path)

        # Reload same config
        changed = filter_svc.reload_config()

        assert changed == []

    def test_reload_config_without_config_path_raises(self):
        """reload_config should raise ValueError when no config_path."""
        filter_svc = KillSwitchFilter()

        with pytest.raises(ValueError, match="no config_path"):
            filter_svc.reload_config()


class TestKillSwitchFilterWithRealConfig:
    """Tests using the actual config/kill_switch.csv file."""

    def test_load_real_config_file(self):
        """Load the actual config/kill_switch.csv from project."""
        config_path = (
            Path(__file__).parent.parent.parent.parent.parent / "config" / "kill_switch.csv"
        )

        if not config_path.exists():
            pytest.skip("config/kill_switch.csv not found")

        filter_svc = KillSwitchFilter(config_path=config_path)

        # Should have 9 criteria (5 HARD + 4 SOFT)
        assert len(filter_svc.get_kill_switch_names()) == 9
        assert len(filter_svc.get_hard_criteria()) == 5
        assert len(filter_svc.get_soft_criteria()) == 4


class TestConfigWatcher:
    """Tests for ConfigWatcher class."""

    @pytest.fixture
    def config_content(self) -> str:
        """Sample config content."""
        return """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
"""

    def test_check_for_changes_first_call(self, config_content: str, tmp_path: Path):
        """First check should return True."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(config_content, encoding="utf-8")

        watcher = ConfigWatcher(config_path=config_path)

        # First explicit check after init
        assert watcher.check_for_changes() is False  # Already read during init

    def test_check_for_changes_after_modification(self, config_content: str, tmp_path: Path):
        """check_for_changes should detect file modification."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(config_content, encoding="utf-8")

        watcher = ConfigWatcher(config_path=config_path)

        # Ensure mtime difference (some filesystems have 1-second resolution)
        time.sleep(0.1)

        # Modify file
        updated = config_content + "city_sewer,SOFT,==,CITY,2.5,City sewer\n"
        config_path.write_text(updated, encoding="utf-8")

        # Force mtime update for filesystems with low resolution
        import os

        os.utime(config_path, None)

        assert watcher.check_for_changes() is True

    def test_check_for_changes_no_modification(self, config_content: str, tmp_path: Path):
        """check_for_changes should return False when no modification."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(config_content, encoding="utf-8")

        watcher = ConfigWatcher(config_path=config_path)
        watcher.check_for_changes()  # Reset state

        # No modification
        assert watcher.check_for_changes() is False

    def test_get_updated_config(self, config_content: str, tmp_path: Path):
        """get_updated_config should load and return configs."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(config_content, encoding="utf-8")

        watcher = ConfigWatcher(config_path=config_path)
        configs = watcher.get_updated_config()

        assert configs is not None
        assert len(configs) == 1
        assert configs[0].name == "no_hoa"

    def test_get_updated_config_invalid_keeps_previous(self, tmp_path: Path):
        """get_updated_config should keep previous config on invalid update."""
        valid_config = """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
"""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(valid_config, encoding="utf-8")

        watcher = ConfigWatcher(config_path=config_path)
        initial_configs = watcher.get_updated_config()
        assert initial_configs is not None
        assert len(initial_configs) == 1

        # Write invalid config
        invalid_config = """\
name,type,operator,threshold,severity,description
bad,HARD,==,0,1.5,HARD with severity
"""
        config_path.write_text(invalid_config, encoding="utf-8")

        # Should return previous valid config
        configs = watcher.get_updated_config()
        assert configs is not None
        assert len(configs) == 1
        assert configs[0].name == "no_hoa"

    def test_on_change_callback(self, config_content: str, tmp_path: Path):
        """on_change callback should be invoked on successful load."""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(config_content, encoding="utf-8")

        callback_results = []

        def on_change(configs):
            callback_results.append(len(configs))

        watcher = ConfigWatcher(config_path=config_path, on_change=on_change)
        watcher.get_updated_config()

        assert len(callback_results) == 1
        assert callback_results[0] == 1

    def test_file_not_exists(self, tmp_path: Path):
        """ConfigWatcher should handle missing file gracefully."""
        config_path = tmp_path / "nonexistent.csv"

        watcher = ConfigWatcher(config_path=config_path)
        assert watcher.check_for_changes() is False
        assert watcher.get_updated_config() is None


class TestKillSwitchFilterEvaluateWithConfigPath:
    """Tests for evaluation using config-loaded criteria."""

    def test_evaluate_with_config_loaded_criteria(self, sample_property, tmp_path: Path):
        """Evaluation should work with config-loaded criteria."""
        config = """\
name,type,operator,threshold,severity,description
no_hoa,HARD,==,0,0.0,NO HOA fees allowed
min_bedrooms,HARD,>=,4,0.0,Minimum 4 bedrooms
"""
        config_path = tmp_path / "kill_switch.csv"
        config_path.write_text(config, encoding="utf-8")

        filter_svc = KillSwitchFilter(config_path=config_path)
        verdict, severity, failures = filter_svc.evaluate_with_severity(sample_property)

        assert verdict == KillSwitchVerdict.PASS
        assert severity == 0.0
        assert len(failures) == 0
