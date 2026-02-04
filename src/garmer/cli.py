"""Command-line interface for Garmer."""

import argparse
import getpass
import json
import logging
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from garmer.auth import AuthenticationError
from garmer.client import GarminClient
from garmer.config import load_config

logger = logging.getLogger(__name__)


def _get_package_root() -> Path | None:
    """Get the root directory of the garmer package (where .git lives)."""
    # First, try walking up from this file's location (works for editable installs)
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Walk up at most 5 levels
        if (current / ".git").exists():
            return current
        current = current.parent

    # Check common source locations
    common_locations = [
        Path.home() / ".openclaw" / "skills" / "garmer",
        Path.home() / "Desktop" / "code" / "garmer",
        Path.home() / "code" / "garmer",
        Path.home() / "projects" / "garmer",
    ]

    for location in common_locations:
        if (location / ".git").exists():
            return location

    # Try to find from pip's direct_url.json (for editable installs)
    try:
        import importlib.metadata

        dist = importlib.metadata.distribution("garmer")
        direct_url_file = dist._path.parent / "direct_url.json"  # type: ignore
        if direct_url_file.exists():
            import json

            with open(direct_url_file) as f:
                data = json.load(f)
                if "url" in data and data["url"].startswith("file://"):
                    source_path = Path(data["url"].replace("file://", ""))
                    if (source_path / ".git").exists():
                        return source_path
    except Exception:
        pass

    return None


def setup_logging(verbose: bool = False) -> None:
    """Set up logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def cmd_login(args: argparse.Namespace) -> int:
    """Handle login command."""
    email = args.email or input("Garmin Connect email: ")
    password = args.password or getpass.getpass("Garmin Connect password: ")

    try:
        client = GarminClient.from_credentials(
            email=email,
            password=password,
            save_tokens=True,
        )
        print("Successfully logged in and saved authentication tokens.")
        return 0
    except AuthenticationError as e:
        print(f"Login failed: {e}", file=sys.stderr)
        return 1


def cmd_logout(args: argparse.Namespace) -> int:
    """Handle logout command."""
    config = load_config()
    token_path = config.token_dir / config.token_file

    if token_path.exists():
        token_path.unlink()
        print("Logged out and deleted saved tokens.")
    else:
        print("No saved tokens found.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Handle status command."""
    try:
        client = GarminClient.from_saved_tokens()
        profile = client.get_user_profile()
        if profile:
            print(f"Logged in as: {profile.display_name or profile.email}")
            print(f"User ID: {profile.profile_id}")
        else:
            print("Authenticated but could not retrieve profile.")
        return 0
    except AuthenticationError:
        print("Not logged in. Use 'garmer login' to authenticate.")
        return 1


def cmd_summary(args: argparse.Namespace) -> int:
    """Handle summary command."""
    try:
        client = GarminClient.from_saved_tokens()
    except AuthenticationError:
        print("Not logged in. Use 'garmer login' first.", file=sys.stderr)
        return 1

    target_date = args.date or date.today()
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    summary = client.get_daily_summary(target_date)
    if summary:
        print(f"\n=== Daily Summary for {target_date} ===\n")
        print(f"Steps: {summary.total_steps:,} / {summary.daily_step_goal:,}")
        print(f"Distance: {summary.total_distance_meters / 1000:.2f} km")
        print(
            f"Calories: {summary.total_kilocalories:,} (Active: {summary.active_kilocalories:,})"
        )
        print(f"Floors: {summary.floors_ascended:.0f}")

        if summary.resting_heart_rate:
            print(f"Resting HR: {summary.resting_heart_rate} bpm")

        if summary.avg_stress_level:
            print(f"Avg Stress: {summary.avg_stress_level}")

        if summary.body_battery_most_recent_value:
            print(f"Body Battery: {summary.body_battery_most_recent_value}")

        print(
            f"\nIntensity Minutes: {summary.moderate_intensity_minutes} moderate + "
            f"{summary.vigorous_intensity_minutes} vigorous"
        )
    else:
        print(f"No data available for {target_date}")

    return 0


