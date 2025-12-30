import asyncio
import webbrowser
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import httpx

from .config import ReportConfig, ensure_output_dir
from .templates import render_report_html
from src.leetcode.api import get_authenticated_client, format_submission_for_llm
from src.llm.openai_client import get_completion


async def generate_daily_report(
    username: str,
    date: Optional[datetime] = None,
    config: Optional[ReportConfig] = None
) -> str:
    """
    Generate a daily LeetCode report for the specified user.

    Args:
        username: LeetCode username
        date: Date for the report (defaults to yesterday)
        config: Report configuration (defaults to env-based config)

    Returns:
        Path to the generated HTML report file

    Raises:
        ValueError: If submissions cannot be fetched or other validation errors
    """
    # Load configuration
    if config is None:
        config = ReportConfig.from_env()

    # Default to yesterday if no date provided
    if date is None:
        date = datetime.now() - timedelta(days=1)

    # Calculate 8AM-8AM time window
    start_time, end_time = _calculate_time_window(date)

    print(f"Fetching submissions for {username}...")
    print(f"Time window: {start_time.strftime('%b %d, %I:%M %p')} - {end_time.strftime('%b %d, %I:%M %p')}")

    # Fetch submissions
    submissions = await _fetch_submissions(username)

    # Filter by time window
    filtered_submissions = filter_submissions_by_window(submissions, start_time, end_time)

    print(f"Found {len(filtered_submissions)} submissions in the time window")

    # Get LLM analyses if enabled
    if config.analyze_submissions and filtered_submissions:
        print(f"Analyzing submissions with AI...")
        await get_llm_analyses(filtered_submissions, config.max_concurrent_llm)
        print("Analysis complete!")

    # Calculate statistics
    statistics = calculate_statistics(filtered_submissions)

    # Prepare report data
    report_data = {
        "username": username,
        "date_range": f"{start_time.strftime('%b %d, %I:%M %p')} - {end_time.strftime('%b %d, %I:%M %p')}",
        "statistics": statistics,
        "submissions": filtered_submissions,
        "generation_time": datetime.now()
    }

    # Render HTML
    html_content = render_report_html(report_data)

    # Save report
    output_dir = ensure_output_dir(config.output_dir)
    report_filename = f"leetcode-report-{date.strftime('%Y-%m-%d')}.html"
    report_path = output_dir / report_filename

    # Handle collision (rare, but possible if run multiple times same day)
    if report_path.exists():
        timestamp = datetime.now().strftime('%H%M%S')
        report_filename = f"leetcode-report-{date.strftime('%Y-%m-%d')}-{timestamp}.html"
        report_path = output_dir / report_filename

    report_path.write_text(html_content, encoding='utf-8')
    print(f"\nReport generated: {report_path}")

    # Auto-open in browser
    if config.auto_open_browser:
        print("Opening in browser...")
        open_in_browser(str(report_path))

    return str(report_path)


def _calculate_time_window(date: datetime) -> tuple[datetime, datetime]:
    """
    Calculate 8AM-8AM time window for the given date.

    Args:
        date: Target date

    Returns:
        Tuple of (start_time, end_time) both as datetime objects
    """
    # Start: 8AM on the given date
    start_time = date.replace(hour=8, minute=0, second=0, microsecond=0)

    # End: 8AM on the next day
    end_time = start_time + timedelta(days=1)

    return start_time, end_time


async def _fetch_submissions(username: str) -> List[Dict[str, Any]]:
    """
    Fetch submissions from LeetCode API.

    Args:
        username: LeetCode username

    Returns:
        List of submission dictionaries

    Raises:
        ValueError: If submissions cannot be fetched
    """
    query = """query recentSubmissions($username: String!, $limit: Int) {
        recentSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
            status
            statusDisplay
            lang
            langName
            runtime
            memory
        }
    }"""

    payload = {
        "query": query,
        "variables": {"username": username, "limit": 50}
    }

    try:
        async with get_authenticated_client() as client:
            response = await client.post("https://leetcode.com/graphql", json=payload)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    raise ValueError(f"LeetCode API error: User '{username}' not found")

                submissions = data["data"]["recentSubmissionList"]

                # Fetch code for each submission
                for submission in submissions:
                    code = await _get_submission_code(submission["id"])
                    submission["code"] = code

                return submissions
            else:
                raise ValueError(f"Failed to fetch submissions: HTTP {response.status_code}")
    except httpx.RequestError as e:
        raise ValueError(f"Network error while fetching submissions: {e}")


