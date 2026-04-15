# Test 08: Deployments Page

## Precondition
- Logged in

## Steps
1. `browser_click` → "Deployments" sidebar link
2. `browser_snapshot` → verify:
   - heading "Deployments"
   - Empty state "No deployments yet"
3. `browser_console_messages` level=error → expect 0 errors

## Pass Criteria
- Page renders with empty state
- 0 console errors