def cmd_sleep(args: argparse.Namespace) -> int:
    """Handle sleep command."""
    try:
        client = GarminClient.from_saved_tokens()
    except AuthenticationError:
        print("Not logged in. Use 'garmer login' first.", file=sys.stderr)
        return 1

    target_date = args.date or date.today()
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    sleep = client.get_sleep(target_date)
    if sleep:
        print(f"\n=== Sleep Data for night ending {target_date} ===\n")
        print(f"Total Sleep: {sleep.total_sleep_hours:.1f} hours")
        print(
            f"Deep Sleep: {sleep.deep_sleep_hours:.1f} hours ({sleep.deep_sleep_percentage:.1f}%)"
        )
        print(f"Light Sleep: {sleep.light_sleep_hours:.1f} hours")
        print(
            f"REM Sleep: {sleep.rem_sleep_hours:.1f} hours ({sleep.rem_sleep_percentage:.1f}%)"
        )

        if sleep.overall_score:
            print(f"\nSleep Score: {sleep.overall_score}")

        if sleep.avg_sleep_heart_rate:
            print(f"Avg HR: {sleep.avg_sleep_heart_rate} bpm")

        if sleep.avg_hrv:
            print(f"Avg HRV: {sleep.avg_hrv:.1f} ms")

        efficiency = sleep.sleep_efficiency
        if efficiency:
            print(f"Sleep Efficiency: {efficiency:.1f}%")
    else:
        print(f"No sleep data available for {target_date}")

    return 0


