# Ensures the repo root is on the import path so tests can
# import services.detection.serve regardless of how pytest is invoked.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))