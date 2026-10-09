"""One-command check (the pre-commit hook runs this): unit tests + text lint."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tests = subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT)
lint = subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools" / "batches.py"), "lint"], cwd=ROOT)
sys.exit(tests or lint)