async def _get_submission_code(submission_id: int) -> Optional[str]:
    """
    Fetch code for a specific submission.

    Args:
        submission_id: Submission ID

    Returns:
        Code string or None if unavailable
    """
    leetcode_session = os.getenv('LEETCODE_SESSION')
    if not leetcode_session:
        return None

    query = """query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            code
        }
    }"""

    payload = {
        "query": query,
        "variables": {"submissionId": submission_id},
        "operationName": "submissionDetails"
    }

    try:
        async with get_authenticated_client() as client:
            response = await client.post("https://leetcode.com/graphql", json=payload)
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    submission_details = data.get("data", {}).get("submissionDetails")
                    if submission_details:
                        return submission_details.get("code")
    except Exception:
        pass  # Silently fail for individual submissions

    return None


def filter_submissions_by_window(
    submissions: List[Dict[str, Any]],
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Filter submissions by time window (8AM-8AM).

    Args:
        submissions: List of submission dictionaries
        start_time: Window start time
        end_time: Window end time

    Returns:
        Filtered list of submissions (sorted by timestamp, newest first)
    """
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())

    filtered = []
    for submission in submissions:
        timestamp = int(submission.get("timestamp", "0"))
        if start_ts <= timestamp < end_ts:
            filtered.append(submission)

    # Sort by timestamp (newest first)
    filtered.sort(key=lambda x: int(x.get("timestamp", "0")), reverse=True)

    return filtered


async def get_llm_analyses(
    submissions: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> None:
    """
    Get LLM analysis for all submissions in parallel.

    Modifies submissions in-place by adding 'analysis' field.

    Args:
        submissions: List of submission dictionaries
        max_concurrent: Maximum concurrent API requests
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze_one(submission: Dict[str, Any]) -> None:
        """Analyze a single submission."""
        async with semaphore:
            try:
                # Format for LLM
                formatted_data = {
                    "question": {
                        "title": submission.get("title", "Unknown"),
                        "titleSlug": submission.get("titleSlug", ""),
                    },
                    "code": submission.get("code", "")
                }
                formatted_text = format_submission_for_llm(formatted_data)

                # Get analysis (running sync function in executor)
                loop = asyncio.get_event_loop()
                analysis = await loop.run_in_executor(None, get_completion, formatted_text)

                submission["analysis"] = analysis
            except Exception as e:
                submission["analysis"] = None
                submission["analysis_error"] = str(e)

    # Analyze all submissions in parallel
    await asyncio.gather(*[analyze_one(sub) for sub in submissions])


def calculate_statistics(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics from submissions.

    Args:
        submissions: List of submission dictionaries

    Returns:
        Dictionary with statistics (total, unique_problems, languages)
    """
    if not submissions:
        return {
            "total": 0,
            "unique_problems": 0,
            "languages": {}
        }

    # Count unique problems by titleSlug
    unique_problems = len(set(sub.get("titleSlug", "") for sub in submissions))

    # Count languages
    languages = {}
    for sub in submissions:
        lang = sub.get("langName", sub.get("lang", "Unknown"))
        languages[lang] = languages.get(lang, 0) + 1

    return {
        "total": len(submissions),
        "unique_problems": unique_problems,
        "languages": languages
    }


def open_in_browser(file_path: str) -> bool:
    """
    Open HTML report in default browser.

    Args:
        file_path: Absolute path to HTML file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert to file:// URL for browser
        file_url = f"file://{os.path.abspath(file_path)}"
        webbrowser.open(file_url)
        return True
    except Exception as e:
        print(f"Warning: Failed to open browser: {e}")
        print(f"You can manually open: {file_path}")
        return False
