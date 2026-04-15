# Playwright E2E Tests

Browser-based end-to-end tests for the LLMOps Platform, executed via the Playwright MCP server in Claude Code.

## Structure

```
playwright/
├── config.js              # Shared config (base URL, credentials, timeouts)
├── README.md              # This file
└── tests/
    ├── 01-auth.md         # Authentication (login, register, logout)
    ├── 02-dashboard.md    # Dashboard page
    ├── 03-prompts.md      # Prompts page
    ├── 04-experiments.md  # Experiments page
    ├── 05-evaluations.md  # Evaluations page
    ├── 06-cost-usage.md   # Cost & Usage page
    ├── 07-observability.md# Observability page
    └── 08-deployments.md  # Deployments page
```

## How to Run

These tests are designed to be executed interactively via Claude Code with the Playwright MCP server.

1. Ensure the app is running at `http://localhost:3000`
2. Ask Claude Code to run a specific test (e.g., "run test 01-auth")
3. Claude will use Playwright MCP tools to navigate, interact, and verify

## Test Account

- **Email:** claude-test@llmops.dev
- **Password:** TestPass@2026!
