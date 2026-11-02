"""Pytest configuration and shared fixtures."""

import os
import sys

# Ensure the src directory is on the path so lib imports work
src_dir = os.path.dirname(os.path.dirname(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
