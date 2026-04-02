# ABOUTME: Root pytest configuration.
# ABOUTME: Ensures the project root is on sys.path for all test modules.

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
