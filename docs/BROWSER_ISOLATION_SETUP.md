# Browser Isolation Setup Guide

This guide explains how to configure browser window isolation for stealth automation on Windows. Browser isolation prevents the browser window from interfering with user input during non-headless stealth operations.

## Why Browser Isolation?

The stealth browser (nodriver) requires **non-headless mode** for effective PerimeterX bypass. However, a visible browser window can:

1. Interfere with user keyboard/mouse input
2. Steal focus from other applications
3. Be distracting during long extraction runs

Browser isolation solves these issues by positioning the browser window where it won't interfere.

## Isolation Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `virtual` | Virtual Display Driver (VDD) | Optimal isolation, best for long runs |
| `secondary` | Position on secondary monitor | Multi-monitor setups |
| `off_screen` | Position off-screen (right of primary) | Single monitor, no VDD |
| `minimize` | Start browser minimized | Fallback, less stealthy |
| `none` | No isolation (browser visible) | Debugging, manual intervention |

## Configuration

### CLI Usage

```bash
# Use Virtual Display Driver (default)
python scripts/extract_images.py --all --isolation virtual

# Use secondary monitor
python scripts/extract_images.py --all --isolation secondary

# Position off-screen
python scripts/extract_images.py --all --isolation off_screen

# Start minimized (fallback)
python scripts/extract_images.py --all --isolation minimize

# No isolation (visible browser)
python scripts/extract_images.py --all --isolation none

# Check detected displays
python scripts/extract_images.py --show-displays
```

### Environment Variables

```bash
# Set isolation mode
set BROWSER_ISOLATION=virtual_display

# Options: virtual_display, secondary_display, off_screen, minimize, none
```

### Python Configuration

```python
from phx_home_analysis.config.settings import (
    BrowserIsolationMode,
    StealthExtractionConfig,
)

config = StealthExtractionConfig(
    browser_headless=False,  # Non-headless for stealth
    isolation_mode=BrowserIsolationMode.VIRTUAL_DISPLAY,
    fallback_to_minimize=True,  # If VDD not found, use minimize
)
```

## Virtual Display Driver Setup (Recommended)

Virtual Display Driver (VDD) provides the best isolation by creating a virtual monitor that Chrome can render to without affecting your physical displays.

### Installation Options

#### Option 1: IddSampleDriver (Free, Open Source)

1. Download from [GitHub Releases](https://github.com/roshkins/IddSampleDriver/releases)
2. Extract the package
3. Right-click `IddSampleDriver.inf` and select "Install"
4. Restart Windows
5. Configure resolution in Display Settings

#### Option 2: Virtual Display Manager (Commercial)

1. Download from [Amyuni Virtual Display](https://www.amyuni.com/en/products/virtual-display/)
2. Run installer
3. Configure displays in Virtual Display Manager

### Verifying Installation

```bash
# Check if VDD is detected
python scripts/extract_images.py --show-displays
```

Expected output with VDD:

```
Display Detection
============================================================
Detected 2 display(s):
  Display 0: 1920x1080 at (0, 0) (primary)
  Display 1: 1920x1080 at (1920, 0) (virtual)
Virtual Display Driver: Installed
Recommended isolation position: (1920, 0)
============================================================
```

## Fallback Strategies

If your preferred isolation mode isn't available, the system falls back gracefully:

```
virtual_display (not found) -> minimize (if fallback enabled)
                            -> off_screen (if fallback disabled)

secondary_display (not found) -> minimize (if fallback enabled)
                              -> off_screen (if fallback disabled)
```

To disable fallback to minimize:

```python
config = StealthExtractionConfig(
    isolation_mode=BrowserIsolationMode.VIRTUAL_DISPLAY,
    fallback_to_minimize=False,  # Use off_screen instead
)
```

## Alternative Solutions

### WSL2 with Xvfb

For Linux-style virtual framebuffer:

```bash
# In WSL2
sudo apt install xvfb
Xvfb :99 -screen 0 1280x720x24 &
export DISPLAY=:99
python scripts/extract_images.py --all
```

### Docker with VNC

```dockerfile
FROM python:3.12
RUN apt-get update && apt-get install -y \
    chromium \
    xvfb \
    x11vnc
# Configure VNC and Xvfb...
```

### Remote Desktop

Use Windows Remote Desktop to run extraction on a headless remote session.

## Troubleshooting

### Browser Window Still Visible

1. Verify isolation mode is set:
   ```bash
   python scripts/extract_images.py --all --isolation virtual -v
   ```
2. Check logs for isolation configuration messages
3. Ensure `BROWSER_HEADLESS` is not set to `true`

### VDD Not Detected

1. Verify driver installation:
   ```bash
   python scripts/extract_images.py --show-displays
   ```
2. Check Device Manager for virtual display adapter
3. Try restarting Windows
4. Reinstall VDD if needed

### Off-Screen Position Not Working

Some systems don't render windows positioned off-screen. Solutions:

1. Use `--isolation minimize` as fallback
2. Install VDD for proper isolation
3. Connect a secondary monitor

### Performance Impact

| Mode | Performance | Notes |
|------|-------------|-------|
| virtual | Best | VDD provides full rendering |
| secondary | Good | Uses existing monitor |
| off_screen | Good | May not render on some systems |
| minimize | Moderate | May affect anti-bot detection |
| none | Best | But interferes with user |

## Display Detection API

For programmatic access to display information:

```python
from phx_home_analysis.services.infrastructure import (
    DisplayInfo,
    get_displays,
    find_virtual_display,
    get_recommended_position,
    check_virtual_display_driver,
    get_display_summary,
)

# Get all displays
displays = get_displays()
for display in displays:
    print(f"{display.index}: {display.width}x{display.height} at ({display.x}, {display.y})")
    print(f"  Primary: {display.is_primary}, Virtual: {display.is_virtual}")

# Find virtual display specifically
vd = find_virtual_display()
if vd:
    print(f"Virtual display at ({vd.x}, {vd.y})")

# Get recommended position for browser
x, y = get_recommended_position()
print(f"Recommended position: ({x}, {y})")

# Check if VDD is installed
if check_virtual_display_driver():
    print("Virtual Display Driver is installed")

# Print summary for debugging
print(get_display_summary())
```

## Best Practices

1. **Use VDD for Production**: Virtual Display Driver provides the most reliable isolation
2. **Test Isolation**: Always verify with `--show-displays` before long runs
3. **Enable Fallback**: Keep `fallback_to_minimize=True` for resilience
4. **Monitor Performance**: Some isolation modes may affect rendering speed
5. **Log Verification**: Check logs for "Using virtual display for isolation" messages

## Related Documentation

- [Image Extraction Pipeline](./IMAGE_EXTRACTION.md)
- [Stealth Browser Configuration](./STEALTH_BROWSER.md)
- [Anti-Bot Bypass Techniques](./ANTI_BOT_BYPASS.md)
