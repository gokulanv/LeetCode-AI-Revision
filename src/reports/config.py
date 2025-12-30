import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ReportConfig:
    """Configuration for LeetCode report generation."""

    output_dir: str = field(default_factory=lambda: os.path.expanduser("~/LeetCode-Reports"))
    timezone: str = "local"
    analyze_submissions: bool = True
    auto_open_browser: bool = True
    max_concurrent_llm: int = 5

    @classmethod
    def from_env(cls) -> 'ReportConfig':
        """
        Create configuration from environment variables.

        Environment variables:
            REPORT_OUTPUT_DIR: Directory for generated reports (default: ~/LeetCode-Reports)
            AUTO_OPEN_REPORT: Whether to auto-open reports in browser (default: true)
            MAX_LLM_CONCURRENT: Max concurrent OpenAI requests (default: 5)

        Returns:
            ReportConfig instance with values from environment
        """
        return cls(
            output_dir=os.getenv("REPORT_OUTPUT_DIR", os.path.expanduser("~/LeetCode-Reports")),
            analyze_submissions=os.getenv("ANALYZE_SUBMISSIONS", "true").lower() == "true",
            auto_open_browser=os.getenv("AUTO_OPEN_REPORT", "true").lower() == "true",
            max_concurrent_llm=int(os.getenv("MAX_LLM_CONCURRENT", "5"))
        )


def ensure_output_dir(path: str) -> Path:
    """
    Ensure output directory exists and is writable.

    Args:
        path: Directory path (can include ~)

    Returns:
        Resolved Path object

    Raises:
        ValueError: If directory cannot be created or is not writable
    """
    resolved_path = Path(path).expanduser().resolve()

    try:
        resolved_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Cannot create output directory {resolved_path}: {e}")

    if not os.access(resolved_path, os.W_OK):
        raise ValueError(f"Output directory {resolved_path} is not writable")

    return resolved_path