def cmd_activities(args: argparse.Namespace) -> int:
    """Handle activities command."""
    try:
        client = GarminClient.from_saved_tokens()
    except AuthenticationError:
        print("Not logged in. Use 'garmer login' first.", file=sys.stderr)
        return 1

    activities = client.get_recent_activities(limit=args.limit)
    if activities:
        print(f"\n=== Recent Activities ({len(activities)}) ===\n")
        for activity in activities:
            print(f"[{activity.activity_type_key}] {activity.activity_name}")
            print(f"  Date: {activity.start_time}")
            print(f"  Duration: {activity.duration_minutes:.1f} min")
            if activity.distance_meters > 0:
                print(f"  Distance: {activity.distance_km:.2f} km")
            print(f"  Calories: {activity.calories:.0f}")
            if activity.avg_heart_rate:
                print(f"  Avg HR: {activity.avg_heart_rate} bpm")
            print()
    else:
        print("No recent activities found.")

    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Handle health snapshot command."""
    try:
        client = GarminClient.from_saved_tokens()
    except AuthenticationError:
        print("Not logged in. Use 'garmer login' first.", file=sys.stderr)
        return 1

    target_date = args.date or date.today()
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    snapshot = client.get_health_snapshot(target_date)

    if args.json:
        print(json.dumps(snapshot, indent=2, default=str))
    else:
        print(f"\n=== Health Snapshot for {target_date} ===\n")

        if snapshot.get("steps"):
            steps = snapshot["steps"]
            print(f"Steps: {steps['total']:,} / {steps['goal']:,}")

        if snapshot.get("sleep"):
            sleep = snapshot["sleep"]
            print(f"Sleep Score: {sleep.get('overall_score', 'N/A')}")

        if snapshot.get("heart_rate"):
            hr = snapshot["heart_rate"]
            print(f"Resting HR: {hr.get('resting', 'N/A')} bpm")

        if snapshot.get("stress"):
            stress = snapshot["stress"]
            print(f"Avg Stress: {stress.get('avg_level', 'N/A')}")

        if snapshot.get("hydration"):
            hydration = snapshot["hydration"]
            print(f"Hydration: {hydration.get('goal_percentage', 0):.0f}% of goal")

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Handle export command."""
    try:
        client = GarminClient.from_saved_tokens()
    except AuthenticationError:
        print("Not logged in. Use 'garmer login' first.", file=sys.stderr)
        return 1

    end_date = args.end_date or date.today()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    start_date = args.start_date
    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = end_date - timedelta(days=args.days - 1)

    print(f"Exporting data from {start_date} to {end_date}...")

    data = client.export_data(
        start_date=start_date,
        end_date=end_date,
        include_activities=True,
        include_sleep=True,
        include_daily=True,
    )

    output_path = (
        Path(args.output)
        if args.output
        else Path(f"garmin_export_{start_date}_{end_date}.json")
    )

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Exported data to {output_path}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    """Handle update command - pull latest changes from git."""
    package_root = _get_package_root()

    if not package_root:
        print("Could not find garmer package root directory.", file=sys.stderr)
        print("Make sure garmer is installed from a git repository.", file=sys.stderr)
        return 1

    print(f"Updating garmer from {package_root}...")

    try:
        # Fetch first to see what's available
        subprocess.run(
            ["git", "fetch"],
            cwd=package_root,
            check=True,
            capture_output=True,
        )

        # Check if there are updates
        result = subprocess.run(
            ["git", "status", "-uno"],
            cwd=package_root,
            check=True,
            capture_output=True,
            text=True,
        )

        if "Your branch is up to date" in result.stdout:
            print("Already up to date.")
            return 0

        # Show what will change
        log_result = subprocess.run(
            ["git", "log", "--oneline", "HEAD..@{u}"],
            cwd=package_root,
            capture_output=True,
            text=True,
        )
        if log_result.stdout.strip():
            print("\nIncoming changes:")
            print(log_result.stdout)

        # Pull the changes
        pull_result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=package_root,
            check=True,
            capture_output=True,
            text=True,
        )

        print(pull_result.stdout)
        print(
            "Update complete! Changes will take effect immediately (editable install)."
        )
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Git error: {e.stderr if e.stderr else e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("Git is not installed or not in PATH.", file=sys.stderr)
        return 1


def cmd_version(args: argparse.Namespace) -> int:
    """Handle version command."""
    from garmer import __version__

    print(f"garmer {__version__}")

    package_root = _get_package_root()
    if package_root:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=package_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"git: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="garmer",
        description="Garmin data extraction tool for MoltBot integration",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Login to Garmin Connect")
    login_parser.add_argument("-e", "--email", help="Garmin Connect email")
    login_parser.add_argument("-p", "--password", help="Garmin Connect password")

    # Logout command
    subparsers.add_parser("logout", help="Logout and delete saved tokens")

    # Status command
    subparsers.add_parser("status", help="Show authentication status")

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show daily summary")
    summary_parser.add_argument("-d", "--date", help="Date (YYYY-MM-DD)")

    # Sleep command
    sleep_parser = subparsers.add_parser("sleep", help="Show sleep data")
    sleep_parser.add_argument("-d", "--date", help="Date (YYYY-MM-DD)")

    # Activities command
    activities_parser = subparsers.add_parser(
        "activities", help="List recent activities"
    )
    activities_parser.add_argument(
        "-n", "--limit", type=int, default=10, help="Number of activities"
    )

    # Snapshot command
    snapshot_parser = subparsers.add_parser("snapshot", help="Get health snapshot")
    snapshot_parser.add_argument("-d", "--date", help="Date (YYYY-MM-DD)")
    snapshot_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to file")
    export_parser.add_argument("-s", "--start-date", help="Start date (YYYY-MM-DD)")
    export_parser.add_argument("-e", "--end-date", help="End date (YYYY-MM-DD)")
    export_parser.add_argument(
        "-n", "--days", type=int, default=7, help="Number of days (if no start date)"
    )
    export_parser.add_argument("-o", "--output", help="Output file path")

    # Update command
    subparsers.add_parser("update", help="Update garmer to latest version (git pull)")

    # Version command
    subparsers.add_parser("version", help="Show version information")

    return parser


def main() -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "login": cmd_login,
        "logout": cmd_logout,
        "status": cmd_status,
        "summary": cmd_summary,
        "sleep": cmd_sleep,
        "activities": cmd_activities,
        "snapshot": cmd_snapshot,
        "export": cmd_export,
        "update": cmd_update,
        "version": cmd_version,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
