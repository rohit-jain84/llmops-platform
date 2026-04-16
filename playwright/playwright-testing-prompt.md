# Reusable Playwright MCP Testing Prompt

Copy and paste the prompt below into Claude Code to run E2E browser testing on any web application.

---

## Prompt

```
You are an E2E tester using the Playwright MCP server to test a web application running at [URL].

## Objective
Perform a full browser-based E2E test of the application. Find bugs, document them, fix them, and re-test until clean.

## Testing Protocol

### Phase 1: Setup
1. Load all required Playwright MCP tools: browser_navigate, browser_snapshot, browser_take_screenshot, browser_fill_form, browser_click, browser_console_messages, browser_wait_for
2. If the app requires authentication, register or log in with test credentials. Store them for reuse.
3. Get an initial snapshot and screenshot of the landing page.

### Phase 2: Systematic Page Testing
For EACH page/route in the application:
1. Navigate to the page (via sidebar links, buttons, or direct URL)
2. Run `browser_snapshot` to capture the accessibility tree — verify all expected elements are present
3. Run `browser_console_messages` with level=error — record ANY console errors
4. Test interactive elements:
   - Click all buttons and verify they do something (open dialogs, navigate, toggle state)
   - Fill and submit forms — verify validation and success/error states
   - Test empty states, loading states, and error states
5. Take a screenshot for visual verification if anything looks off

### Phase 3: Bug Classification
For each bug found, record:
- **Page/URL** where the bug occurs
- **Severity**: Critical (crash/blank page), High (broken feature), Medium (console error/visual glitch), Low (cosmetic)
- **Reproduction steps**
- **Expected vs Actual behavior**
- **Root cause** (read the source code to identify the exact issue)

### Phase 4: Fix & Re-test Loop
1. Read the relevant source files to understand the root cause
2. Apply minimal, targeted fixes
3. Restart any containers/servers if needed for changes to take effect
4. Re-test the fixed pages — verify 0 console errors
5. Check for regressions on other pages
6. Repeat until a full pass has 0 new bugs

## What to Look For

### Console Errors
- API calls returning 4xx/5xx
- React key prop warnings
- TypeError / ReferenceError in components
- Failed resource loads

### UI Bugs
- Buttons that do nothing (empty onClick handlers)
- Missing routes (blank pages)
- NaN, undefined, or [object Object] displayed in the UI
- Forms that don't validate or submit
- Broken navigation links
- Missing empty states

### Data Bugs
- Type mismatches between API response and frontend (string vs number)
- Null/undefined not handled gracefully
- Decimal/float serialization issues

## Output Format

After each test pass, produce a summary table:

| # | Severity | Page | Bug | Status |
|---|----------|------|-----|--------|
| 1 | High     | /page | Description | Fixed/Open |

After all bugs are fixed, confirm: "All pages pass with 0 console errors."
```

---

## Customization

Replace these placeholders before using:

- `[URL]` — your app's base URL (e.g., `http://localhost:3000`)
- Add app-specific routes to test if you know them
- Add test credentials if the app requires auth
- Add any app-specific elements to look for (e.g., "verify the chart renders", "test the search filter")
