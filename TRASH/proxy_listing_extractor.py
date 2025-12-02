#!/usr/bin/env python3
"""
Proxy-enabled listing extractor for real estate websites.
Uses rotating proxies and stealth techniques to bypass CAPTCHA and rate limiting.
"""

import asyncio
import hashlib
import json
import random
import sys
from datetime import datetime
from pathlib import Path

# Check for playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.async_api import async_playwright

# Check for playwright-stealth
try:
    from playwright_stealth import Stealth
except ImportError:
    print("Installing playwright-stealth...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright-stealth"], check=True)
    from playwright_stealth import Stealth


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "property_images" / "processed"
METADATA_DIR = DATA_DIR / "property_images" / "metadata"
CONFIG_DIR = PROJECT_ROOT / "config"

# Proxy configuration - Rotating Residential Proxy (auto-rotates IP each request)
# Single endpoint that automatically assigns random residential IP per request
PROXIES = [
    {"server": "http://p.webshare.io:80", "username": "svcvoqpm-rotate", "password": "g2j2p2cv602u"},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def property_hash(address: str) -> str:
    """Generate property hash from address."""
    return hashlib.md5(address.lower().encode()).hexdigest()[:8]


def get_random_proxy():
    """Get a random proxy from the pool."""
    return random.choice(PROXIES)


def get_random_user_agent():
    """Get a random user agent."""
    return random.choice(USER_AGENTS)


async def extract_zillow_listing(address: str, proxy: dict = None) -> dict:
    """Extract listing data and images from Zillow."""

    # Format address for Zillow URL
    formatted = address.replace(",", "").replace(" ", "-")
    url = f"https://www.zillow.com/homes/{formatted}_rb/"

    prop_hash = property_hash(address)
    image_dir = IMAGES_DIR / prop_hash
    image_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "address": address,
        "property_hash": prop_hash,
        "source": "zillow",
        "status": "pending",
        "url": url,
        "data": {},
        "images": [],
        "errors": []
    }

    proxy = proxy or get_random_proxy()
    user_agent = get_random_user_agent()

    print(f"\n{'='*60}")
    print(f"Extracting: {address}")
    print(f"URL: {url}")
    print(f"Proxy: {proxy['server']}")
    print(f"{'='*60}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            proxy=proxy,
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/Phoenix",
            geolocation={"latitude": 33.4484, "longitude": -112.0740},
            permissions=["geolocation"],
        )

        page = await context.new_page()

        # Apply stealth techniques using Stealth class
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # Additional stealth init scripts
        await page.add_init_script("""
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});

            // Override chrome property
            window.chrome = { runtime: {} };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        try:
            # Navigate with longer timeout
            print("Navigating to Zillow...")

            # Add random delay before navigation (human-like)
            await asyncio.sleep(random.uniform(1, 3))

            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Human-like behavior: random mouse movements and scrolling
            await asyncio.sleep(random.uniform(2, 4))
            await page.mouse.move(random.randint(100, 500), random.randint(100, 400))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.mouse.wheel(0, random.randint(100, 300))
            await asyncio.sleep(random.uniform(1, 2))

            # Check for CAPTCHA
            page_content = await page.content()
            title = await page.title()

            print(f"Page title: {title}")

            captcha_solved = False  # Track if we needed to solve CAPTCHA

            if "Access to this page has been denied" in page_content or "Press & Hold" in page_content:
                print("[CAPTCHA] Press & Hold detected - attempting to solve...")

                try:
                    # PerimeterX CAPTCHA is often in an iframe - check for it
                    target_frame = page
                    frames = page.frames
                    for frame in frames:
                        frame_content = await frame.content()
                        if "Press & Hold" in frame_content:
                            print(f"  Found CAPTCHA in iframe: {frame.url}")
                            target_frame = frame
                            break

                    # Find the Press & Hold button - look for button-like elements
                    # The button text is exactly "Press & Hold" (not the instructional paragraph)
                    hold_button = None
                    box = None

                    # Try specific selectors first
                    selectors = [
                        'button:has-text("Press & Hold")',
                        '[role="button"]:has-text("Press & Hold")',
                        'a:has-text("Press & Hold")',
                        'div[style*="cursor"]:has-text("Press & Hold")',
                    ]

                    for selector in selectors:
                        try:
                            hold_button = await target_frame.query_selector(selector)
                            if hold_button:
                                box = await hold_button.bounding_box()
                                # Valid button should be in the center area of page (y > 300)
                                if box and box["y"] > 300:
                                    print(f"  Found button with selector: {selector}")
                                    break
                                else:
                                    hold_button = None
                                    box = None
                        except:
                            continue

                    # If no button found, try to find all elements with exact text
                    if not hold_button:
                        elements = await target_frame.query_selector_all('*')
                        for elem in elements:
                            try:
                                text = await elem.text_content()
                                # Look for element with ONLY "Press & Hold" (the button)
                                if text and text.strip() == "Press & Hold":
                                    box = await elem.bounding_box()
                                    if box and box["y"] > 300:  # Must be in center/lower area
                                        hold_button = elem
                                        print("  Found button by exact text match")
                                        break
                            except:
                                continue

                    # Fallback: click center of viewport where button typically appears
                    if not box or box["y"] < 300:
                        print("  Using fallback: clicking visual center of CAPTCHA modal")
                        # Based on 1280x720 viewport, button is around (640, 417)
                        box = {"x": 510, "y": 392, "width": 260, "height": 50}

                    if box:
                        x = box["x"] + box["width"] / 2
                        y = box["y"] + box["height"] / 2

                        print(f"  Target button at ({x:.0f}, {y:.0f})")

                        # Human-like mouse movement pattern before clicking
                        # Start from a random corner
                        start_x = random.randint(100, 300)
                        start_y = random.randint(100, 200)
                        await page.mouse.move(start_x, start_y)
                        await asyncio.sleep(random.uniform(0.2, 0.5))

                        # Move toward button with intermediate points (bezier-like path)
                        mid_x = (start_x + x) / 2 + random.randint(-50, 50)
                        mid_y = (start_y + y) / 2 + random.randint(-30, 30)
                        await page.mouse.move(mid_x, mid_y, steps=random.randint(10, 20))
                        await asyncio.sleep(random.uniform(0.1, 0.3))

                        # Final approach to button with slight overshoot correction
                        await page.mouse.move(x + random.randint(-5, 5), y + random.randint(-3, 3), steps=random.randint(15, 25))
                        await asyncio.sleep(random.uniform(0.3, 0.6))

                        # Settle on exact center
                        await page.mouse.move(x, y, steps=random.randint(3, 6))
                        await asyncio.sleep(random.uniform(0.2, 0.4))

                        print(f"  Clicking at ({x:.0f}, {y:.0f})")

                        # Press and hold for 4-7 seconds (longer hold)
                        hold_duration = random.uniform(4.0, 7.0)
                        print(f"  Pressing and holding for {hold_duration:.1f}s...")
                        await page.mouse.down()
                        await asyncio.sleep(hold_duration)
                        await page.mouse.up()

                        # Wait for page to process
                        print("  Released - waiting for verification...")
                        await asyncio.sleep(3)

                        # Check if CAPTCHA was solved
                        new_content = await page.content()
                        new_title = await page.title()

                        if "Press & Hold" not in new_content and "denied" not in new_title.lower():
                            print("[SUCCESS] CAPTCHA solved!")
                            captcha_solved = True
                        else:
                            print("[FAILED] CAPTCHA still present after attempt")
                    else:
                        print("  Could not determine button position")

                except Exception as e:
                    print(f"  CAPTCHA solve error: {e}")

                if not captcha_solved:
                    result["status"] = "blocked"
                    result["errors"].append({"source": "zillow", "error": "CAPTCHA detected"})
                    print("[BLOCKED] CAPTCHA could not be solved!")

                    # Take screenshot for debugging
                    screenshot_path = image_dir / "captcha_debug.png"
                    await page.screenshot(path=str(screenshot_path))
                    print(f"Debug screenshot saved: {screenshot_path}")
                else:
                    # CAPTCHA solved - continue to extraction
                    page_content = await page.content()  # Refresh content

            # Proceed with extraction if page loaded successfully (or CAPTCHA solved)
            if result["status"] != "blocked" and (captcha_solved or (response and response.status == 200)):
                print("[OK] Page loaded successfully!")
                result["status"] = "success"

                # Take main screenshot
                main_screenshot = image_dir / "listing_main.png"
                await page.screenshot(path=str(main_screenshot), full_page=False)
                result["images"].append(str(main_screenshot))
                print(f"Main screenshot saved: {main_screenshot}")

                # Try to extract listing data
                try:
                    # Price
                    price_elem = await page.query_selector('[data-test="property-card-price"]')
                    if price_elem:
                        result["data"]["price"] = await price_elem.text_content()

                    # Beds/Baths/Sqft
                    beds_elem = await page.query_selector('[data-test="bed-bath-item"]:has-text("bd")')
                    if beds_elem:
                        result["data"]["beds"] = await beds_elem.text_content()

                    baths_elem = await page.query_selector('[data-test="bed-bath-item"]:has-text("ba")')
                    if baths_elem:
                        result["data"]["baths"] = await baths_elem.text_content()

                except Exception as e:
                    result["errors"].append({"source": "data_extraction", "error": str(e)})

                # Try to click through photo gallery
                try:
                    gallery_button = await page.query_selector('[data-test="open-gallery-button"]')
                    if gallery_button:
                        await gallery_button.click()
                        await asyncio.sleep(2)

                        # Capture gallery images
                        for i in range(min(5, 10)):  # Max 5 images
                            img_path = image_dir / f"photo_{i+1:03d}.png"
                            await page.screenshot(path=str(img_path))
                            result["images"].append(str(img_path))
                            print(f"Gallery image {i+1} saved")

                            # Try to go to next image
                            next_btn = await page.query_selector('[aria-label="Next image"]')
                            if next_btn:
                                await next_btn.click()
                                await asyncio.sleep(1)
                            else:
                                break

                except Exception as e:
                    result["errors"].append({"source": "gallery", "error": str(e)})

            else:
                result["status"] = "failed"
                result["errors"].append({
                    "source": "zillow",
                    "error": f"HTTP {response.status if response else 'unknown'}"
                })

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append({"source": "navigation", "error": str(e)})
            print(f"[ERROR] {e}")

        finally:
            await browser.close()

    return result


async def extract_redfin_listing(address: str, proxy: dict = None) -> dict:
    """Extract listing data from Redfin."""

    # Format for Redfin URL
    parts = address.split(",")
    street = parts[0].strip().replace(" ", "-")
    city_state_zip = "-".join([p.strip().replace(" ", "-") for p in parts[1:]])
    url = f"https://www.redfin.com/AZ/Phoenix/{street}-{city_state_zip.split('-')[0]}"

    prop_hash = property_hash(address)
    image_dir = IMAGES_DIR / prop_hash
    image_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "address": address,
        "property_hash": prop_hash,
        "source": "redfin",
        "status": "pending",
        "url": url,
        "data": {},
        "images": [],
        "errors": []
    }

    proxy = proxy or get_random_proxy()
    user_agent = get_random_user_agent()

    print(f"\nTrying Redfin: {url}")
    print(f"Proxy: {proxy['server']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            proxy=proxy,
            user_agent=user_agent,
            viewport={"width": 1280, "height": 720},
        )

        page = await context.new_page()

        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3)

            if response and response.status == 429:
                result["status"] = "rate_limited"
                result["errors"].append({"source": "redfin", "error": "HTTP 429 Rate Limited"})
                print("[BLOCKED] Rate limited!")
            elif response and response.status == 200:
                title = await page.title()
                if "robot" in title.lower() or "blocked" in title.lower():
                    result["status"] = "blocked"
                    result["errors"].append({"source": "redfin", "error": "Bot detection"})
                else:
                    result["status"] = "success"
                    screenshot_path = image_dir / "redfin_main.png"
                    await page.screenshot(path=str(screenshot_path))
                    result["images"].append(str(screenshot_path))
                    print(f"[OK] Redfin screenshot saved: {screenshot_path}")
            else:
                result["status"] = "failed"
                result["errors"].append({"source": "redfin", "error": f"HTTP {response.status if response else 'unknown'}"})

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append({"source": "navigation", "error": str(e)})

        finally:
            await browser.close()

    return result


async def test_proxy(proxy: dict) -> bool:
    """Test if a proxy is working."""
    print(f"Testing proxy: {proxy['server']}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(proxy=proxy)
        page = await context.new_page()

        try:
            # Test with a simple site first
            await page.goto("https://httpbin.org/ip", timeout=15000)
            content = await page.content()
            print(f"  [OK] Proxy working! Response: {content[:100]}")
            await browser.close()
            return True
        except Exception as e:
            print(f"  [FAIL] Proxy failed: {e}")
            await browser.close()
            return False


async def main():
    """Main extraction workflow."""

    # Test addresses (first 5 from test batch)
    test_addresses = [
        "4732 W Davis Rd, Glendale, AZ 85306",
        "2353 W Tierra Buena Ln, Phoenix, AZ 85023",
        "2344 W Marconi Ave, Phoenix, AZ 85023",
        "2846 W Villa Rita Dr, Phoenix, AZ 85053",
        "15225 N 37th Way, Phoenix, AZ 85032",
    ]

    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-proxy":
            # Test all proxies
            print("Testing all proxies...")
            working = []
            for proxy in PROXIES:
                if await test_proxy(proxy):
                    working.append(proxy)
            print(f"\n{len(working)}/{len(PROXIES)} proxies working")
            return
        elif sys.argv[1] == "--address":
            test_addresses = [" ".join(sys.argv[2:])]

    print(f"\nExtracting listings for {len(test_addresses)} properties...")
    print(f"Using {len(PROXIES)} rotating proxies")

    results = []

    for i, address in enumerate(test_addresses):
        print(f"\n[{i+1}/{len(test_addresses)}] Processing: {address}")

        # Try with rotating proxies
        for attempt, proxy in enumerate(random.sample(PROXIES, min(3, len(PROXIES)))):
            result = await extract_zillow_listing(address, proxy)

            if result["status"] == "success":
                results.append(result)
                break
            elif attempt < 2:
                print(f"Retrying with different proxy (attempt {attempt+2}/3)...")
                await asyncio.sleep(2)
        else:
            # All Zillow attempts failed, try Redfin
            result = await extract_redfin_listing(address, get_random_proxy())
            results.append(result)

        # Delay between properties
        if i < len(test_addresses) - 1:
            delay = random.uniform(3, 6)
            print(f"Waiting {delay:.1f}s before next property...")
            await asyncio.sleep(delay)

    # Summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)

    success = sum(1 for r in results if r["status"] == "success")
    blocked = sum(1 for r in results if r["status"] == "blocked")
    failed = sum(1 for r in results if r["status"] == "failed")

    print(f"Total: {len(results)}")
    print(f"Success: {success}")
    print(f"Blocked: {blocked}")
    print(f"Failed: {failed}")

    # Save results
    output_file = DATA_DIR / "extraction_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
