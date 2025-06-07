"""Command line interface for SVG Terminal Recorder.

This module provides the main command-line interface for recording terminal sessions
and rendering them as SVG animations or still frames. It handles argument parsing,
subcommand dispatching, and orchestrates the recording and rendering processes.
"""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
    IO,
    Generator,
    BinaryIO,
    TextIO,
    AnyStr,
    Callable,
    Iterator,
    Mapping,
    MutableMapping,
    NamedTuple,
    NoReturn,
    Type,
    TypeVar,
    overload,
)

from typing_extensions import TypedDict, Literal, Protocol

from svgterm import __version__
import svgterm.anim
import svgterm.config
import svgterm.term
from svgterm.types import (
    Milliseconds,
    Geometry,
    TemplateName,
    Template,
    AnimationConfig,
)

# Type variables
T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')

# Constants
DEFAULT_LOOP_DELAY: Milliseconds = 1000
DEFAULT_MIN_FRAME_DURATION: Milliseconds = 1
DEFAULT_GEOMETRY: Geometry = (80, 24)
DEFAULT_TEMPLATE: str = "powershell"

# Module-level logger
logger: logging.Logger = logging.getLogger(__name__)

# Usage strings for help messages
USAGE = """
svgterm [output_path] [-c COMMAND] [-D DELAY] [-g GEOMETRY]
        [-m MIN_DURATION] [-M MAX_DURATION] [-s] [-t TEMPLATE] [-h]

Record a terminal session and render an SVG animation on the fly.
"""

EPILOG = """
See also:
  svgterm record --help    For recording terminal sessions
  svgterm render --help   For rendering recorded sessions
"""

RECORD_USAGE = """
svgterm record [output_path] [-c COMMAND] [-g GEOMETRY] [-h]

Record a terminal session to an asciicast file.
"""

RENDER_USAGE = """
svgterm render input_file [output_path] [-D DELAY] [-m MIN_DURATION]
        [-M MAX_DURATION] [-s] [-t TEMPLATE] [-h]

Render a recorded terminal session as an SVG animation or still frames.
"""


class CommandLineArgs(TypedDict, total=False):
    """Typed dictionary for parsed command line arguments.
    
    This class defines the structure of the parsed command line arguments
    with proper type hints. The 'total=False' indicates that all fields are optional.
    """
    command: str
    output_path: Optional[str]
    input_file: Optional[str]
    screen_geometry: Optional[Geometry]
    min_frame_duration: Milliseconds
    max_frame_duration: Optional[Milliseconds]
    loop_delay: Milliseconds
    template: Union[TemplateName, Template]
    still_frames: bool
    verbose: bool
    quiet: bool
    env: Optional[Dict[str, str]]


def validate_geometry(geometry_str: str) -> Geometry:
    """Validate and parse a geometry string.
    
    Args:
        geometry_str: String in format 'WIDTHxHEIGHT'
        
    Returns:
        Tuple of (width, height) as integers
        
    Raises:
        argparse.ArgumentTypeError: If the geometry string is invalid
    """
    try:
        if not geometry_str:
            raise ValueError("Empty geometry string")
            
        parts = geometry_str.lower().split('x')
        if len(parts) != 2:
            raise ValueError("Geometry must be in format WIDTHxHEIGHT")
            
        width, height = map(int, parts)
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive integers")
            
        return width, height
        
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid geometry: {geometry_str}. {str(e)}"
        )


def validate_duration(duration_str: str) -> Milliseconds:
    """Validate and convert a duration string to milliseconds.
    
    Args:
        duration_str: Duration string (e.g., '100ms' or '1.5s')
        
    Returns:
        Duration in milliseconds
        
    Raises:
        argparse.ArgumentTypeError: If the duration is invalid
    """
    try:
        if not duration_str:
            raise ValueError("Empty duration string")
            
        # Remove 'ms' suffix if present
        if duration_str.lower().endswith('ms'):
            value = float(duration_str[:-2])
        # Remove 's' suffix if present
        elif duration_str[-1].lower() == 's':
            value = float(duration_str[:-1]) * 1000
        else:
            value = float(duration_str)
            
        if value <= 0:
            raise ValueError("Duration must be positive")
            
        return int(round(value))
        
    except (ValueError, TypeError) as e:
        raise argparse.ArgumentTypeError(
            f"Invalid duration: {duration_str}. {str(e)}"
        )


