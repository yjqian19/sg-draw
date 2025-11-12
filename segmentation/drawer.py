"""
Segmentation-Based Abstract Drawing
Draws colored circles based on segmentation analysis.
"""

from PIL import Image, ImageDraw
import math


class SegmentationDrawer:
    """Draws circle-based abstract art from segmentation data."""

    def __init__(self, canvas_width: int = 1200):
        """
        Initialize drawer.

        Args:
            canvas_width: Canvas width in pixels
        """
        self.canvas_width = canvas_width

    def _get_color(self, label: str) -> tuple[int, int, int]:
        """
        Get color for a label.

        Args:
            label: Label name

        Returns:
            RGB color tuple
        """
        # Simple hash-based color generation
        hash_val = hash(label)
        r = (hash_val & 0xFF0000) >> 16
        g = (hash_val & 0x00FF00) >> 8
        b = hash_val & 0x0000FF

        # Ensure colors are not too dark
        r = max(r, 80)
        g = max(g, 80)
        b = max(b, 80)

        return (r, g, b)

    def _calculate_radius(self, proportion: float, canvas_area: float) -> float:
        """
        Calculate circle radius from proportion.

        Args:
            proportion: Area proportion (0-1)
            canvas_area: Total canvas area

        Returns:
            Circle radius in pixels
        """
        # Circle area = π * r²
        # r = sqrt(area / π)
        circle_area = canvas_area * proportion
        radius = math.sqrt(circle_area / math.pi)
        return radius

    def draw(self, instance_data: dict, output_path: str):
        """
        Draw abstract art from instance segmentation data.
        Each instance gets its own circle, colored by category.

        Args:
            instance_data: Instance segmentation data dictionary
            output_path: Output image path
        """
        # Get dimensions
        orig_width = instance_data["image_dimensions"]["width"]
        orig_height = instance_data["image_dimensions"]["height"]

        # Calculate canvas size (maintain aspect ratio)
        aspect_ratio = orig_height / orig_width
        canvas_height = int(self.canvas_width * aspect_ratio)
        canvas_area = self.canvas_width * canvas_height

        # Create white canvas
        img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        instances = instance_data["instances"]

        # Define category-based colors (same as in extractor)
        category_colors = {
            "person": (255, 100, 100),
            "bicycle": (100, 255, 100),
            "car": (100, 100, 255),
            "motorcycle": (255, 255, 100),
            "bus": (255, 100, 255),
            "truck": (100, 255, 255),
            "traffic light": (255, 165, 0),
            "stop sign": (255, 0, 0),
            "bird": (255, 192, 203),
            "cat": (255, 140, 0),
            "dog": (210, 105, 30),
            "backpack": (128, 0, 128),
            "umbrella": (0, 128, 128),
            "handbag": (139, 69, 19),
        }

        # Draw circles (largest first, in background)
        for instance in reversed(instances):
            proportion = instance["proportion"]
            center = instance["center"]
            category = instance["category"]

            # Calculate circle position
            cx = center["x"] * self.canvas_width
            cy = center["y"] * canvas_height

            # Calculate radius
            radius = self._calculate_radius(proportion, canvas_area)

            # Get color based on category
            color = category_colors.get(category, (128, 128, 128))

            # Draw circle
            bbox = [
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius
            ]
            draw.ellipse(bbox, fill=color, outline=color)

        # Save
        img.save(output_path)
        print(f"Abstract art saved to {output_path}")
