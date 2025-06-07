"""Data models and core business logic for SVG Terminal Recorder."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pyte.screens


class TerminalMode(Enum):
    """Terminal operating modes."""
    COOKED = auto()
    RAW = auto()


@dataclass
class TerminalConfig:
    """Configuration for terminal emulation."""
    columns: int = 80
    rows: int = 24
    mode: TerminalMode = TerminalMode.COOKED
    encoding: str = "utf-8"


@dataclass
class Frame:
    """A single frame of terminal output."""
    timestamp: float
    buffer: Dict[int, Dict[int, str]]  # row -> column -> character
    cursor: Optional[Tuple[int, int]] = None
    styles: Dict[Tuple[int, int], Dict[str, str]] = field(default_factory=dict)


@dataclass
class TerminalSession:
    """A recorded terminal session."""
    config: TerminalConfig
    frames: List[Frame] = field(default_factory=list)
    
    def add_frame(self, frame: Frame) -> None:
        """Add a frame to the session."""
        self.frames.append(frame)
    
    def to_asciicast(self, output_path: Union[str, Path]) -> None:
        """Export session to asciicast format."""
        # TODO: Implement asciicast export
        raise NotImplementedError
    
    @classmethod
    def from_asciicast(cls, input_path: Union[str, Path]) -> "TerminalSession":
        """Create a session from an asciicast file."""
        # TODO: Implement asciicast import
        raise NotImplementedError


class TerminalRecorder:
    """Records terminal output."""
    
    def __init__(self, config: Optional[TerminalConfig] = None):
        self.config = config or TerminalConfig()
        self.screen = pyte.Screen(
            self.config.columns,
            self.config.rows
        )
        self.stream = pyte.Stream(self.screen)
    
    def feed(self, data: bytes) -> Frame:
        """Feed data to the terminal and return the resulting frame."""
        self.stream.feed(data)
        # TODO: Capture the frame from the screen
        return Frame(timestamp=0.0, buffer={})


class SVGRenderer:
    """Renders terminal frames as SVG."""
    
    def __init__(self, template: str = "default"):
        self.template = template
    
    def render_frame(self, frame: Frame) -> str:
        """Render a single frame as SVG."""
        # TODO: Implement SVG rendering
        return ""
    
    def render_animation(
        self,
        frames: List[Frame],
        output_path: Union[str, Path],
        loop: bool = True,
        frame_delay: int = 100,
    ) -> None:
        """Render frames as an animated SVG."""
        # TODO: Implement animation rendering
        pass
