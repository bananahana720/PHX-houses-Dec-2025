"""Integration tests for complete transient error recovery flow.

Tests verify:
- Retry decorator with work_items.json integration
- Successful retry does not record failure
- Exhausted retries records failure with correct details
- Permanent errors recorded immediately
- Pipeline continues after item failure
"""

import json
from pathlib import Path

import pytest

from phx_home_analysis.errors import (
    get_failure_summary,
    mark_item_failed,
    retry_with_backoff,
)


class TestTransientErrorRecoveryIntegration:
    """Integration tests for complete error recovery flow."""

    @pytest.fixture
    def work_items_file(self, tmp_path: Path) -> Path:
        """Create a test work_items.json file."""
        work_items_path = tmp_path / "work_items.json"
        data = {
            "session": {"session_id": "test123"},
            "work_items": [
                {
                    "address": "123 Main St, Phoenix, AZ 85001",
                    "phases": {"phase1_listing": {"status": "pending"}},
                    "last_updated": "2025-12-04T10:00:00Z",
                },
                {
                    "address": "456 Oak Ave, Mesa, AZ 85201",
                    "phases": {"phase1_listing": {"status": "pending"}},
                    "last_updated": "2025-12-04T10:00:00Z",
                },
                {
                    "address": "789 Elm Blvd, Tempe, AZ 85281",
                    "phases": {"phase1_listing": {"status": "pending"}},
                    "last_updated": "2025-12-04T10:00:00Z",
                },
            ],
            "summary": {"failed": 0},
        }
        work_items_path.write_text(json.dumps(data, indent=2))
        return work_items_path

    @pytest.mark.asyncio
    async def test_retry_then_succeed_no_failure_recorded(
        self, work_items_file: Path
    ) -> None:
        """Successful retry should not record failure."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def fetch_data() -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return {"data": "success"}

        result = await fetch_data()
        assert result == {"data": "success"}

        # Verify no failure recorded (we didn't mark it failed)
        summary = get_failure_summary(work_items_file)
        assert summary["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_exhausted_retries_records_failure(
        self, work_items_file: Path
    ) -> None:
        """Exhausted retries should record failure in work_items.json."""
        error = ConnectionError("Persistent failure")

        @retry_with_backoff(max_retries=2, min_delay=0.01)
        async def fetch_data() -> dict[str, str]:
            raise error

        with pytest.raises(ConnectionError):
            await fetch_data()

        # Record the failure
        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error,
        )

        # Verify failure recorded
        summary = get_failure_summary(work_items_file)
        assert summary["failed_count"] == 1
        assert summary["failures"][0]["phase"] == "phase1_listing"
        assert summary["failures"][0]["error_category"] == "transient"

    @pytest.mark.asyncio
    async def test_permanent_error_immediate_failure(
        self, work_items_file: Path
    ) -> None:
        """Permanent error should immediately record failure."""
        error = Exception("Not found")
        error.status_code = 404  # type: ignore[attr-defined]

        @retry_with_backoff(max_retries=3, min_delay=0.01)
        async def fetch_data() -> dict[str, str]:
            raise error

        with pytest.raises(Exception, match="Not found"):
            await fetch_data()

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error,
        )

        summary = get_failure_summary(work_items_file)
        assert summary["failed_count"] == 1
        assert summary["failures"][0]["error_category"] == "permanent"

    @pytest.mark.asyncio
    async def test_pipeline_continues_after_item_failure(
        self, work_items_file: Path
    ) -> None:
        """Pipeline should continue processing after one item fails."""
        addresses = [
            "123 Main St, Phoenix, AZ 85001",
            "456 Oak Ave, Mesa, AZ 85201",
            "789 Elm Blvd, Tempe, AZ 85281",
        ]

        results: list[dict[str, str | bool]] = []
        for i, addr in enumerate(addresses):

            @retry_with_backoff(max_retries=1, min_delay=0.01)
            async def process_item(
                address: str = addr, index: int = i
            ) -> dict[str, str | bool]:
                if index == 1:  # Second item fails
                    raise ConnectionError("Failed")
                return {"address": address, "success": True}

            try:
                result = await process_item()
                results.append(result)
            except ConnectionError:
                mark_item_failed(
                    work_items_file, addr, "phase1_listing", ConnectionError("Failed")
                )

        # Two items succeeded, one failed
        assert len(results) == 2
        summary = get_failure_summary(work_items_file)
        assert summary["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_multiple_failures_tracked_separately(
        self, work_items_file: Path
    ) -> None:
        """Multiple failures should be tracked separately."""
        # Fail two different items
        error1 = ConnectionError("Network error")
        error2 = Exception("Rate limited")
        error2.status_code = 429  # type: ignore[attr-defined]

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error1,
        )
        mark_item_failed(
            work_items_file,
            "456 Oak Ave, Mesa, AZ 85201",
            "phase1_listing",
            error2,
        )

        summary = get_failure_summary(work_items_file)
        assert summary["failed_count"] == 2

        # Both should be transient
        categories = [f["error_category"] for f in summary["failures"]]
        assert all(c == "transient" for c in categories)

    @pytest.mark.asyncio
    async def test_failure_includes_timestamp(self, work_items_file: Path) -> None:
        """Failure should include timestamp."""
        error = ConnectionError("Network error")

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error,
        )

        summary = get_failure_summary(work_items_file)
        assert len(summary["failures"]) == 1
        assert summary["failures"][0]["failed_at"] is not None
        # Should be ISO format timestamp
        assert "T" in summary["failures"][0]["failed_at"]

    @pytest.mark.asyncio
    async def test_failure_includes_actionable_error_message(
        self, work_items_file: Path
    ) -> None:
        """Failure should include actionable error message."""
        error = Exception("Unauthorized")
        error.status_code = 401  # type: ignore[attr-defined]

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error,
        )

        summary = get_failure_summary(work_items_file)
        error_msg = summary["failures"][0]["error"]

        # Should mention status code
        assert "401" in error_msg
        # Should include actionable guidance
        assert "token" in error_msg.lower() or "api" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_retrying_status_when_can_retry(self, work_items_file: Path) -> None:
        """Should set 'retrying' status when can_retry=True for transient errors."""
        error = ConnectionError("Network error")

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error,
            can_retry=True,
        )

        # Read back the file to check status
        with open(work_items_file) as f:
            data = json.load(f)

        status = data["work_items"][0]["phases"]["phase1_listing"]["status"]
        assert status == "retrying"

    @pytest.mark.asyncio
    async def test_failed_status_for_permanent_error_even_with_can_retry(
        self, work_items_file: Path
    ) -> None:
        """Should set 'failed' status for permanent errors even when can_retry=True."""
        error = Exception("Not found")
        error.status_code = 404  # type: ignore[attr-defined]

        mark_item_failed(
            work_items_file,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            error,
            can_retry=True,  # Even with this, permanent errors should be 'failed'
        )

        # Read back the file to check status
        with open(work_items_file) as f:
            data = json.load(f)

        status = data["work_items"][0]["phases"]["phase1_listing"]["status"]
        assert status == "failed"

    @pytest.mark.asyncio
    async def test_missing_work_items_file_handled_gracefully(
        self, tmp_path: Path
    ) -> None:
        """Should handle missing work_items.json gracefully."""
        nonexistent_path = tmp_path / "nonexistent.json"

        # Should not raise
        mark_item_failed(
            nonexistent_path,
            "123 Main St, Phoenix, AZ 85001",
            "phase1_listing",
            ConnectionError("Error"),
        )

        # Summary should return empty
        summary = get_failure_summary(nonexistent_path)
        assert summary["failed_count"] == 0
        assert summary["failures"] == []

    @pytest.mark.asyncio
    async def test_unknown_address_handled_gracefully(
        self, work_items_file: Path
    ) -> None:
        """Should handle unknown address gracefully."""
        # Should not raise for unknown address
        mark_item_failed(
            work_items_file,
            "999 Unknown St, Nowhere, AZ 00000",
            "phase1_listing",
            ConnectionError("Error"),
        )

        # No failure should be recorded
        summary = get_failure_summary(work_items_file)
        assert summary["failed_count"] == 0
