---
name: garmer
description: Extract health and fitness data from Garmin Connect including activities, sleep, heart rate, stress, steps, and body composition. Use when the user asks about their Garmin data, fitness metrics, sleep analysis, or health insights.
license: MIT
compatibility: Requires Python 3.10+, pip/uv for installation. Requires Garmin Connect account credentials for authentication.
metadata:
  author: MoltBot Team
  version: "0.1.0"
  moltbot:
    emoji: "⌚"
    primaryEnv: "GARMER_TOKEN_DIR"
    requires:
      bins:
        - garmer
    install:
      - id: uv
        kind: uv
        package: garmer
        bins:
          - garmer
        label: Install garmer (uv)
      - id: pip
        kind: pip
        package: garmer
        bins:
          - garmer
        label: Install garmer (pip)
---

# Garmer - Garmin Data Extraction Skill

This skill enables extraction of health and fitness data from Garmin Connect for analysis and insights.

## Prerequisites

1. A Garmin Connect account with health data
2. The `garmer` CLI tool installed (see installation options in metadata)

## Authentication (One-Time Setup)

Before using garmer, authenticate with Garmin Connect:

```bash
garmer login
```

This will prompt for your Garmin Connect email and password. Tokens are saved to `~/.garmer/garmin_tokens` for future use.

To check authentication status:

```bash
garmer status
```

## Available Commands

### Daily Summary

Get today's health summary (steps, calories, heart rate, stress):

```bash
garmer summary
# Or for a specific date:
garmer summary --date 2024-01-15
```

### Sleep Data

Get sleep analysis (duration, phases, score, HRV):

```bash
garmer sleep
# Or for a specific date:
garmer sleep --date 2024-01-15
```

### Activities

List recent fitness activities:

```bash
garmer activities
# Limit number of results:
garmer activities --limit 5
```

### Health Snapshot

Get comprehensive health data for a day:

```bash
garmer snapshot
# As JSON for programmatic use:
garmer snapshot --json
```

### Export Data

Export multiple days of data to JSON:

```bash
# Last 7 days (default)
garmer export

# Custom date range
garmer export --start-date 2024-01-01 --end-date 2024-01-31 --output my_data.json

# Last N days
garmer export --days 14
```

## Python API Usage

For more complex data processing, use the Python API:

```python
from garmer import GarminClient

# Use saved tokens
client = GarminClient.from_saved_tokens()

# Get daily summary
summary = client.get_daily_summary()
print(f"Steps: {summary.total_steps}")

# Get sleep data
sleep = client.get_sleep()
print(f"Sleep: {sleep.total_sleep_hours:.1f} hours")

# Get recent activities
activities = client.get_recent_activities(limit=5)
for activity in activities:
    print(f"{activity.activity_name}: {activity.distance_km:.1f} km")

# Get comprehensive health snapshot
snapshot = client.get_health_snapshot()
```

## Common Workflows

### Health Check Query

When a user asks "How did I sleep?" or "What's my health summary?":

```bash
garmer snapshot --json
```

### Activity Analysis

When a user asks about workouts or exercise:

```bash
garmer activities --limit 10
```

### Trend Analysis

When analyzing health trends over time:

```bash
garmer export --days 30 --output health_data.json
```

Then process the JSON file with Python for analysis.

## Data Types Available

- **Activities**: Running, cycling, swimming, strength training, etc.
- **Sleep**: Duration, phases (deep, light, REM), score, HRV
- **Heart Rate**: Resting HR, samples, zones
- **Stress**: Stress levels, body battery
- **Steps**: Total steps, distance, floors
- **Body Composition**: Weight, body fat, muscle mass
- **Hydration**: Water intake tracking
- **Respiration**: Breathing rate data

## Error Handling

If not authenticated:

```
Not logged in. Use 'garmer login' first.
```

If session expired, re-authenticate:

```bash
garmer login
```

## Environment Variables

- `GARMER_TOKEN_DIR`: Custom directory for token storage
- `GARMER_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `GARMER_CACHE_ENABLED`: Enable/disable data caching (true/false)

## References

For detailed API documentation and MoltBot integration examples, see `references/REFERENCE.md`.
