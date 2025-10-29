"""
Component 1: Scene Graph Extraction
Analyzes an image and produces a structured scene graph with objects and relationships.
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
import anthropic
import os


class SceneGraphExtractor:
    """Extracts scene graphs from images using vision models."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the extractor with API credentials.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY or pass api_key parameter.")

        self.client = anthropic.Anthropic(api_key=self.api_key)

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
        Extract scene graph from an image.

        Args:
            image_path: Path to the input image

        Returns:
            Scene graph dictionary with 'objects' and 'relations'
        """
        image_data, media_type = self._encode_image(image_path)

        prompt = """Analyze this image and produce a structured scene graph in JSON format.

Your response must be ONLY valid JSON (no markdown, no explanations).

Identify all significant objects in the image and their spatial/functional relationships.

Format:
{
  "objects": [
    {"id": "o1", "label": "person"},
    {"id": "o2", "label": "laptop"}
  ],
  "relations": [
    {"subject": "o1", "predicate": "using", "object": "o2"}
  ]
}

Guidelines:
- Use clear object labels (person, dog, car, tree, building, cup, phone, etc.)
- Use intuitive predicates: on_top_of, next_to, holding, using, wearing, inside, in_front_of, behind, above, below
- Include 3-10 objects (most prominent)
- Include all meaningful relationships between objects
- Use simple IDs: o1, o2, o3, etc.

Return ONLY the JSON, nothing else."""

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        # Extract JSON from response
        response_text = message.content[0].text.strip()

        # Try to parse JSON, handling potential markdown wrapping
        if response_text.startswith('```'):
            # Remove markdown code blocks
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)

        scene_graph = json.loads(response_text)

        # Validate structure
        if 'objects' not in scene_graph or 'relations' not in scene_graph:
            raise ValueError("Invalid scene graph format returned by API")

        return scene_graph

    def save_scene_graph(self, scene_graph: Dict, output_path: str):
        """
        Save scene graph to JSON file.

        Args:
            scene_graph: Scene graph dictionary
            output_path: Path to save JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(scene_graph, f, indent=2)
        print(f"Scene graph saved to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python scene_graph_extractor.py <image_path> [output_json_path]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "scene_graph.json"

    extractor = SceneGraphExtractor()
    scene_graph = extractor.extract(image_path)
    extractor.save_scene_graph(scene_graph, output_path)

    print("\nExtracted Scene Graph:")
    print(json.dumps(scene_graph, indent=2))
