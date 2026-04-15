# Test 06: Cost & Usage Pages

## Precondition
- Logged in

## Steps
1. `browser_navigate` → `/cost` — verify Cost Analytics with 4 metric cards and charts
2. `browser_console_messages` level=error → expect 0 errors (no chart key warnings)
3. `browser_navigate` → `/cost/analytics` — verify Token Analytics with tabs (By Time/Model/App)
4. `browser_navigate` → `/cost/routing` — verify Routing Rules with "New Rule" button
5. `browser_navigate` → `/cost/alerts` — verify Budget Alerts with "New Alert" button
6. `browser_navigate` → `/cost/forecast` — verify Cost Forecast with projections chart

## Pass Criteria
- All 5 cost sub-pages render without errors
- No "key prop" React warnings in console
- Charts display correctly with proper legends
