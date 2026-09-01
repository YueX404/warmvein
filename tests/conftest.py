# Add src/python to sys.path so tests can import project modules
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1] / "src" / "python"
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
