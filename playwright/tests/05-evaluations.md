# Test 05: Evaluations Page

## Precondition
- Logged in

## Steps
1. `browser_click` → "Evaluations" sidebar link
2. `browser_snapshot` → verify:
   - heading "Evaluations"
   - Stat cards: Datasets (0), Recent Runs (0), Avg Score (—)
   - "Manage Datasets" button
3. `browser_navigate` → `/evaluations/datasets`
4. `browser_snapshot` → verify "Evaluation Datasets" page with "New Dataset" button
5. `browser_console_messages` level=error → expect 0 errors

## Pass Criteria
- Dashboard and Datasets sub-pages render
- 0 console errors
