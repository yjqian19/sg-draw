"""
Position-Based Abstract Drawing Generation
Generates abstract drawings where shapes are positioned at their actual locations.
"""

import json
import math
import random
from typing import Dict, Tuple
from PIL import Image, ImageDraw


class PositionDrawer:
    """Generates position-based abstract drawings."""

    # Color palettes by category (same as other drawers)
    WARM_COLORS = [
        (255, 107, 107),  # coral red
        (255, 159, 64),   # orange
        (255, 205, 86),   # yellow
        (255, 140, 105),  # peach
        (239, 71, 111),   # pink
    ]

    COOL_COLORS = [
        (54, 162, 235),   # blue
        (75, 192, 192),   # teal
        (153, 102, 255),  # purple
        (100, 149, 237),  # cornflower
        (72, 201, 176),   # turquoise
    ]

    BRIGHT_COLORS = [
        (255, 99, 132),   # bright pink
        (255, 206, 86),   # bright yellow
        (75, 255, 107),   # lime
        (255, 0, 255),    # magenta
        (0, 255, 255),    # cyan
    ]

    NEUTRAL_COLORS = [
        (201, 203, 207),  # light gray
        (169, 169, 169),  # gray
        (211, 211, 211),  # light gray 2
        (192, 192, 192),  # silver
        (220, 220, 220),  # very light gray
    ]

    # Object category mappings
    LIVING_ENTITIES = {'person', 'man', 'woman', 'child', 'baby', 'dog', 'cat', 'bird', 'animal', 'human', 'people'}
    DEVICES = {'laptop', 'computer', 'phone', 'tablet', 'monitor', 'screen', 'keyboard', 'mouse', 'device', 'machine', 'tv', 'camera'}
    TOOLS = {'cup', 'mug', 'glass', 'bottle', 'fork', 'knife', 'spoon', 'pen', 'pencil', 'book', 'plate', 'bowl'}
    SURFACES = {'desk', 'table', 'floor', 'ground', 'wall', 'shelf', 'counter', 'surface', 'bed', 'sofa', 'chair'}

    def _categorize_object(self, label: str) -> str:
        """
        Categorize an object label into color groups.

        Args:
            label: Object label

        Returns:
            Category name: 'living', 'device', 'tool', or 'surface'
        """
        label_lower = label.lower()

        if label_lower in self.LIVING_ENTITIES:
            return 'living'
        elif label_lower in self.DEVICES:
            return 'device'
        elif label_lower in self.TOOLS:
            return 'tool'
        elif label_lower in self.SURFACES:
            return 'surface'
        else:
            # Default categorization by heuristics
            if any(word in label_lower for word in ['person', 'man', 'woman', 'animal']):
                return 'living'
            elif any(word in label_lower for word in ['desk', 'table', 'floor', 'wall']):
                return 'surface'
            else:
                return 'tool'

    def _assign_color(self, label: str) -> Tuple[int, int, int]:
        """
        Assign color based on object category.

        Args:
            label: Object label

        Returns:
            RGB color tuple
        """
        category = self._categorize_object(label)

        if category == 'living':
            return random.choice(self.WARM_COLORS)
        elif category == 'device':
            return random.choice(self.COOL_COLORS)
        elif category == 'tool':
            return random.choice(self.BRIGHT_COLORS)
        else:  # surface
            return random.choice(self.NEUTRAL_COLORS)

    def _assign_shape(self, label: str) -> str:
        """
        Assign shape based on object category.

        Args:
            label: Object label

        Returns:
            Shape name: 'circle', 'square', or 'rectangle'
        """
        category = self._categorize_object(label)

        if category == 'living':
            return 'circle'
        elif category == 'device':
            return 'rectangle'
        elif category == 'tool':
            return random.choice(['circle', 'square'])
        else:  # surface
            return 'rectangle'

    def _calculate_shape_dimensions(
        self,
        area: float,
        shape_type: str
    ) -> Tuple[float, float]:
        """
        Calculate shape dimensions from area.

        Args:
            area: Desired area for the shape
            shape_type: 'circle', 'square', or 'rectangle'

        Returns:
            Tuple of (width, height) or (diameter, diameter) for circle
        """
        if shape_type == 'circle':
            # Area = π * r²
            radius = math.sqrt(area / math.pi)
            diameter = radius * 2
            return (diameter, diameter)
        elif shape_type == 'square':
            # Area = side²
            side = math.sqrt(area)
            return (side, side)
        else:  # rectangle
            # Use aspect ratio of 1.5:1
            aspect_ratio = 1.5
            width = math.sqrt(area * aspect_ratio)
            height = area / width
            return (width, height)

    def _draw_shape(
        self,
        draw: ImageDraw.Draw,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Tuple[int, int, int],
        shape_type: str,
        label: str
    ):
        """
        Draw a shape on the canvas (no outline).

        Args:
            draw: PIL ImageDraw object
            x, y: Center position
            width, height: Shape dimensions
            color: RGB color tuple
            shape_type: 'circle', 'square', or 'rectangle'
            label: Object label for text
        """
        if shape_type == 'circle':
            radius = width / 2
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color
            )
        elif shape_type == 'square':
            side = width
            draw.rectangle(
                [x - side/2, y - side/2, x + side/2, y + side/2],
                fill=color
            )
        else:  # rectangle
            draw.rectangle(
                [x - width/2, y - height/2, x + width/2, y + height/2],
                fill=color
            )

        # Draw label
        bbox = draw.textbbox((0, 0), label)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.text(
            (x - text_width/2, y - text_height/2),
            label,
            fill=(0, 0, 0)
        )

    def draw(self, position_data: Dict, output_path: str):
        """
        Generate abstract drawing from position data.

        Args:
            position_data: Position data dictionary
            output_path: Path to save output image
        """
        # Get canvas dimensions from position data
        canvas_width = position_data['image_dimensions']['output']['width']
        canvas_height = position_data['image_dimensions']['output']['height']
        canvas_area = canvas_width * canvas_height

        # Create canvas
        img = Image.new('RGB', (canvas_width, canvas_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        objects = position_data['objects']

        # Pre-assign colors and shapes for each unique label
        # This ensures all objects with same label have same color and shape
        label_styles = {}
        for obj in objects:
            label = obj['label']
            if label not in label_styles:
                # Assign once per unique label
                label_styles[label] = {
                    'color': self._assign_color(label),
                    'shape': self._assign_shape(label)
                }

        # Draw each object at its position
        for obj in objects:
            label = obj['label']
            proportion = obj['proportion']
            pos_x = obj['position']['x']  # Relative position (0-1)
            pos_y = obj['position']['y']  # Relative position (0-1)

            # Get consistent color and shape for this label
            color = label_styles[label]['color']
            shape_type = label_styles[label]['shape']

            # Calculate area and dimensions based on individual proportion
            area = canvas_area * proportion
            shape_width, shape_height = self._calculate_shape_dimensions(area, shape_type)

            # Convert relative position to absolute coordinates
            abs_x = pos_x * canvas_width
            abs_y = pos_y * canvas_height

            # Draw shape centered at position
            self._draw_shape(
                draw, abs_x, abs_y,
                shape_width, shape_height,
                color, shape_type, label
            )

        # Save
        img.save(output_path)
        print(f"Position-based abstract drawing saved to {output_path}")

    def draw_from_file(self, position_path: str, output_path: str):
        """
        Generate abstract drawing from position JSON file.

        Args:
            position_path: Path to position data JSON
            output_path: Path to save output image
        """
        with open(position_path, 'r') as f:
            position_data = json.load(f)

        self.draw(position_data, output_path)
