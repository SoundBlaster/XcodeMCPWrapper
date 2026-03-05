"""Unit tests for package version initialization."""

import importlib
from unittest.mock import patch

import mcpbridge_wrapper


def test_version_comes_from_importlib_metadata() -> None:
    with patch("importlib.metadata.version", return_value="9.9.9"):
        reloaded = importlib.reload(mcpbridge_wrapper)

    assert reloaded.__version__ == "9.9.9"


def test_version_fallback_when_metadata_unavailable() -> None:
    with patch("importlib.metadata.version", side_effect=Exception("missing metadata")):
        reloaded = importlib.reload(mcpbridge_wrapper)

    assert reloaded.__version__ == "0.0.0+unknown"

    # Restore module state for the remaining test session.
    importlib.reload(mcpbridge_wrapper)
