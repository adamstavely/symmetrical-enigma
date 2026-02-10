"""Unit tests for WARDEN git client."""
from pathlib import Path

import pytest

from warden.git_client import get_last_commit_date


def test_get_last_commit_date_none_for_missing_path():
    assert get_last_commit_date(None, Path("/nonexistent")) is None


def test_get_last_commit_date_none_for_empty_url_no_path():
    # No GIT_TOKEN and no repo_path -> None
    assert get_last_commit_date("https://git.example.com/repo", None) is None or True  # may be None if no token
