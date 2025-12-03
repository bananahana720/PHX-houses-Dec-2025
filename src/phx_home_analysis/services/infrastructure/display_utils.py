"""Display detection and configuration utilities for browser isolation.

Provides Windows-specific display detection to position browser windows
on virtual displays or secondary monitors, preventing interference with
user input during stealth browser automation.

Platform Support:
    - Windows: Full support via ctypes/Win32 API
    - macOS/Linux: Stub implementation (returns empty list)

Usage:
    from phx_home_analysis.services.infrastructure.display_utils import (
        get_displays,
        find_virtual_display,
        get_recommended_position,
        check_virtual_display_driver,
    )

    # Get recommended position for browser isolation
    x, y = get_recommended_position()

    # Check if Virtual Display Driver is installed
    if check_virtual_display_driver():
        vd = find_virtual_display()
        if vd:
            x, y = vd.x, vd.y
"""

import ctypes
import logging
import platform
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DisplayInfo:
    """Information about a connected display.

    Attributes:
        index: Zero-based display index
        x: X coordinate of display origin (pixels)
        y: Y coordinate of display origin (pixels)
        width: Display width in pixels
        height: Display height in pixels
        is_primary: Whether this is the primary display
        device_name: Windows device name (e.g., r'\\.\\DISPLAY1')
        is_virtual: Whether this appears to be a virtual display
    """

    index: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool
    device_name: str = ""
    is_virtual: bool = False

    @property
    def right(self) -> int:
        """Right edge X coordinate."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Bottom edge Y coordinate."""
        return self.y + self.height

    def __str__(self) -> str:
        """Human-readable display description."""
        flags = []
        if self.is_primary:
            flags.append("primary")
        if self.is_virtual:
            flags.append("virtual")
        flag_str = f" ({', '.join(flags)})" if flags else ""
        return f"Display {self.index}: {self.width}x{self.height} at ({self.x}, {self.y}){flag_str}"


def get_displays() -> list[DisplayInfo]:
    """Get list of connected displays.

    On Windows, uses the Win32 API (EnumDisplayMonitors) to enumerate
    all connected displays including virtual displays.

    On other platforms, returns an empty list with a warning.

    Returns:
        List of DisplayInfo objects for each connected display,
        sorted by display index.
    """
    if platform.system() != "Windows":
        logger.warning("Display detection not implemented for %s", platform.system())
        return []

    try:
        return _get_windows_displays()
    except Exception as e:
        logger.error("Failed to enumerate displays: %s", e)
        return []


def _get_windows_displays() -> list[DisplayInfo]:
    """Get displays using Windows Win32 API.

    Uses EnumDisplayMonitors and GetMonitorInfo to enumerate displays.

    Returns:
        List of DisplayInfo objects
    """
    displays: list[DisplayInfo] = []

    # Define required structures
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    class MONITORINFOEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    # Constants
    MONITORINFOF_PRIMARY = 0x00000001

    # Callback type for EnumDisplayMonitors
    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,  # hMonitor
        ctypes.c_void_p,  # hdcMonitor
        ctypes.POINTER(RECT),  # lprcMonitor
        ctypes.c_longlong,  # dwData
    )

    # Get function references
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]

    display_index = [0]  # Use list for mutable closure

    def monitor_callback(
        hMonitor: ctypes.c_void_p,
        hdcMonitor: ctypes.c_void_p,
        lprcMonitor: ctypes.POINTER,  # type: ignore[type-arg]
        dwData: ctypes.c_longlong,
    ) -> bool:
        """Callback for each enumerated monitor."""
        try:
            # Get detailed monitor info
            monitor_info = MONITORINFOEX()
            monitor_info.cbSize = ctypes.sizeof(MONITORINFOEX)

            if user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info)):
                rc = monitor_info.rcMonitor
                is_primary = bool(monitor_info.dwFlags & MONITORINFOF_PRIMARY)
                device_name = monitor_info.szDevice

                # Check if this appears to be a virtual display
                # Virtual Display Driver devices typically have specific patterns
                is_virtual = _is_virtual_display(device_name)

                display = DisplayInfo(
                    index=display_index[0],
                    x=rc.left,
                    y=rc.top,
                    width=rc.right - rc.left,
                    height=rc.bottom - rc.top,
                    is_primary=is_primary,
                    device_name=device_name,
                    is_virtual=is_virtual,
                )
                displays.append(display)
                display_index[0] += 1

                logger.debug("Found display: %s", display)

        except Exception as e:
            logger.warning("Error processing monitor: %s", e)

        return True  # Continue enumeration

    # Create callback and enumerate monitors
    callback = MONITORENUMPROC(monitor_callback)
    user32.EnumDisplayMonitors(None, None, callback, 0)

    # Sort by index
    displays.sort(key=lambda d: d.index)

    logger.info("Detected %d display(s)", len(displays))
    return displays


