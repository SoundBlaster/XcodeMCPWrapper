"""
Pytest configuration and shared fixtures for unit tests.
"""

import sys
from pathlib import Path

# Add scripts directory to Python path for importing
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))
