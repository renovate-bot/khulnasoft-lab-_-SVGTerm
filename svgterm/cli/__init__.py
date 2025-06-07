"""Command-line interface for SVG Terminal Recorder."""

import argparse
import logging
import os
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..types import AnimationConfig, Geometry, Milliseconds, Template, TemplateName

logger = logging.getLogger("svgterm.cli")

DEFAULT_LOOP_DELAY: Milliseconds = 1000


def create_parser(templates: Dict[TemplateName, Template]) -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.
    
    Args:
        templates: Available templates
        
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Record terminal sessions as SVG animations"
    )
    
    # Global options
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__import__('svgterm').__version__}"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Record command
    record_parser = subparsers.add_parser(
        "record",
        help="Record terminal session to a file"
    )
    _add_common_arguments(record_parser, templates)
    _add_record_arguments(record_parser)
    
    # Render command
    render_parser = subparsers.add_parser(
        "render",
        help="Render a recording to SVG"
    )
    _add_common_arguments(render_parser, templates)
    _add_render_arguments(render_parser)
    
    # Default command (record and render)
    _add_common_arguments(parser, templates)
    _add_record_arguments(parser)
    _add_render_arguments(parser)
    
    return parser


def _add_common_arguments(
    parser: argparse.ArgumentParser,
    templates: Dict[TemplateName, Template]
) -> None:
    """Add common arguments to a parser."""
    parser.add_argument(
        "output_path",
        nargs="?",
        help="Output file or directory path"
    )
    parser.add_argument(
        "-t", "--template",
        choices=list(templates.keys()),
        default="default",
        help="SVG template to use"
    )


def _add_record_arguments(parser: argparse.ArgumentParser) -> None:
    """Add recording-specific arguments to a parser."""
    parser.add_argument(
        "-c", "--command",
        default=os.environ.get("SHELL", "sh"),
        help="Command to execute in the terminal"
    )
    parser.add_argument(
        "-g", "--geometry",
        type=_parse_geometry,
        help="Terminal geometry (WIDTHxHEIGHT)"
    )


def _add_render_arguments(parser: argparse.ArgumentParser) -> None:
    """Add rendering-specific arguments to a parser."""
    parser.add_argument(
        "-m", "--min-frame-duration",
        type=int,
        default=1,
        help="Minimum frame duration in milliseconds"
    )
    parser.add_argument(
        "-M", "--max-frame-duration",
        type=int,
        help="Maximum frame duration in milliseconds"
    )
    parser.add_argument(
        "-D", "--loop-delay",
        type=int,
        default=DEFAULT_LOOP_DELAY,
        help="Delay between animation loops in milliseconds"
    )
    parser.add_argument(
        "-s", "--still-frames",
        action="store_true",
        help="Generate still frames instead of an animation"
    )


def _parse_geometry(geometry_str: str) -> Tuple[int, int]:
    """Parse a geometry string into (width, height)."""
    try:
        width, height = map(int, geometry_str.lower().split("x"))
        if width <= 0 or height <= 0:
            raise ValueError("Dimensions must be positive")
        return width, height
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid geometry: {geometry_str}. Expected format: WIDTHxHEIGHT"
        ) from e


def main(args: Optional[List[str]] = None) -> None:
    """Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (default: sys.argv[1:])
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # Parse command-line arguments
    parser = create_parser({})  # TODO: Load templates
    parsed_args = parser.parse_args(args)
    
    # TODO: Implement command execution
    if parsed_args.command == "record":
        _handle_record(parsed_args)
    elif parsed_args.command == "render":
        _handle_render(parsed_args)
    else:
        _handle_record_and_render(parsed_args)


def _handle_record(args) -> None:
    """Handle the record command."""
    # TODO: Implement recording
    pass


def _handle_render(args) -> None:
    """Handle the render command."""
    # TODO: Implement rendering
    pass


def _handle_record_and_render(args) -> None:
    """Handle the default command (record and render)."""
    # TODO: Implement combined recording and rendering
    pass
