"""
Entry point for the FL validation agent.

From the AgentV2 project root:
    python FL/main.py [options]      (replaces the old `python FL/run_validation.py`)
    python -m FL [options]
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Started as a script: swap the FL folder for the project root on sys.path so `FL` resolves as a
    # package and its sub-packages (config, core, data, ...) cannot shadow third-party modules.
    sys.path[0] = str(Path(__file__).resolve().parents[1])

from FL.pipeline.run_validation import main

if __name__ == "__main__":
    main()
