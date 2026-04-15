# Test 04: Experiments Page

## Precondition
- Logged in

## Steps
1. `browser_click` → "Experiments" sidebar link
2. `browser_snapshot` → verify:
   - heading "Experiments"
   - Filter buttons: All, draft, running, stopped, completed
   - Empty state "No experiments"
3. `browser_click` → "New Experiment"
4. Verify navigation to `/experiments/new` with form:
   - Experiment Name, Application ID
   - Variants section (Control 50%, Variant B 50%)
   - Create Experiment button (disabled until filled)
5. `browser_console_messages` level=error → expect 0 errors

## Pass Criteria
- List page renders with filters
- New Experiment navigates to create form
- 0 console errors