def integral_duration_validation(duration: str) -> int:
    """Validate and convert a duration string to milliseconds.
    
    This is a backward-compatible wrapper around the newer validate_duration function,
    maintained for compatibility with existing code.
    
    Args:
        duration: Duration string, optionally ending with 'ms' or 's'
        
    Returns:
        Duration in milliseconds as an integer
        
    Raises:
        ValueError: If duration is not a positive number
    """
    try:
        return validate_duration(duration)
    except argparse.ArgumentTypeError as e:
        # Convert to ValueError for backward compatibility
        raise ValueError(str(e)) from e


def create_geometry_parser(parser: argparse.ArgumentParser) -> None:
    """Add geometry-related arguments to a parser.
    
    Args:
        parser: Argument parser to add geometry arguments to
    """
    geometry_group = parser.add_argument_group('geometry arguments')
    
    # Add --screen-geometry as the primary option
    geometry_group.add_argument(
        '--screen-geometry',
        dest='screen_geometry',
        type=validate_geometry,
        help='Terminal dimensions in the form "WIDTHxHEIGHT". Default: terminal size',
        metavar='GEOMETRY'
    )
    
    # Add --geometry and -g as aliases for backward compatibility
    if not any(any(opt in action.option_strings for opt in ['--geometry', '-g'])
              for action in parser._actions 
              if hasattr(action, 'option_strings')):
        geometry_group.add_argument(
            '--geometry', '-g',
            dest='screen_geometry',
            type=validate_geometry,
            help=argparse.SUPPRESS,  # Hidden from help as it's deprecated
            metavar='GEOMETRY'
        )


def create_common_parsers(
    templates: Dict[str, str],
    default_template: str,
    default_min_dur: int,
    default_max_dur: Optional[int],
    default_loop_delay: int,
) -> Dict[str, argparse.ArgumentParser]:
    """Create common argument parsers.
    
    Args:
        templates: Available template names and content
        default_template: Default template name
        default_min_dur: Default minimum frame duration
        default_max_dur: Default maximum frame duration
        default_loop_delay: Default loop delay
        
    Returns:
        Dictionary of common argument parsers
    """
    # Parser for common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    common_parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress non-error output'
    )
    
    # Parser for command specification
    command_parser = argparse.ArgumentParser(add_help=False)
    command_parser.add_argument(
        '-c', '--command',
        default=os.environ.get('SHELL', 'sh'),
        help='Command to execute in the terminal (default: $SHELL or sh)'
    )
    
    # Parser for template selection
    template_parser = argparse.ArgumentParser(add_help=False)
    template_parser.add_argument(
        '-t', '--template',
        choices=list(templates.keys()),
        default=default_template,
        help='SVG template to use (default: %(default)s)'
    )
    
    # Parser for duration-related arguments
    duration_parser = argparse.ArgumentParser(add_help=False)
    duration_parser.add_argument(
        '-m', '--min-frame-duration',
        type=integral_duration_validation,
        default=default_min_dur,
        help=f'Minimum frame duration in ms (default: {default_min_dur}ms)'
    )
    
    if default_max_dur is not None:
        max_dur_help = f'Maximum frame duration in ms (default: {default_max_dur}ms)'
    else:
        max_dur_help = 'Maximum frame duration in ms (default: no limit)'
    
    duration_parser.add_argument(
        '-M', '--max-frame-duration',
        type=integral_duration_validation,
        default=default_max_dur,
        help=max_dur_help
    )
    
    duration_parser.add_argument(
        '-D', '--loop-delay',
        type=integral_duration_validation,
        default=default_loop_delay,
        help=f'Delay between animation loops in ms (default: {default_loop_delay}ms)'
    )
    
    # Parser for still frames option
    still_parser = argparse.ArgumentParser(add_help=False)
    still_parser.add_argument(
        '-s', '--still-frames',
        action='store_true',
        help='Generate still frames instead of an animation'
    )
    
    return {
        'common': common_parser,
        'command': command_parser,
        'template': template_parser,
        'duration': duration_parser,
        'still': still_parser,
    }


def parse_geometry(geometry_str: Optional[str]) -> Optional[Geometry]:
    """Parse a geometry string into a (width, height) tuple.
    
    Args:
        geometry_str: String in format 'WIDTHxHEIGHT' or None
        
    Returns:
        Tuple of (width, height) as integers, or None if input is invalid
    """
    if not geometry_str:
        return None
    try:
        width, height = map(int, geometry_str.lower().split('x'))
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        return width, height
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError(
            f'Invalid geometry: {geometry_str}. Expected format: WIDTHxHEIGHT'
        )

