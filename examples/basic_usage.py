#!/usr/bin/env python3
"""
Basic usage examples for Garmer - Garmin data extraction tool.

This script demonstrates how to use Garmer to extract various health
and fitness data from Garmin Connect.
"""

from datetime import date, timedelta

from garmer import GarminClient


def main():
    """Demonstrate basic Garmer usage."""

    # =========================================================================
    # Authentication
    # =========================================================================

    # Option 1: Login with credentials (tokens are saved automatically)
    # client = GarminClient.from_credentials(
    #     email="your-email@example.com",
    #     password="your-password",
    # )

    # Option 2: Use previously saved tokens
    client = GarminClient.from_saved_tokens()

    # =========================================================================
    # User Profile
    # =========================================================================

    print("=== User Profile ===")
    profile = client.get_user_profile()
    if profile:
        print(f"Name: {profile.display_name}")
        print(f"Email: {profile.email}")
        if profile.height_cm:
            print(f"Height: {profile.height_cm} cm")
        if profile.weight_kg:
            print(f"Weight: {profile.weight_kg} kg")

    # =========================================================================
    # Today's Summary
    # =========================================================================

    print("\n=== Today's Summary ===")
    summary = client.get_daily_summary()
    if summary:
        print(f"Steps: {summary.total_steps:,} / {summary.daily_step_goal:,}")
        print(f"Calories: {summary.total_kilocalories:,}")
        print(f"Distance: {summary.total_distance_meters / 1000:.2f} km")
        print(f"Floors: {summary.floors_ascended}")
        if summary.resting_heart_rate:
            print(f"Resting HR: {summary.resting_heart_rate} bpm")

    # =========================================================================
    # Last Night's Sleep
    # =========================================================================

    print("\n=== Last Night's Sleep ===")
    sleep = client.get_sleep()
    if sleep:
        print(f"Total Sleep: {sleep.total_sleep_hours:.1f} hours")
        print(f"Deep Sleep: {sleep.deep_sleep_hours:.1f} hours")
        print(f"REM Sleep: {sleep.rem_sleep_hours:.1f} hours")
        if sleep.overall_score:
            print(f"Sleep Score: {sleep.overall_score}")
        if sleep.avg_sleep_heart_rate:
            print(f"Avg HR during sleep: {sleep.avg_sleep_heart_rate} bpm")

    # =========================================================================
    # Today's Stress
    # =========================================================================

    print("\n=== Today's Stress ===")
    stress = client.get_stress()
    if stress:
        if stress.avg_stress_level:
            print(f"Average Stress: {stress.avg_stress_level}")
        print(f"Rest Time: {stress.rest_duration_hours:.1f} hours")
        print(f"High Stress Time: {stress.high_stress_hours:.1f} hours")

    # =========================================================================
    # Recent Activities
    # =========================================================================

    print("\n=== Recent Activities ===")
    activities = client.get_recent_activities(limit=5)
    for activity in activities:
        print(f"- [{activity.activity_type_key}] {activity.activity_name}")
        print(f"  Duration: {activity.duration_minutes:.1f} min")
        if activity.distance_km > 0:
            print(f"  Distance: {activity.distance_km:.2f} km")
        print(f"  Calories: {activity.calories:.0f}")

    # =========================================================================
    # Heart Rate
    # =========================================================================

    print("\n=== Heart Rate ===")
    hr = client.get_heart_rate()
    if hr:
        if hr.resting_heart_rate:
            print(f"Resting HR: {hr.resting_heart_rate} bpm")
        if hr.max_heart_rate:
            print(f"Max HR: {hr.max_heart_rate} bpm")
        if hr.min_heart_rate:
            print(f"Min HR: {hr.min_heart_rate} bpm")

    # =========================================================================
    # Hydration
    # =========================================================================

    print("\n=== Hydration ===")
    hydration = client.get_hydration()
    if hydration:
        print(f"Water Intake: {hydration.total_intake_ml} ml")
        print(f"Goal: {hydration.goal_ml} ml ({hydration.goal_percentage:.0f}%)")

    # =========================================================================
    # Weight
    # =========================================================================

    print("\n=== Weight ===")
    weight = client.get_latest_weight()
    if weight:
        print(f"Latest Weight: {weight.weight_kg:.1f} kg ({weight.weight_lbs:.1f} lbs)")

    # =========================================================================
    # Health Snapshot (All Data at Once)
    # =========================================================================

    print("\n=== Health Snapshot ===")
    snapshot = client.get_health_snapshot()
    print(f"Date: {snapshot['date']}")

    if snapshot.get("steps"):
        steps = snapshot["steps"]
        print(f"Steps: {steps['total']:,} (Goal reached: {steps['goal_reached']})")

    if snapshot.get("sleep"):
        sleep_data = snapshot["sleep"]
        print(f"Sleep Duration: {sleep_data.get('total_sleep_seconds', 0) / 3600:.1f} hours")

    # =========================================================================
    # Weekly Report
    # =========================================================================

    print("\n=== Weekly Health Report ===")
    report = client.get_weekly_health_report()
    print(f"Period: {report['period']['start']} to {report['period']['end']}")

    if report.get("activities"):
        act = report["activities"]
        print(f"Activities: {act['count']} workouts")
        print(f"Total Duration: {act['total_duration_hours']:.1f} hours")
        print(f"Total Distance: {act['total_distance_km']:.1f} km")

    if report.get("steps"):
        steps = report["steps"]
        print(f"Avg Daily Steps: {steps['avg_daily']:.0f}")
        print(f"Days Goal Reached: {steps['days_goal_reached']}/7")

    if report.get("sleep"):
        sleep = report["sleep"]
        print(f"Avg Sleep: {sleep['avg_hours']:.1f} hours")

    # =========================================================================
    # Export Data
    # =========================================================================

    print("\n=== Data Export ===")
    end_date = date.today()
    start_date = end_date - timedelta(days=6)

    export = client.export_data(
        start_date=start_date,
        end_date=end_date,
        include_activities=True,
        include_sleep=True,
        include_daily=True,
    )

    print(f"Exported {len(export.get('activities', []))} activities")
    print(f"Exported {len(export.get('sleep', []))} sleep records")
    print(f"Exported {len(export.get('daily_summaries', []))} daily summaries")


if __name__ == "__main__":
    main()
