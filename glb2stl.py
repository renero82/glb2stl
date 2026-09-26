#!/usr/bin/env python3
"""Backward-compatible launcher for the command line: python3 glb2stl.py model.glb"""
import sys

from glb2stl.cli import main

if __name__ == "__main__":
    sys.exit(main())
