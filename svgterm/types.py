"""Type definitions for svgterm."""
from typing import Dict, List, NamedTuple, Optional, Tuple, Union, Literal, TypedDict
from typing_extensions import Protocol

# Type aliases
Color = str
RGB = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]
ColorType = Union[Color, RGB, RGBA]
TemplateName = str
Template = str

# Terminal geometry: (columns, rows)
Geometry = Tuple[int, int]

# Frame timing in milliseconds
Milliseconds = int

class CharacterCell(NamedTuple):
    """Represents a single character cell in the terminal."""
    char: str
    fg: Optional[ColorType] = None
    bg: Optional[ColorType] = None
    bold: bool = False
    italics: bool = False
    underline: bool = False
    strikethrough: bool = False

class TimedFrame(NamedTuple):
    """A terminal frame with timing information."""
    time: Milliseconds
    duration: Milliseconds
    buffer: Dict[int, Dict[int, CharacterCell]]

class TemplateConfig(TypedDict, total=False):
    """Configuration for SVG templates."""
    name: str
    content: str
    description: str

class AnimationConfig(TypedDict, total=False):
    """Configuration for animation rendering."""
    min_frame_duration: Milliseconds
    max_frame_duration: Optional[Milliseconds]
    loop_delay: Milliseconds

class Renderer(Protocol):
    """Protocol for renderer implementations."""
    def render_animation(
        self,
        frames: List[TimedFrame],
        geometry: Geometry,
        output_path: str,
        template: Union[TemplateName, Template],
    ) -> None: ...

    def render_still_frames(
        self,
        frames: List[TimedFrame],
        geometry: Geometry,
        output_dir: str,
        template: Union[TemplateName, Template],
    ) -> None: ...
