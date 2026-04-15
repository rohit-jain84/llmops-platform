# Test 03: Prompts Page

## Precondition
- Logged in

## Steps
1. `browser_click` → "Prompts" sidebar link
2. `browser_snapshot` → verify empty state with "No prompts yet"
3. `browser_click` → "New Prompt" button
4. `browser_snapshot` → verify "Create Prompt Template" card appears with:
   - Application ID input
   - Name input
   - Description input
   - Create (disabled) and Cancel buttons
5. `browser_click` → "Cancel" to dismiss
6. `browser_console_messages` level=error → expect 0 errors

## Pass Criteria
- Empty state renders correctly
- "New Prompt" button opens create form (not a no-op)
- Cancel dismisses the form
- 0 console errors
