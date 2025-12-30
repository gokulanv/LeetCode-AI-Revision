from datetime import datetime
from typing import List, Dict, Any, Optional
import markdown


def format_timestamp(unix_timestamp: int) -> str:
    """
    Convert Unix timestamp to readable format.

    Args:
        unix_timestamp: Unix epoch timestamp

    Returns:
        Formatted date string (e.g., "Dec 29, 2025 at 2:30 PM")
    """
    dt = datetime.fromtimestamp(unix_timestamp)
    return dt.strftime("%b %d, %Y at %I:%M %p")


def render_report_html(data: Dict[str, Any]) -> str:
    """
    Render complete HTML report from submission data.

    Args:
        data: Dictionary containing:
            - username: str
            - date_range: str (e.g., "Dec 28, 8:00 AM - Dec 29, 8:00 AM")
            - statistics: dict with total, unique, languages
            - submissions: list of submission dicts
            - generation_time: datetime

    Returns:
        Complete HTML string
    """
    username = data.get("username", "Unknown")
    date_range = data.get("date_range", "")
    stats = data.get("statistics", {})
    submissions = data.get("submissions", [])
    generation_time = data.get("generation_time", datetime.now())

    # Build statistics cards
    stats_html = f"""
    <div class="statistics">
        <div class="stat-card">
            <div class="stat-value">{stats.get('total', 0)}</div>
            <div class="stat-label">Total Submissions</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats.get('unique_problems', 0)}</div>
            <div class="stat-label">Unique Problems</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{_format_language_breakdown(stats.get('languages', {}))}</div>
            <div class="stat-label">Languages</div>
        </div>
    </div>
    """

    # Build submission cards
    submissions_html = ""
    for idx, submission in enumerate(submissions, 1):
        submissions_html += _render_submission_card(submission, idx)

    # If no submissions
    if not submissions:
        submissions_html = """
        <div class="no-submissions">
            <h2>No submissions found in this period</h2>
            <p>Try a different date range or check your LeetCode activity.</p>
        </div>
        """

    # Complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LeetCode Daily Report - {date_range}</title>
    <style>
        {_get_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LeetCode Daily Report</h1>
            <p class="username">@{username}</p>
            <p class="date-range">{date_range}</p>
        </div>

        {stats_html}

        <div class="submissions-section">
            <h2 class="section-title">Your Submissions</h2>
            {submissions_html}
        </div>

        <div class="footer">
            <a href="mailto:?subject=My LeetCode Report - {date_range}&body=Check out my LeetCode progress!" class="share-button">
                Share via Email
            </a>
            <p class="generation-info">Generated on {generation_time.strftime("%b %d, %Y at %I:%M %p")}</p>
        </div>
    </div>
</body>
</html>"""

    return html


def _render_submission_card(submission: Dict[str, Any], index: int) -> str:
    """Render a single submission card."""
    title = submission.get("title", "Unknown Problem")
    lang = submission.get("langName", submission.get("lang", "Unknown"))
    runtime = submission.get("runtime", "N/A")
    memory = submission.get("memory", "N/A")
    timestamp = submission.get("timestamp")
    code = submission.get("code", "")
    analysis = submission.get("analysis", None)
    status = submission.get("statusDisplay", "Accepted")

    # Format timestamp
    time_str = format_timestamp(int(timestamp)) if timestamp else "Unknown time"

    # Format code with proper escaping
    code_html = _escape_html(code) if code else "Code not available"

    # Render analysis if available
    analysis_html = ""
    if analysis:
        # Convert markdown analysis to HTML
        analysis_md = markdown.markdown(
            analysis,
            extensions=['extra', 'codehilite', 'fenced_code']
        )
        analysis_html = f"""
        <div class="analysis-section">
            <h3>AI Revision Tips</h3>
            <div class="analysis-content">{analysis_md}</div>
        </div>
        """
    elif analysis is None and submission.get("analysis_error"):
        analysis_html = """
        <div class="analysis-section analysis-unavailable">
            <p>Analysis unavailable for this submission</p>
        </div>
        """

    return f"""
    <div class="submission-card">
        <div class="submission-header">
            <h3><span class="submission-number">#{index}</span> {_escape_html(title)}</h3>
            <span class="status-badge status-{status.lower().replace(' ', '-')}">{status}</span>
        </div>
        <div class="metadata">
            <span class="metadata-item"><strong>Language:</strong> {lang}</span>
            <span class="metadata-item"><strong>Runtime:</strong> {runtime}</span>
            <span class="metadata-item"><strong>Memory:</strong> {memory}</span>
            <span class="metadata-item"><strong>Time:</strong> {time_str}</span>
        </div>
        <div class="code-section">
            <h3>Your Solution</h3>
            <pre><code class="language-{lang.lower()}">{code_html}</code></pre>
        </div>
        {analysis_html}
    </div>
    """


def _format_language_breakdown(languages: Dict[str, int]) -> str:
    """Format language breakdown for display."""
    if not languages:
        return "N/A"
    return ", ".join([f"{lang}: {count}" for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)])


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


def _get_css() -> str:
    """
    Get CSS styling for reports.
    Reuses patterns from src/utils/email.py with report-specific additions.
    """
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f7fa;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .header {
            text-align: center;
            padding: 40px 20px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .username {
            font-size: 1.2em;
            opacity: 0.95;
            margin-bottom: 5px;
        }

        .date-range {
            font-size: 1em;
            opacity: 0.9;
        }

        .statistics {
            display: flex;
            justify-content: space-around;
            padding: 30px 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            flex-wrap: wrap;
            gap: 15px;
        }

        .stat-card {
            flex: 1;
            min-width: 150px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9em;
        }

        .submissions-section {
            padding: 30px 20px;
        }

        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }

        .submission-card {
            margin-bottom: 30px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            background-color: #fafafa;
        }

        .submission-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .submission-header h3 {
            color: #2c3e50;
            font-size: 1.4em;
            flex: 1;
        }

        .submission-number {
            color: #667eea;
            margin-right: 8px;
        }

        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .status-accepted {
            background-color: #d4edda;
            color: #155724;
        }

        .metadata {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background-color: white;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .metadata-item {
            color: #666;
            font-size: 0.95em;
        }

        .code-section {
            margin: 20px 0;
        }

        .code-section h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        pre {
            background-color: #2d2d2d;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.5;
        }

        code {
            font-family: 'Courier New', Consolas, Monaco, monospace;
            color: #f8f8f2;
        }

        pre code {
            background-color: transparent;
            padding: 0;
        }

        .analysis-section {
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
            border-left: 4px solid #2196f3;
        }

        .analysis-section h3 {
            color: #1976d2;
            margin-bottom: 15px;
            font-size: 1.1em;
        }

        .analysis-content {
            color: #333;
            line-height: 1.8;
        }

        .analysis-content h1, .analysis-content h2, .analysis-content h3 {
            color: #1976d2;
            margin-top: 15px;
            margin-bottom: 10px;
        }

        .analysis-content p {
            margin-bottom: 10px;
        }

        .analysis-content ul, .analysis-content ol {
            margin-left: 25px;
            margin-bottom: 10px;
        }

        .analysis-content code {
            background-color: rgba(33, 150, 243, 0.1);
            padding: 2px 6px;
            border-radius: 3px;
            color: #1976d2;
            font-size: 0.9em;
        }

        .analysis-unavailable {
            background-color: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }

        .no-submissions {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .no-submissions h2 {
            color: #999;
            margin-bottom: 10px;
        }

        .footer {
            text-align: center;
            padding: 30px 20px;
            background-color: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }

        .share-button {
            display: inline-block;
            background-color: #667eea;
            color: white;
            padding: 12px 30px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            margin-bottom: 15px;
            transition: background-color 0.3s;
        }

        .share-button:hover {
            background-color: #5568d3;
        }

        .generation-info {
            color: #999;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }

            .statistics {
                flex-direction: column;
            }

            .submission-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .metadata {
                flex-direction: column;
                gap: 10px;
            }
        }
    """
