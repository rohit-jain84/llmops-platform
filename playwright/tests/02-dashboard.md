# Test 02: Dashboard

## Precondition
- Logged in (run Test 01 first)

## Steps
1. `browser_navigate` → `http://localhost:3000/`
2. `browser_console_messages` level=error → expect 0 errors
3. `browser_snapshot` → verify:
   - heading "Dashboard"
   - 4 MetricCards: Total Requests, Total Cost ($0.00), Cache Hit Rate (0.0%), Active Experiments
   - "Request Volume & Cost" chart with Requests/Cost legends
   - Token Usage section with Input/Output/Total Tokens

## Pass Criteria
- Page renders fully with all widgets
- 0 console errors (cost/analytics API returns 200)
- No NaN or undefined values
