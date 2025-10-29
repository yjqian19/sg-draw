"""
Position-Based Extraction
Analyzes an image and identifies each object instance with its proportion and position.
Uses OpenRouter API for flexible model selection.
"""

import json
import base64
from pathlib import Path
from typing import Dict, Optional, Tuple
import os
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

# Load environment variables from .env file
load_dotenv()


class PositionExtractor:
    """Extracts object proportions and positions from images using OpenRouter API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        canvas_width: int = 1200
    ):
        """
        Initialize the extractor with OpenRouter API credentials.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model to use (defaults to MODEL env var or qwen/qwen3-vl-32b-instruct)
            canvas_width: Output canvas width in pixels (default: 1200)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENROUTER_API_KEY env var or pass api_key parameter."
            )

        self.model = model or os.getenv("MODEL", "qwen/qwen3-vl-32b-instruct")
        self.canvas_width = canvas_width
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def _get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        """
        Get original image dimensions.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (width, height)
        """
        with Image.open(image_path) as img:
            return img.size

    def _calculate_output_dimensions(self, original_width: int, original_height: int) -> Tuple[int, int]:
        """
        Calculate output dimensions maintaining aspect ratio.

        Args:
            original_width: Original image width
            original_height: Original image height

        Returns:
            Tuple of (output_width, output_height)
        """
        aspect_ratio = original_height / original_width
        output_height = int(self.canvas_width * aspect_ratio)
        return (self.canvas_width, output_height)

    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """
        Encode image to base64 for API submission.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (base64_data, media_type)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine media type
        suffix = path.suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(suffix, 'image/jpeg')

        # Read and encode
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        return image_data, media_type

    def extract(self, image_path: str) -> Dict:
        """
        Extract object proportions and positions from an image.

        Args:
            image_path: Path to the input image

        Returns:
            Position data dictionary with objects and their positions
        """
        # Get image dimensions
        orig_width, orig_height = self._get_image_dimensions(image_path)
        out_width, out_height = self._calculate_output_dimensions(orig_width, orig_height)

        image_data, media_type = self._encode_image(image_path)

        prompt = """Analyze this image and identify EVERY object instance with its visual area proportion and position.

Your response must be ONLY valid JSON (no markdown, no explanations).

Requirements:
1. List each object instance separately (if there are 8 windows, list 8 window entries)
2. Estimate the visual area proportion for each object (0.0 to 1.0)
3. Estimate the center position of each object as relative coordinates:
   - x: 0.0 (left edge) to 1.0 (right edge)
   - y: 0.0 (top edge) to 1.0 (bottom edge)
4. Use simple numeric IDs: "1", "2", "3", etc.

Format:
{
  "objects": [
    {
      "id": "1",
      "label": "sky",
      "proportion": 0.40,
      "position": {"x": 0.5, "y": 0.2}
    },
    {
      "id": "2",
      "label": "window",
      "proportion": 0.02,
      "position": {"x": 0.3, "y": 0.5}
    },
    {
      "id": "3",
      "label": "window",
      "proportion": 0.02,
      "position": {"x": 0.7, "y": 0.5}
    }
  ]
}

Guidelines:
- Be comprehensive - include all visible objects
- Proportions represent visual area coverage
- Position x,y represents the center point of each object
- Use clear, simple labels
- If there are multiple instances of the same object type, list each one separately with its own position

Return ONLY the JSON, nothing else."""

        print(f"  Using model: {self.model}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=4096,
            temperature=0.3
        )

        # Extract JSON from response
        response_text = response.choices[0].message.content
        if response_text is None:
            raise ValueError("Model returned None/empty response")

        response_text = response_text.strip()

        print(f"  Response length: {len(response_text)} characters")

        # Try to parse JSON, handling potential markdown wrapping
        if response_text.startswith('```'):
            # Remove markdown code blocks
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)

        try:
            position_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"\n[DEBUG] Failed to parse JSON. Error: {e}")
            print(f"[DEBUG] Model used: {self.model}")
            print(f"[DEBUG] Response length: {len(response_text)} characters")
            print(f"[DEBUG] Full raw response:\n{response_text}")
            raise ValueError(f"Failed to parse JSON response from model: {e}")

        # Validate structure
        if 'objects' not in position_data:
            raise ValueError("Invalid position data format returned by API")

        # Validate that each object has required fields
        for obj in position_data['objects']:
            if 'id' not in obj or 'label' not in obj or 'proportion' not in obj or 'position' not in obj:
                raise ValueError(f"Object missing required fields: {obj}")
            if 'x' not in obj['position'] or 'y' not in obj['position']:
                raise ValueError(f"Position missing x or y coordinate: {obj}")

        # Add image dimensions to the data
        position_data['image_dimensions'] = {
            'original': {'width': orig_width, 'height': orig_height},
            'output': {'width': out_width, 'height': out_height}
        }

        return position_data

    def save_position_data(self, position_data: Dict, output_path: str):
        """
        Save position data to JSON file.

        Args:
            position_data: Position data dictionary
            output_path: Path to save JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(position_data, f, indent=2)
        print(f"Position data saved to {output_path}")