def parse(
    args: List[str],
    templates: Dict[str, str],
    default_template: str,
    default_geometry: Optional[Geometry],
    default_min_dur: int,
    default_max_dur: Optional[int],
    default_cmd: str,
    default_loop_delay: int,
) -> Tuple[Optional[str], CommandLineArgs]:
    """Parse command line arguments.

    Args:
        args: Command line arguments to parse
        templates: Mapping between template names and template content
        default_template: Name of the default template to use
        default_geometry: Default terminal geometry as (columns, rows)
        default_min_dur: Default minimum frame duration in milliseconds
        default_max_dur: Default maximum frame duration in milliseconds
        default_cmd: Default command to run in the terminal
        default_loop_delay: Default delay between animation loops in milliseconds

    Returns:
        A tuple containing:
            - The subcommand (None, 'record', or 'render')
            - A dictionary of parsed arguments
    """
    # Create the main parser
    parser = argparse.ArgumentParser(
        prog="svgterm",
        description="Record and render terminal sessions as SVG animations",
        usage=USAGE,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    # Add common arguments
    parser.add_argument(
        '-h', '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='show this help message and exit'
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(
        dest='subcommand',
        help='Subcommand to execute',
        metavar='{record,render}'
    )
    
    # Helper function to add common arguments to a subparser
    def add_common_arguments(subparser):
        # Add template selection
        subparser.add_argument(
            '-t', '--template',
            choices=list(templates.keys()),
            default=default_template,
            help='SVG template to use (default: %(default)s)'
        )
        # Add duration arguments
        subparser.add_argument(
            '-m', '--min-frame-duration',
            type=integral_duration_validation,
            default=default_min_dur,
            help=f'Minimum frame duration in ms (default: {default_min_dur}ms)'
        )
        if default_max_dur is not None:
            max_dur_help = f'Maximum frame duration in ms (default: {default_max_dur}ms)'
        else:
            max_dur_help = 'Maximum frame duration in ms (default: no limit)'
        subparser.add_argument(
            '-M', '--max-frame-duration',
            type=integral_duration_validation,
            default=default_max_dur,
            help=max_dur_help
        )
        subparser.add_argument(
            '-D', '--loop-delay',
            type=integral_duration_validation,
            default=default_loop_delay,
            help=f'Delay between animation loops in ms (default: {default_loop_delay}ms)'
        )
        # Add verbosity flags
        subparser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='increase output verbosity'
        )
        subparser.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='decrease output verbosity'
        )
    
    # Record subcommand
    record_parser = subparsers.add_parser(
        'record',
        help='Record a terminal session to a file',
        usage=RECORD_USAGE,
        add_help=False
    )
    record_parser.add_argument(
        'filename',
        nargs='?',
        help='filename of the recording (default: auto-generated name)'
    )
    record_parser.add_argument(
        '-c', '--command',
        default=default_cmd,
        help='Command to execute in the terminal (default: %(default)s)'
    )
    record_parser.add_argument(
        '-e', '--env',
        default='SHELL,TERM',
        help='list of environment variables to capture, defaults to "SHELL,TERM"'
    )
    add_common_arguments(record_parser)
    create_geometry_parser(record_parser)
    
    # Render subcommand
    render_parser = subparsers.add_parser(
        'render',
        help='Render an asciicast recording as an SVG animation',
        usage=RENDER_USAGE,
        add_help=False
    )
    render_parser.add_argument(
        'input_file',
        metavar='input_file',
        help='recording of a terminal session in asciicast v1 or v2 format'
    )
    render_parser.add_argument(
        'output_path',
        nargs='?',
        metavar='output_path',
        help='filename of the SVG animation or directory for still frames. If --still-frame is '
             'specified, output_path should be the path of the directory where still frames will be '
             'stored. If missing, a random path will be automatically generated.'
    )
    render_parser.add_argument(
        '-s', '--still-frames',
        action='store_true',
        help='Save each frame as an individual SVG file instead of an animation',
    )
    add_common_arguments(render_parser)
    
    # Default command (record and render in one step)
    default_parser = subparsers.add_parser(
        'default',
        help='record and render in one command (default)',
        usage=USAGE,
        add_help=False
    )
    default_parser.add_argument(
        'output_path',
        nargs='?',
        help='filename of the SVG animation or directory for still frames',
        metavar='output_path'
    )
    default_parser.add_argument(
        '-c', '--command',
        default=default_cmd,
        help='Command to execute in the terminal (default: %(default)s)'
    )
    default_parser.add_argument(
        '-s', '--still-frames',
        action='store_true',
        help='render still frames instead of an animation'
    )
    add_common_arguments(default_parser)
    create_geometry_parser(default_parser)
    
    # Handle default command if no subcommand is provided
    if not args or args[0] not in ['record', 'render', 'default']:
        args = ['default'] + (args or [])
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Convert screen_geometry string to tuple if it exists
    screen_geometry = default_geometry
    if hasattr(parsed_args, 'screen_geometry') and parsed_args.screen_geometry:
        if isinstance(parsed_args.screen_geometry, str):
            try:
                screen_geometry = parse_geometry(parsed_args.screen_geometry)
            except argparse.ArgumentTypeError:
                screen_geometry = default_geometry
    
    # Convert to CommandLineArgs dictionary
    result_args: CommandLineArgs = {
        'command': getattr(parsed_args, 'command', default_cmd),
        'output_path': getattr(parsed_args, 'output_path', None),
        'input_file': getattr(parsed_args, 'input_file', None),
        'screen_geometry': screen_geometry,
        'min_frame_duration': getattr(parsed_args, 'min_frame_duration', default_min_dur),
        'max_frame_duration': getattr(parsed_args, 'max_frame_duration', default_max_dur),
        'loop_delay': getattr(parsed_args, 'loop_delay', default_loop_delay),
        'template': getattr(parsed_args, 'template', default_template),
        'still_frames': getattr(parsed_args, 'still_frames', False),
        'verbose': getattr(parsed_args, 'verbose', False),
        'quiet': getattr(parsed_args, 'quiet', False),
        'env': None
    }
    
    # Special handling for record subcommand
    if parsed_args.subcommand == 'record':
        result_args['output_path'] = getattr(parsed_args, 'filename', None)
        # Parse environment variables
        if hasattr(parsed_args, 'env') and parsed_args.env:
            result_args['env'] = {var.strip(): os.environ.get(var.strip(), '') 
                                for var in parsed_args.env.split(',') if var.strip()}
    
    return (parsed_args.subcommand if parsed_args.subcommand != 'default' else None, 
            result_args)


