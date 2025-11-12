"""
Dot Pattern Abstract Drawing
Generates pointillism-style abstract art from instance segmentation.
Each instance is represented by multiple small dots.
"""

from PIL import Image, ImageDraw
import math
import random


class DotPatternDrawer:
    """Draws dot-pattern abstract art from instance segmentation data."""

    def __init__(self, canvas_width: int = 1200, dot_size: int = 8, dot_density: float = 0.3):
        """
        Initialize drawer.

        Args:
            canvas_width: Canvas width in pixels
            dot_size: Diameter of each dot in pixels (default: 8)
            dot_density: Density of dots (0.1=sparse, 1.0=very dense)
        """
        self.canvas_width = canvas_width
        self.dot_size = dot_size
        self.dot_density = dot_density

    def _calculate_dot_count(self, proportion: float, canvas_area: float) -> int:
        """
        Calculate number of dots for an instance based on its proportion.

        Args:
            proportion: Area proportion (0-1)
            canvas_area: Total canvas area

        Returns:
            Number of dots to draw
        """
        # Calculate instance area
        instance_area = canvas_area * proportion

        # Calculate how many dots can fit (accounting for dot size)
        dot_area = math.pi * (self.dot_size / 2) ** 2
        max_dots = int(instance_area / dot_area * self.dot_density)

        # At least 3 dots for visible instances
        return max(3, max_dots)

    def _get_category_color(self, category: str) -> tuple[int, int, int]:
        """
        Get color for a category.

        Args:
            category: Category name

        Returns:
            RGB color tuple
        """
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
        return category_colors.get(category, (128, 128, 128))

    def _generate_dot_positions_random(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        num_dots: int
    ) -> list[tuple[float, float]]:
        """
        Generate random dot positions within a circular area.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Radius of the area
            num_dots: Number of dots to generate

        Returns:
            List of (x, y) positions
        """
        positions = []
        for _ in range(num_dots):
            # Random angle and distance
            angle = random.uniform(0, 2 * math.pi)
            # Use sqrt for uniform distribution in circle
            distance = radius * math.sqrt(random.uniform(0, 1))

            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            positions.append((x, y))

        return positions

    def _generate_dot_positions_grid(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        num_dots: int
    ) -> list[tuple[float, float]]:
        """
        Generate grid-pattern dot positions within a circular area.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Radius of the area
            num_dots: Number of dots to generate

        Returns:
            List of (x, y) positions
        """
        positions = []
        grid_size = int(math.sqrt(num_dots)) + 1
        spacing = (2 * radius) / grid_size

        for i in range(grid_size):
            for j in range(grid_size):
                if len(positions) >= num_dots:
                    break

                x = center_x - radius + i * spacing
                y = center_y - radius + j * spacing

                # Check if point is within circle
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist <= radius:
                    positions.append((x, y))

        return positions[:num_dots]

    def _generate_dot_positions_spiral(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        num_dots: int
    ) -> list[tuple[float, float]]:
        """
        Generate spiral-pattern dot positions.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Radius of the area
            num_dots: Number of dots to generate

        Returns:
            List of (x, y) positions
        """
        positions = []
        golden_angle = math.pi * (3 - math.sqrt(5))  # Golden angle in radians

        for i in range(num_dots):
            angle = i * golden_angle
            distance = radius * math.sqrt(i / num_dots)

            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            positions.append((x, y))

        return positions

    def draw(
        self,
        instance_data: dict,
        output_path: str,
        pattern: str = "random"
    ):
        """
        Draw dot-pattern abstract art from instance segmentation data.

        Args:
            instance_data: Instance segmentation data dictionary
            output_path: Output image path
            pattern: Dot pattern style ("random", "grid", or "spiral")
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

        # Select pattern generator
        if pattern == "grid":
            generate_positions = self._generate_dot_positions_grid
        elif pattern == "spiral":
            generate_positions = self._generate_dot_positions_spiral
        else:  # random
            generate_positions = self._generate_dot_positions_random

        # Draw dots for each instance (largest first, in background)
        for instance in reversed(instances):
            proportion = instance["proportion"]
            center = instance["center"]
            category = instance["category"]

            # Skip very small instances
            if proportion < 0.0005:  # Less than 0.05%
                continue

            # Calculate position and radius
            cx = center["x"] * self.canvas_width
            cy = center["y"] * canvas_height

            # Calculate area-based radius (for dot distribution)
            instance_area = canvas_area * proportion
            radius = math.sqrt(instance_area / math.pi)

            # Calculate number of dots
            num_dots = self._calculate_dot_count(proportion, canvas_area)

            # Get color
            color = self._get_category_color(category)

            # Generate dot positions
            positions = generate_positions(cx, cy, radius, num_dots)

            # Draw dots
            dot_radius = self.dot_size / 2
            for x, y in positions:
                bbox = [
                    x - dot_radius,
                    y - dot_radius,
                    x + dot_radius,
                    y + dot_radius
                ]
                draw.ellipse(bbox, fill=color, outline=color)

        # Save
        img.save(output_path)
        print(f"Dot-pattern abstract art saved to {output_path}")
        print(f"  Pattern style: {pattern}")
        print(f"  Dot size: {self.dot_size}px")
        print(f"  Dot density: {self.dot_density}")
