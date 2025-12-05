# MCP Commands Reference

Quick reference for Model Context Protocol (MCP) commands.

---

## Context7 - Library Documentation

Context7 provides up-to-date documentation and code examples for any library.

### Commands

```python
mcp__context7__resolve-library-id(libraryName)     # Find library ID by name
mcp__context7__get-library-docs(                   # Fetch documentation
    context7CompatibleLibraryID,                   # Required: "/org/project" format
    topic="hooks",                                 # Optional: focus area
    mode="code",                                   # "code" (default) or "info"
    page=1                                         # Pagination (1-10)
)
```

### Workflow

**Step 1: Resolve library ID (REQUIRED unless user provides ID)**
```python
mcp__context7__resolve-library-id(libraryName="pydantic")
# Returns: /pydantic/pydantic
```

**Step 2: Fetch documentation**
```python
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/pydantic/pydantic",
    topic="validators",
    mode="code"
)
```

### Mode Selection

| Mode | Use For |
|------|---------|
| `code` | API references, code examples, implementation patterns |
| `info` | Conceptual guides, architecture, narrative explanations |

### Examples

```python
# Python libraries
mcp__context7__resolve-library-id(libraryName="fastapi")
mcp__context7__get-library-docs(context7CompatibleLibraryID="/fastapi/fastapi", topic="dependencies")

# JavaScript/TypeScript
mcp__context7__resolve-library-id(libraryName="react")
mcp__context7__get-library-docs(context7CompatibleLibraryID="/facebook/react", topic="hooks", mode="code")

# Database
mcp__context7__resolve-library-id(libraryName="sqlalchemy")
mcp__context7__get-library-docs(context7CompatibleLibraryID="/sqlalchemy/sqlalchemy", topic="async")
```

### Best Practices

1. **Always resolve first** - Call `resolve-library-id` before `get-library-docs` unless user provides exact ID
2. **Use specific topics** - Narrow results with `topic` parameter (e.g., "routing", "middleware", "validation")
3. **Paginate for more** - If context insufficient, try `page=2`, `page=3`, etc.
4. **Choose mode wisely** - Use `code` for implementation, `info` for understanding concepts

---

## Fetch - Web Content Retrieval

```python
mcp__fetch__fetch(
    url,                    # Required: URL to fetch
    max_length=5000,        # Max characters (default: 5000, max: 1000000)
    start_index=0,          # Character offset for pagination
    raw=False               # True for raw HTML, False for markdown
)
```

---

## Playwright - Browser Automation

### Browser Navigation

```python
mcp__playwright__browser_navigate(url)              # Navigate to URL
mcp__playwright__browser_navigate_back()            # Go back
mcp__playwright__browser_close()                    # Close browser
mcp__playwright__browser_resize(width, height)      # Resize window
```

### Page Interaction

```python
mcp__playwright__browser_click(element, ref)                     # Click element
mcp__playwright__browser_type(element, ref, text)                # Type in input
mcp__playwright__browser_press_key(key)                          # Press keyboard key
mcp__playwright__browser_hover(element, ref)                     # Hover over element
mcp__playwright__browser_select_option(element, ref, values)     # Select dropdown
mcp__playwright__browser_drag(startElement, startRef, endElement, endRef)  # Drag and drop
```

### Page State Inspection

```python
mcp__playwright__browser_snapshot()                  # Get accessibility tree (PREFERRED)
mcp__playwright__browser_take_screenshot()           # Visual screenshot
mcp__playwright__browser_console_messages()          # Get console logs
mcp__playwright__browser_network_requests()          # Get network activity
```

**Note:** Use `browser_snapshot()` for actions, not screenshots. Screenshots are for visual inspection only.

### Tab Management

```python
mcp__playwright__browser_tabs(action="list")         # List all tabs
mcp__playwright__browser_tabs(action="new")          # Open new tab
mcp__playwright__browser_tabs(action="select", index=N)  # Switch to tab N
mcp__playwright__browser_tabs(action="close")        # Close current tab
```

### Forms and Input

```python
mcp__playwright__browser_fill_form(fields)           # Fill multiple form fields
mcp__playwright__browser_file_upload(paths)          # Upload files
```

**Form fields format:**
```python
fields = [
    {"name": "Username", "type": "textbox", "ref": "ref123", "value": "user@example.com"},
    {"name": "Remember Me", "type": "checkbox", "ref": "ref456", "value": "true"},
    {"name": "Country", "type": "combobox", "ref": "ref789", "value": "United States"}
]
```

### Waiting and Timing

```python
mcp__playwright__browser_wait_for(time=N)            # Wait N seconds
mcp__playwright__browser_wait_for(text="...")        # Wait for text to appear
mcp__playwright__browser_wait_for(textGone="...")    # Wait for text to disappear
```

### Advanced

```python
mcp__playwright__browser_evaluate(function)          # Run JavaScript
mcp__playwright__browser_run_code(code)              # Run Playwright code snippet
mcp__playwright__browser_handle_dialog(accept, promptText)  # Handle alerts/prompts
```

**Example JavaScript evaluation:**
```python
# Get page title
mcp__playwright__browser_evaluate(function="() => { return document.title; }")

# Click element by selector
mcp__playwright__browser_run_code(code="await page.locator('#submit-btn').click();")
```

### Installation

If you get an error about browser not being installed:
```python
mcp__playwright__browser_install()
```

### MCP Configuration

**Location:** `.mcp.json` - MCP server must be restarted after config changes.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "cmd",
      "args": ["/c", "npx", "@playwright/mcp@latest", "--headless", "--viewport-size=1280x720"]
    }
  }
}
```

**Note:** Stealth browsers (nodriver, curl_cffi) used instead for Zillow/Redfin PerimeterX bypass.

### Browser URL Patterns

#### Maricopa County Assessor
```
# Search by address
https://mcassessor.maricopa.gov/mcs/?q={address}

# Property details by APN
https://mcassessor.maricopa.gov/mcs/?q={apn}&mod=pd

# Building sketch
https://mcassessor.maricopa.gov/sketch/{apn}/view/1/

# Maps (GIS)
http://maps.mcassessor.maricopa.gov/?esearch={apn}&slayer=0&exprnum=0
```

#### Google Maps
```
https://www.google.com/maps/search/{address}
https://www.google.com/maps/@{lat},{lng},20z/data=!3m1!1e3  # Satellite
```

#### GreatSchools
```
https://www.greatschools.org/search/search.page?q={address}
```

### Best Practices

1. Use `browser_snapshot()` before interactions (get element refs from accessibility tree)
2. Use `browser_wait_for()` for dynamic content
3. Take screenshots for debugging
4. Handle errors gracefully (listing sites may block/rate-limit)
5. Add human-like delays: `wait_for(time=2)` between actions
6. Prefer Maricopa County Assessor (unblocked, official data)
