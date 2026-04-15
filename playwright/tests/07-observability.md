# Test 07: Observability Pages

## Precondition
- Logged in

## Steps
1. `browser_navigate` → `/observability`
2. `browser_snapshot` → verify:
   - 4 MetricCards: Avg Latency P50 (245ms, 5.2%), Error Rate (0.12%, 0.0%), Throughput, Active Traces
   - NO "NaN%" in any metric card
   - Request Latency chart with P50/P95/P99 legends
   - Grafana Dashboards section (4 cards)
3. `browser_navigate` → `/observability/traces` — verify Traces page with search and filters
4. `browser_navigate` → `/observability/alerts` — verify Alert Configuration page with:
   - "New Alert" button
   - Table with 5 default alert rules
   - Severity badges, Active/Disabled status
5. `browser_console_messages` level=error → expect 0 errors

## Pass Criteria
- All 3 observability pages render fully (no blank pages)
- Metric percentages show numbers, not NaN
- 0 console errors
