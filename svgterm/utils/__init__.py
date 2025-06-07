"""Utility functions for SVG Terminal Recorder."""

import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple, Union


def get_terminal_size(fd: Optional[int] = None) -> Tuple[int, int]:
    """Get the size of the terminal.
    
    Args:
        fd: File descriptor to check (default: stdout)
        
    Returns:
        Tuple of (columns, rows)
    """
    fd = fd or sys.stdout.fileno()
    try:
        import fcntl
        import termios
        import struct
        
        # Try to get terminal size using ioctl
        try:
            # This works on Unix-like systems
            h, w, _, _ = struct.unpack(
                'HHHH',
                fcntl.ioctl(fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
            )
            return w, h
        except (IOError, ImportError, struct.error):
            # Fall back to environment variables
            pass
    except ImportError:
        pass
    
    # Fall back to environment variables
    return (
        int(os.environ.get('COLUMNS', 80)),
        int(os.environ.get('LINES', 24))
    )


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
        
    Returns:
        Path to the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def tempfile_context(*args, **kwargs):
    """Context manager for creating a temporary file.
    
    Args:
        *args: Positional arguments passed to tempfile.NamedTemporaryFile
        **kwargs: Keyword arguments passed to tempfile.NamedTemporaryFile
        
    Yields:
        A file-like object for the temporary file
    """
    with tempfile.NamedTemporaryFile(*args, **kwargs) as f:
        yield f


def run_command(
    command: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command and return the result.
    
    Args:
        command: Command to run (as string or list of args)
        cwd: Working directory
        env: Environment variables
        check: If True, raise CalledProcessError on non-zero exit code
        
    Returns:
        CompletedProcess instance
    """
    if isinstance(command, str):
        command = [command]
    
    return subprocess.run(
        command,
        cwd=cwd,
        env=env or os.environ,
        check=check,
        text=True,
        capture_output=True,
    )


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {int(seconds)}s"


def parse_geometry(geometry: str) -> Tuple[int, int]:
    """Parse a geometry string into (width, height)."""
    try:
        width, height = map(int, geometry.lower().split("x"))
        if width <= 0 or height <= 0:
            raise ValueError("Dimensions must be positive")
        return width, height
    except (ValueError, AttributeError) as e:
        raise ValueError(
            f"Invalid geometry: {geometry}. Expected format: WIDTHxHEIGHT"
        ) from e


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Copy a file, creating parent directories if needed."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    if dst_path.is_dir():
        dst_path = dst_path / src_path.name
    
    ensure_directory(dst_path.parent)
    shutil.copy2(src_path, dst_path)