def record_subcommand(
    process_args, geometry, input_fileno, output_fileno, cast_filename
):
    """Save a terminal session as an asciicast recording"""
    from svgterm.term import get_terminal_size, TerminalMode, record

    logger.info('Recording started, enter "exit" command or Control-D to end')
    if geometry is None:
        columns, lines = get_terminal_size(output_fileno)
    else:
        columns, lines = geometry
    with TerminalMode(input_fileno):
        # Do not write anything to stdout (print, logger...) while in this
        # context manager if the output of the process is set to stdout. We
        # do not want two processes writing to the same terminal.
        records = record(process_args, columns, lines, input_fileno, output_fileno)
        with open(cast_filename, "w") as cast_file:
            for record_ in records:
                print(record_.to_json_line(), file=cast_file)
    logger.info("Recording ended, cast file is {}".format(cast_filename))


def render_subcommand(
    still,
    template,
    cast_filename,
    output_path,
    min_frame_duration,
    max_frame_duration,
    loop_delay,
):
    """Render the animation from an asciicast recording"""
    from svgterm.asciicast import read_records
    from svgterm.term import timed_frames

    logger.info("Rendering started")
    asciicast_records = read_records(cast_filename)
    geometry, frames = timed_frames(
        asciicast_records, min_frame_duration, max_frame_duration, loop_delay
    )
    if still:
        svgterm.anim.render_still_frames(
            frames=frames, geometry=geometry, directory=output_path, template=template
        )
        logger.info("Rendering ended, SVG frames are located at {}".format(output_path))
    else:
        svgterm.anim.render_animation(
            frames=frames, geometry=geometry, filename=output_path, template=template
        )
        logger.info("Rendering ended, SVG animation is {}".format(output_path))


def record_render_subcommand(
    process_args,
    still,
    template,
    geometry,
    input_fileno,
    output_fileno,
    output_path,
    min_frame_duration,
    max_frame_duration,
    loop_delay,
):
    """Record and render the animation on the fly"""
    from svgterm.term import get_terminal_size, TerminalMode, record, timed_frames

    logger.info('Recording started, enter "exit" command or Control-D to end')
    if geometry is None:
        columns, lines = get_terminal_size(output_fileno)
    else:
        columns, lines = geometry
    with TerminalMode(input_fileno):
        # Do not write anything to stdout (print, logger...) while in this
        # context manager if the output of the process is set to stdout. We
        # do not want two processes writing to the same terminal.
        asciicast_records = record(
            process_args, columns, lines, input_fileno, output_fileno
        )
        geometry, frames = timed_frames(
            asciicast_records, min_frame_duration, max_frame_duration, loop_delay
        )

        if still:
            svgterm.anim.render_still_frames(frames, geometry, output_path, template)
            end_msg = "Rendering ended, SVG frames are located at {}"
        else:
            svgterm.anim.render_animation(frames, geometry, output_path, template)
            end_msg = "Rendering ended, SVG animation is {}"

    logger.info(end_msg.format(output_path))


