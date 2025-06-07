"""Social card generation for SVG Terminal Recorder.

This module provides functionality to generate dynamic social media preview cards
for terminal recordings using Vercel Edge Functions and WebAssembly.
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Optional, Union, Tuple

import httpx
from pydantic import BaseModel, HttpUrl

class SocialCardConfig(BaseModel):
    """Configuration for social card generation."""
    title: str
    description: Optional[str] = None
    theme: str = "default"
    width: int = 1200
    height: int = 630
    bg_color: str = "#1a1b26"
    text_color: str = "#a9b1d6"
    accent_color: str = "#7aa2f7"
    font_family: str = "JetBrains Mono, monospace"
    code: Optional[str] = None
    code_language: str = "bash"
    show_terminal: bool = True
    terminal_theme: str = "material"

class SocialCardGenerator:
    """Generate social media preview cards for terminal recordings."""
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        """Initialize the social card generator.
        
        Args:
            api_key: API key for the social card service
            endpoint: Custom endpoint URL for the social card service
        """
        self.api_key = api_key or os.getenv("SVGTERM_SOCIAL_API_KEY")
        self.endpoint = endpoint or "https://social-cards.vercel.app/api/generate"
    
    async def generate(
        self,
        config: Union[SocialCardConfig, Dict],
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """Generate a social card image.
        
        Args:
            config: Configuration for the social card
            output_path: Optional path to save the generated image
            
        Returns:
            Bytes of the generated image (PNG format)
        """
        if isinstance(config, dict):
            config = SocialCardConfig(**config)
        
        # Prepare the request payload
        payload = config.dict(exclude_none=True)
        
        # Make the API request
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            image_data = response.content
        
        # Save the image if output path is provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_data)
        
        return image_data
    
    def generate_sync(
        self,
        config: Union[SocialCardConfig, Dict],
        output_path: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """Synchronous version of generate."""
        import asyncio
        
        return asyncio.run(self.generate(config, output_path))

# Helper function for CLI usage
def generate_social_card(
    title: str,
    output_path: Union[str, Path],
    description: Optional[str] = None,
    code: Optional[str] = None,
    theme: str = "default",
    **kwargs
) -> None:
    """Generate a social card with the given configuration.
    
    Args:
        title: Title text for the card
        output_path: Path to save the generated image
        description: Optional description text
        code: Optional code snippet to include
        theme: Color theme for the card
        **kwargs: Additional arguments for SocialCardConfig
    """
    config = SocialCardConfig(
        title=title,
        description=description,
        code=code,
        theme=theme,
        **kwargs
    )
    
    generator = SocialCardGenerator()
    generator.generate_sync(config, output_path)
