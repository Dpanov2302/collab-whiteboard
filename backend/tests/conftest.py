"""Test configuration.

GitHub Actions runs pytest from the backend directory, while some local IDEs run it
from the repository root. Explicitly adding the backend directory to sys.path keeps
imports like `from app.main import app` stable in both cases.
"""

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
