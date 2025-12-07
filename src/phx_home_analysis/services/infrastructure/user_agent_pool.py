"""User-Agent rotation pool for stealth browser automation.

Provides thread-safe rotation of 20+ User-Agent signatures to avoid
bot detection patterns. Supports random selection and sequential rotation.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Iterator
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)


class UserAgentRotator:
    """Rotates User-Agent strings for stealth web scraping.

    Loads User-Agent signatures from config file and provides
    thread-safe rotation mechanisms.

    Example:
        ```python
        rotator = UserAgentRotator()
        ua1 = rotator.get_random()  # Random selection
        ua2 = next(rotator)         # Sequential rotation
        ```
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parents[4] / "config" / "user_agents.txt"

    def __init__(self, config_path: Path | None = None):
        """Initialize User-Agent rotator.

        Args:
            config_path: Path to user_agents.txt file (optional)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._user_agents: list[str] = []
        self._current_index = 0
        self._lock = Lock()

        self._load_user_agents()

    def _load_user_agents(self) -> None:
        """Load User-Agent signatures from config file.

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file has fewer than 20 UAs
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"User-Agent config file not found: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Filter out comments and empty lines
        user_agents = [
            line.strip() for line in lines if line.strip() and not line.strip().startswith("#")
        ]

        if len(user_agents) < 20:
            raise ValueError(
                f"User-Agent pool must have at least 20 entries, "
                f"got {len(user_agents)} in {self.config_path}"
            )

        self._user_agents = user_agents
        logger.info(
            "Loaded %d User-Agent signatures from %s",
            len(self._user_agents),
            self.config_path,
        )

    def get_random(self) -> str:
        """Get random User-Agent from pool.

        Returns:
            Random User-Agent string

        Thread-safe: Yes
        """
        with self._lock:
            return random.choice(self._user_agents)

    def get_next(self) -> str:
        """Get next User-Agent in sequential rotation.

        Returns:
            Next User-Agent string in sequence

        Thread-safe: Yes
        """
        with self._lock:
            ua = self._user_agents[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._user_agents)
            return ua

    def __next__(self) -> str:
        """Support iterator protocol for sequential rotation.

        Returns:
            Next User-Agent in sequence
        """
        return self.get_next()

    def __iter__(self) -> Iterator[str]:
        """Support iteration protocol.

        Returns:
            Self as iterator
        """
        return self

    def __len__(self) -> int:
        """Get pool size.

        Returns:
            Number of User-Agent signatures in pool
        """
        return len(self._user_agents)

    def get_all(self) -> list[str]:
        """Get all User-Agent signatures.

        Returns:
            Copy of all User-Agent strings

        Thread-safe: Yes
        """
        with self._lock:
            return self._user_agents.copy()


# Module-level singleton
_rotator: UserAgentRotator | None = None
_rotator_lock = Lock()


def get_rotator() -> UserAgentRotator:
    """Get or create the global User-Agent rotator instance.

    Returns:
        UserAgentRotator singleton

    Thread-safe: Yes
    """
    global _rotator
    if _rotator is None:
        with _rotator_lock:
            if _rotator is None:  # Double-check after acquiring lock
                _rotator = UserAgentRotator()
    return _rotator


def get_random_user_agent() -> str:
    """Get random User-Agent from global rotator.

    Convenience function for simple random selection.

    Returns:
        Random User-Agent string

    Thread-safe: Yes
    """
    return get_rotator().get_random()
