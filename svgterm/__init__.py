"""SVG Terminal Recorder

A tool to record terminal sessions as SVG animations.
"""

from importlib.metadata import version

__version__ = version("svgterm")
__all__ = ["__version__", "record", "render", "record_and_render"]

# Import main functionality
from svgterm.cli import main
from svgterm.core import record, render, record_and_render

# Clean up the namespace
del version