def main(args=None, input_fileno=None, output_fileno=None) -> None:
    """Main entry point for the svgterm command line interface.

    Args:
        args: Command line arguments (default: None, which uses sys.argv[1:])
        input_fileno: File descriptor for input (default: None, which uses sys.stdin.fileno())
        output_fileno: File descriptor for output (default: None, which uses sys.stdout.fileno())
    """
    if args is None:
        args = sys.argv[1:]

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    logger = logging.getLogger('svgterm')

    try:
        # Parse command line arguments
        subcommand, parsed_args = parse(
            args=args,
            templates=svgterm.config.default_templates(),
            default_template='powershell',
            default_geometry=None,
            default_min_dur=1,
            default_max_dur=None,
            default_cmd=os.environ.get('SHELL', 'sh'),
            default_loop_delay=1000
        )

        # Set log level based on verbosity
        if parsed_args.get('verbose'):
            logger.setLevel(logging.DEBUG)
        elif parsed_args.get('quiet'):
            logger.setLevel(logging.ERROR)

        logger.debug('Parsed arguments: %s', parsed_args)

        # Get input and output file descriptors
        if input_fileno is None:
            input_fileno = sys.stdin.fileno()
        if output_fileno is None:
            output_fileno = sys.stdout.fileno()

        # Get the template as bytes
        template_name = parsed_args.get('template', 'powershell')
        templates = svgterm.config.default_templates()
        template = templates[template_name]
        if isinstance(template, str):
            template = template.encode('utf-8')

        # Execute the appropriate subcommand
        if subcommand == 'record':
            output_path = parsed_args.get('output_path')
            if output_path is None:
                _, output_path = tempfile.mkstemp(prefix="svgterm_", suffix=".cast")
                
            record_subcommand(
                process_args=shlex.split(parsed_args.get('command', os.environ.get('SHELL', 'sh'))),
                geometry=parsed_args.get('screen_geometry'),
                input_fileno=input_fileno,
                output_fileno=output_fileno,
                cast_filename=output_path
            )
        elif subcommand == 'render':
            input_file = parsed_args.get('input_file')
            if not input_file:
                raise ValueError("Input file is required for render command")
                
            output_path = parsed_args.get('output_path')
            if parsed_args.get('still_frames', False):
                if output_path:
                    os.makedirs(output_path, exist_ok=True)
                else:
                    output_path = tempfile.mkdtemp(prefix="svgterm_frames_")
            elif not output_path:
                output_path = os.path.splitext(input_file)[0] + '.svg'
            
            render_subcommand(
                still=parsed_args.get('still_frames', False),
                template=template,
                cast_filename=input_file,
                output_path=output_path,
                min_frame_duration=parsed_args.get('min_frame_duration', 1),
                max_frame_duration=parsed_args.get('max_frame_duration'),
                loop_delay=parsed_args.get('loop_delay', 1000)
            )
        else:  # Default command (record and render)
            output_path = parsed_args.get('output_path', 'terminal.svg')
            
            record_render_subcommand(
                process_args=shlex.split(parsed_args.get('command', os.environ.get('SHELL', 'sh'))),
                still=parsed_args.get('still_frames', False),
                template=template,
                geometry=parsed_args.get('screen_geometry'),
                input_fileno=input_fileno,
                output_fileno=output_fileno,
                output_path=output_path,
                min_frame_duration=parsed_args.get('min_frame_duration', 1),
                max_frame_duration=parsed_args.get('max_frame_duration'),
                loop_delay=parsed_args.get('loop_delay', 1000)
            )

    except KeyboardInterrupt:
        logger.info('Operation cancelled by user')
        sys.exit(1)
    except Exception as e:
        logger.error('Error: %s', str(e))
        if 'parsed_args' in locals() and parsed_args.get('verbose'):
            logger.exception('Stack trace:')
        sys.exit(1)
    finally:
        # Ensure all log handlers are properly closed
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
