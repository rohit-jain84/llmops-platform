// Playwright E2E Test Configuration
// These values are used across all test scripts

export const config = {
  baseUrl: 'http://localhost:3000',
  credentials: {
    email: 'claude-test@llmops.dev',
    password: 'TestPass@2026!',
  },
  timeouts: {
    navigation: 10000,
    action: 5000,
  },
};
