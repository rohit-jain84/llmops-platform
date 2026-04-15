# Test 01: Authentication Flow

## Steps

### Login
1. `browser_navigate` → `http://localhost:3000`
2. Verify redirect to `/login` (snapshot: heading "LLMOps Platform", "Sign in to your account")
3. `browser_fill_form` → Email: `claude-test@llmops.dev`, Password: `TestPass@2026!`
4. `browser_click` → "Sign In" button
5. Verify redirect to `/` and user email in header

### Registration (if account doesn't exist)
1. `browser_navigate` → `http://localhost:3000/login`
2. `browser_click` → "Don't have an account? Register"
3. `browser_fill_form` → Email: `claude-test@llmops.dev`, Password: `TestPass@2026!`
4. `browser_click` → "Register"
5. Verify redirect to `/`

### Logout
1. `browser_click` → logout button (banner button)
2. Verify redirect to `/login`

### Console Check
- `browser_console_messages` level=error → expect 0 errors

## Pass Criteria
- Login redirects to Dashboard
- Logout redirects to /login
- 0 console errors
