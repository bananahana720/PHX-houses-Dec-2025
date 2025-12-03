"""CAPTCHA metrics tracking and alerting for image extraction pipeline.

Provides comprehensive monitoring of CAPTCHA encounters, solve success/failure rates,
and intelligent alerting for degradation detection. Enables data-driven optimization
and early warning when anti-bot protection changes.

Example CAPTCHA Event Log Entry:
    {
        "timestamp": "2025-12-02T14:30:45.123456-07:00",
        "event_type": "captcha_solved",
        "property_address": "123 Main St, Phoenix, AZ 85001",
        "source": "zillow",
        "details": {
            "solve_time_seconds": 6.42,
            "hold_duration": 5.3,
            "retry_attempt": 1
        },
        "correlation_id": "abc123de"
    }

Usage:
    ```python
    # Initialize metrics tracker
    metrics = CaptchaMetrics()

    # Record CAPTCHA encounter
    start_time = time.time()
    solved = await attempt_captcha_solve(tab)
    solve_time = time.time() - start_time

    metrics.record_encounter(solved=solved, solve_time=solve_time)

    # Check for alerting conditions
    should_alert, reason = metrics.should_alert()
    if should_alert:
        logger.error("CAPTCHA alert triggered: %s", reason)

    # Log structured event
    log_captcha_event(
        event_type="captcha_solved" if solved else "captcha_failed",
        property_address=property.full_address,
        details={"solve_time_seconds": solve_time},
        source="zillow"
    )
    ```
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


def _ensure_log_directory() -> Path:
    """Ensure data/logs directory exists.

    Returns:
        Path to logs directory
    """
    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parents[5]  # phx_home_analysis/services/image_extraction/metrics.py -> root
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def log_captcha_event(
    event_type: str,
    property_address: str,
    details: dict[str, Any],
    source: str = "unknown",
    correlation_id: str | None = None,
) -> None:
    """Log structured CAPTCHA event to JSONL file.

    Writes machine-readable event logs for analysis, debugging, and correlation.
    Each line is a complete JSON object for streaming processing.

    Args:
        event_type: Event type (captcha_detected, captcha_solved, captcha_failed)
        property_address: Full property address being processed
        details: Event-specific details (solve_time, retry_attempt, error_msg, etc.)
        source: Data source name (zillow, redfin, etc.)
        correlation_id: Optional ID to correlate related events (defaults to new UUID)

    Example:
        >>> log_captcha_event(
        ...     event_type="captcha_solved",
        ...     property_address="123 Main St, Phoenix, AZ 85001",
        ...     details={"solve_time_seconds": 6.42, "hold_duration": 5.3},
        ...     source="zillow"
        ... )
    """
    logs_dir = _ensure_log_directory()
    log_file = logs_dir / "captcha_events.jsonl"

    # Build event record
    event = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "event_type": event_type,
        "property_address": property_address,
        "source": source,
        "details": details,
        "correlation_id": correlation_id or str(uuid4())[:8],
    }

    try:
        # Append to JSONL file (one JSON object per line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        logger.debug(
            "CAPTCHA event logged: %s for %s (source: %s)",
            event_type,
            property_address,
            source,
        )
    except OSError as e:
        logger.error("Failed to write CAPTCHA event log: %s", e)


@dataclass
class CaptchaMetrics:
    """Track CAPTCHA encounter rates and solve success/failure metrics.

    Provides real-time monitoring of CAPTCHA solving performance with
    intelligent alerting for degradation detection.

    Attributes:
        captcha_encounters: Total CAPTCHA challenges encountered
        captcha_solves_success: Successful CAPTCHA solves
        captcha_solves_failed: Failed CAPTCHA solve attempts
        solve_times: List of solve times in seconds (for average calculation)

    Properties:
        solve_rate: Success rate as float 0.0-1.0
        average_solve_time: Mean solve time in seconds

    Alerting Thresholds:
        - CRITICAL: Solve rate < 50% over 10+ attempts
        - WARNING: CAPTCHA encounters > 50% of extraction attempts
        - INFO: First CAPTCHA of session

    Example:
        >>> metrics = CaptchaMetrics()
        >>> metrics.record_encounter(solved=True, solve_time=6.2)
        >>> metrics.record_encounter(solved=False, solve_time=8.5)
        >>> metrics.solve_rate
        0.5
        >>> metrics.average_solve_time
        7.35
        >>> should_alert, reason = metrics.should_alert()
        >>> if should_alert:
        ...     logger.error("Alert: %s", reason)
    """

    captcha_encounters: int = 0
    captcha_solves_success: int = 0
    captcha_solves_failed: int = 0
    solve_times: list[float] = field(default_factory=list)

    # Track extraction attempts for encounter rate calculation
    _extraction_attempts: int = 0

    @property
    def solve_rate(self) -> float:
        """Calculate CAPTCHA solve success rate.

        Returns:
            Success rate as float 0.0-1.0, or 0.0 if no encounters

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.captcha_solves_success = 8
            >>> metrics.captcha_encounters = 10
            >>> metrics.solve_rate
            0.8
        """
        if self.captcha_encounters == 0:
            return 0.0
        return self.captcha_solves_success / self.captcha_encounters

    @property
    def average_solve_time(self) -> float:
        """Calculate average CAPTCHA solve time.

        Returns:
            Mean solve time in seconds, or 0.0 if no solves

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.solve_times = [5.2, 6.8, 4.9]
            >>> metrics.average_solve_time
            5.633333333333334
        """
        if not self.solve_times:
            return 0.0
        return sum(self.solve_times) / len(self.solve_times)

    @property
    def encounter_rate(self) -> float:
        """Calculate CAPTCHA encounter rate across all extractions.

        Returns:
            Encounter rate as float 0.0-1.0, or 0.0 if no attempts

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.captcha_encounters = 15
            >>> metrics._extraction_attempts = 100
            >>> metrics.encounter_rate
            0.15
        """
        if self._extraction_attempts == 0:
            return 0.0
        return self.captcha_encounters / self._extraction_attempts

    def record_encounter(self, solved: bool, solve_time: float) -> None:
        """Record a CAPTCHA encounter with outcome.

        Updates encounter counts, success/failure rates, and solve times.

        Args:
            solved: True if CAPTCHA was solved successfully
            solve_time: Time taken to solve (or fail) in seconds

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.record_encounter(solved=True, solve_time=6.2)
            >>> metrics.captcha_encounters
            1
            >>> metrics.captcha_solves_success
            1
            >>> metrics.solve_times
            [6.2]
        """
        self.captcha_encounters += 1

        if solved:
            self.captcha_solves_success += 1
        else:
            self.captcha_solves_failed += 1

        self.solve_times.append(solve_time)

        logger.debug(
            "CAPTCHA encounter recorded: solved=%s, time=%.2fs (total: %d, rate: %.1f%%)",
            solved,
            solve_time,
            self.captcha_encounters,
            self.solve_rate * 100,
        )

    def record_extraction_attempt(self) -> None:
        """Record an extraction attempt (for encounter rate calculation).

        Call this for EVERY property extraction attempt, regardless of
        whether a CAPTCHA was encountered.

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.record_extraction_attempt()
            >>> metrics._extraction_attempts
            1
        """
        self._extraction_attempts += 1

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive metrics summary.

        Returns:
            Dict with all metrics and calculated rates

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.captcha_encounters = 10
            >>> metrics.captcha_solves_success = 8
            >>> metrics.captcha_solves_failed = 2
            >>> metrics.solve_times = [5.2, 6.1, 4.8, 7.3, 5.9, 6.4, 5.5, 6.8, 5.1, 7.2]
            >>> summary = metrics.get_summary()
            >>> summary["solve_rate"]
            0.8
            >>> summary["average_solve_time"]
            6.03
        """
        return {
            "captcha_encounters": self.captcha_encounters,
            "captcha_solves_success": self.captcha_solves_success,
            "captcha_solves_failed": self.captcha_solves_failed,
            "solve_rate": round(self.solve_rate, 3),
            "average_solve_time": round(self.average_solve_time, 2),
            "encounter_rate": round(self.encounter_rate, 3),
            "extraction_attempts": self._extraction_attempts,
        }

    def should_alert(self) -> tuple[bool, str]:
        """Check if alerting conditions are met.

        Alerting Rules:
            - CRITICAL: Solve rate < 50% over 10+ attempts → ERROR log
            - WARNING: CAPTCHA encounters > 50% of extractions → WARNING log
            - INFO: First CAPTCHA of session → INFO log

        Returns:
            Tuple of (should_alert: bool, reason: str)

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.captcha_encounters = 15
            >>> metrics.captcha_solves_success = 3
            >>> metrics.captcha_solves_failed = 12
            >>> should_alert, reason = metrics.should_alert()
            >>> should_alert
            True
            >>> "solve rate" in reason.lower()
            True
        """
        # CRITICAL: Low solve rate over significant sample size
        if self.captcha_encounters >= 10 and self.solve_rate < 0.5:
            return (
                True,
                f"CRITICAL: CAPTCHA solve rate {self.solve_rate:.1%} < 50% over "
                f"{self.captcha_encounters} attempts. Recommend: (1) Check proxy rotation, "
                "(2) Verify hold duration randomization, (3) Review anti-detection techniques, "
                "(4) Consider longer delays between requests."
            )

        # WARNING: High encounter rate suggests detection
        if self._extraction_attempts >= 10 and self.encounter_rate > 0.5:
            return (
                True,
                f"WARNING: CAPTCHA encounter rate {self.encounter_rate:.1%} > 50% of "
                f"{self._extraction_attempts} extractions. Anti-bot detection may be triggering. "
                "Consider: (1) Rotating proxies, (2) Increasing delays, "
                "(3) Randomizing viewport/user-agent."
            )

        # INFO: First CAPTCHA is noteworthy for tracking
        if self.captcha_encounters == 1:
            return (
                True,
                f"INFO: First CAPTCHA encountered in this session (solve rate: "
                f"{self.solve_rate:.1%}). Monitoring for degradation."
            )

        return (False, "")

    def reset(self) -> None:
        """Reset all metrics to zero.

        Useful for starting a new monitoring session or after alert conditions
        have been addressed.

        Example:
            >>> metrics = CaptchaMetrics()
            >>> metrics.captcha_encounters = 10
            >>> metrics.reset()
            >>> metrics.captcha_encounters
            0
        """
        self.captcha_encounters = 0
        self.captcha_solves_success = 0
        self.captcha_solves_failed = 0
        self.solve_times = []
        self._extraction_attempts = 0

        logger.info("CAPTCHA metrics reset")
