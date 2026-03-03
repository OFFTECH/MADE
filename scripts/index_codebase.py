#!/usr/bin/env python3
"""Convenience wrapper for tools/index_codebase.py.

This script exists in scripts/ for discoverability but delegates to
the canonical implementation in tools/.

Usage: python scripts/index_codebase.py [args]
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOL = REPO_ROOT / "tools" / "index_codebase.py"

sys.exit(subprocess.run([sys.executable, str(TOOL)] + sys.argv[1:]).returncode)
