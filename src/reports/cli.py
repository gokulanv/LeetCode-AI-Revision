import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from .generator import generate_daily_report
from .config import ReportConfig


def main():
    """Main CLI entry point for report generation."""
    parser = argparse.ArgumentParser(
        description="Generate LeetCode daily reports with AI analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate yesterday's report
  python -m src.reports.cli generate --username gokulanv

  # Generate report for specific date
  python -m src.reports.cli generate --username gokulanv --date 2025-12-28

  # Skip AI analysis (faster)
  python -m src.reports.cli generate --username gokulanv --no-analyze

  # Custom output directory
  python -m src.reports.cli generate --username gokulanv --output-dir ./my-reports

  # Don't auto-open in browser
  python -m src.reports.cli generate --username gokulanv --no-open
        """
    )

    parser.add_argument(
        "command",
        choices=["generate"],
        help="Command to execute"
    )

    parser.add_argument(
        "--username",
        required=True,
        help="LeetCode username"
    )

    parser.add_argument(
        "--date",
        help="Date for report in YYYY-MM-DD format (default: yesterday)"
    )

    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Skip OpenAI analysis (faster generation)"
    )

    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't auto-open report in browser"
    )

    parser.add_argument(
        "--output-dir",
        help="Override output directory (default: ~/LeetCode-Reports)"
    )

    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(_run_generate(args))


async def _run_generate(args):
    """Run the generate command."""
    try:
        # Parse date if provided
        target_date = None
        if args.date:
            try:
                target_date = datetime.strptime(args.date, "%Y-%m-%d")
            except ValueError:
                print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
                sys.exit(1)

        # Build configuration
        config = ReportConfig.from_env()

        # Override with CLI arguments
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.no_analyze:
            config.analyze_submissions = False
        if args.no_open:
            config.auto_open_browser = False

        # Generate report
        print("=" * 60)
        print("LeetCode Daily Report Generator")
        print("=" * 60)

        report_path = await generate_daily_report(
            username=args.username,
            date=target_date,
            config=config
        )

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nReport saved to: {report_path}")

        if not config.auto_open_browser:
            print(f"\nTo view the report, open: {report_path}")

    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
