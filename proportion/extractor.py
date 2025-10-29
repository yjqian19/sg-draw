"""
Proportion Extraction
Analyzes an image and identifies each object instance with its visual area proportion.
Uses OpenRouter API for flexible model selection.
"""

import json
import base64
from pathlib import Path
from typing import Dict, Optional
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ProportionExtractor:
    """Extracts object proportions from images using OpenRouter API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic/claude-3.5-sonnet"
    ):
        """
        Initialize the extractor with OpenRouter API credentials.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model to use (default: anthropic/claude-3.5-sonnet)
                   Examples:
                   - anthropic/claude-3.5-sonnet
                   - openai/gpt-4o
                   - google/gemini-pro-1.5
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENROUTER_API_KEY env var or pass api_key parameter."
            )

        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

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
        Extract object proportions from an image.

        Args:
            image_path: Path to the input image

        Returns:
            Proportion data dictionary with list of objects
        """
        image_data, media_type = self._encode_image(image_path)

        prompt = """Analyze this image and identify EVERY object instance with its visual area proportion.

Your response must be ONLY valid JSON (no markdown, no explanations).

Requirements:
1. List each object instance separately (if there are 8 windows, list 8 window entries)
2. Estimate the visual area proportion for each object (0.0 to 1.0)
3. All proportions should sum to approximately 1.0
4. Use simple numeric IDs: "1", "2", "3", etc.

Format:
{
  "objects": [
    {"id": "1", "label": "sky", "proportion": 0.40},
    {"id": "2", "label": "building", "proportion": 0.35},
    {"id": "3", "label": "window", "proportion": 0.02},
    {"id": "4", "label": "window", "proportion": 0.02}
  ]
}

Guidelines:
- Be comprehensive - include all visible objects
- Proportions represent visual area coverage (not importance)
- Use clear, simple labels
- If there are multiple instances of the same object type, list each one separately
- Each object should have its individual proportion

Return ONLY the JSON, nothing else."""

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
            ]
        )

        # Extract JSON from response
        response_text = response.choices[0].message.content.strip()

        # Try to parse JSON, handling potential markdown wrapping
        if response_text.startswith('```'):
            # Remove markdown code blocks
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)

        proportion_data = json.loads(response_text)

        # Validate structure
        if 'objects' not in proportion_data:
            raise ValueError("Invalid proportion data format returned by API")

        # Validate that each object has required fields
        for obj in proportion_data['objects']:
            if 'id' not in obj or 'label' not in obj or 'proportion' not in obj:
                raise ValueError(f"Object missing required fields: {obj}")

        return proportion_data

    def save_proportion_data(self, proportion_data: Dict, output_path: str):
        """
        Save proportion data to JSON file.

        Args:
            proportion_data: Proportion data dictionary
            output_path: Path to save JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(proportion_data, f, indent=2)
        print(f"Proportion data saved to {output_path}")