def _is_virtual_display(device_name: str) -> bool:
    """Check if a device name indicates a virtual display.

    Virtual Display Driver (VDD) and other virtual display drivers
    often have specific naming patterns.

    Args:
        device_name: Windows device name (e.g., r'\\.\\DISPLAY1')

    Returns:
        True if this appears to be a virtual display
    """
    if not device_name:
        return False

    device_name_lower = device_name.lower()

    # Known virtual display patterns
    virtual_patterns = [
        "virtual",
        "vdd",
        "idisplay",
        "spacedesk",
        "parsec",
        "splashtop",
        "deskreen",
        "dummy",
    ]

    for pattern in virtual_patterns:
        if pattern in device_name_lower:
            return True

    return False


def find_virtual_display() -> DisplayInfo | None:
    """Find virtual display driver if installed.

    Searches for displays that appear to be virtual displays
    based on their device name patterns.

    Returns:
        DisplayInfo for virtual display, or None if not found
    """
    displays = get_displays()

    for display in displays:
        if display.is_virtual:
            logger.info("Found virtual display: %s", display)
            return display

    logger.debug("No virtual display found")
    return None


def get_recommended_position() -> tuple[int, int]:
    """Get recommended window position for browser isolation.

    Strategy:
    1. If virtual display exists, use its position
    2. If secondary monitor exists, use its position
    3. Fallback: position off-screen to the right of primary

    Note: Off-screen positioning may not render on all systems,
    but works for isolation purposes.

    Returns:
        Tuple of (x, y) coordinates for window positioning
    """
    displays = get_displays()

    if not displays:
        # No displays detected, use fallback
        logger.warning("No displays detected, using fallback position (1920, 0)")
        return (1920, 0)

    # Priority 1: Virtual display
    for display in displays:
        if display.is_virtual:
            logger.info("Recommended position: virtual display at (%d, %d)", display.x, display.y)
            return (display.x, display.y)

    # Priority 2: Secondary (non-primary) display
    secondary_displays = [d for d in displays if not d.is_primary]
    if secondary_displays:
        # Use the first secondary display
        secondary = secondary_displays[0]
        logger.info("Recommended position: secondary display at (%d, %d)", secondary.x, secondary.y)
        return (secondary.x, secondary.y)

    # Priority 3: Off-screen to the right of primary
    primary = next((d for d in displays if d.is_primary), displays[0])
    position = (primary.right, 0)
    logger.info(
        "Recommended position: off-screen at (%d, %d) (right of primary)",
        position[0],
        position[1],
    )
    return position


def check_virtual_display_driver() -> bool:
    """Check if Virtual Display Driver is installed.

    Looks for virtual displays or known VDD registry keys.

    Returns:
        True if virtual display driver appears to be installed
    """
    # Check for virtual displays
    displays = get_displays()
    if any(d.is_virtual for d in displays):
        logger.info("Virtual Display Driver detected via display enumeration")
        return True

    # On Windows, check registry for common VDD installations
    if platform.system() == "Windows":
        try:
            import winreg

            vdd_registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Virtual Display Driver"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\IddSampleDriver"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\VDD"),
            ]

            for hkey, path in vdd_registry_paths:
                try:
                    winreg.OpenKey(hkey, path)
                    logger.info("Virtual Display Driver detected via registry: %s", path)
                    return True
                except FileNotFoundError:
                    continue
                except Exception as e:
                    logger.debug("Registry check failed for %s: %s", path, e)

        except ImportError:
            logger.debug("winreg not available")

    logger.debug("Virtual Display Driver not detected")
    return False


def get_display_summary() -> str:
    """Get human-readable summary of detected displays.

    Useful for logging and debugging.

    Returns:
        Multi-line string describing all detected displays
    """
    displays = get_displays()

    if not displays:
        return "No displays detected"

    lines = [f"Detected {len(displays)} display(s):"]
    for display in displays:
        lines.append(f"  {display}")

    vdd_installed = check_virtual_display_driver()
    lines.append(f"Virtual Display Driver: {'Installed' if vdd_installed else 'Not detected'}")

    recommended = get_recommended_position()
    lines.append(f"Recommended isolation position: ({recommended[0]}, {recommended[1]})")

    return "\n".join(lines)


# Type for progress callbacks
DisplayChangeCallback = Callable[[list[DisplayInfo]], None]

_display_change_callbacks: list[DisplayChangeCallback] = []


def register_display_change_callback(callback: DisplayChangeCallback) -> None:
    """Register callback for display configuration changes.

    Note: This is a placeholder for future implementation.
    Windows display change notifications require a message loop
    which is complex to implement in an async context.

    Args:
        callback: Function to call when displays change
    """
    _display_change_callbacks.append(callback)
    logger.debug("Registered display change callback (note: not yet implemented)")


def unregister_display_change_callback(callback: DisplayChangeCallback) -> None:
    """Unregister display change callback.

    Args:
        callback: Previously registered callback
    """
    if callback in _display_change_callbacks:
        _display_change_callbacks.remove(callback)
        logger.debug("Unregistered display change callback")
