"""
Density Field Abstract Drawing
Generates abstract art using density field approach.
Randomly scatter dots across entire canvas, with density influenced by instance centers.
"""

from PIL import Image, ImageDraw
import math
import random
import numpy as np


class DensityFieldDrawer:
    """Draws density-field abstract art from instance segmentation data."""

    def __init__(
        self,
        canvas_width: int = 1200,
        dot_size: int = 4,
        total_dots: int = 10000,
        influence_radius: float = 200,
        concentration: float = 2.0
    ):
        """
        Initialize drawer.

        Args:
            canvas_width: Canvas width in pixels
            dot_size: Diameter of each dot in pixels (default: 4)
            total_dots: Total number of dots to scatter (default: 10000)
            influence_radius: Radius of influence for each instance (default: 200)
            concentration: Density falloff exponent (default: 2.0)
                Higher = steeper falloff = more concentrated near center
                Range: 1.0 (gradual) to 4.0+ (very steep)
        """
        self.canvas_width = canvas_width
        self.dot_size = dot_size
        self.total_dots = total_dots
        self.influence_radius = influence_radius
        self.concentration = concentration

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

    def _calculate_density_at_point(
        self,
        x: float,
        y: float,
        instances: list,
        canvas_width: int,
        canvas_height: int
    ) -> tuple[float, tuple[int, int, int]]:
        """
        Calculate density and color at a given point based on nearby instances.

        Args:
            x, y: Point coordinates
            instances: List of instance data
            canvas_width, canvas_height: Canvas dimensions

        Returns:
            Tuple of (density value 0-1, color)
        """
        max_density = 0
        dominant_color = (200, 200, 200)  # Default gray

        for instance in instances:
            # Instance center in canvas coordinates
            cx = instance["center"]["x"] * canvas_width
            cy = instance["center"]["y"] * canvas_height

            # Distance to instance center
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)

            # Calculate influence based on distance and instance proportion
            # Larger instances have stronger influence
            proportion = instance["proportion"]

            # Influence radius scaled by proportion (larger instances = larger influence)
            scaled_radius = self.influence_radius * (1 + proportion * 5)

            # Avoid division by zero
            if scaled_radius < 1:
                scaled_radius = 1

            if dist < scaled_radius:
                # Density decreases with distance
                # Higher concentration = steeper falloff
                density = (1 - (dist / scaled_radius)**self.concentration) * proportion * 10

                if density > max_density:
                    max_density = density
                    dominant_color = self._get_category_color(instance["category"])

        return min(max_density, 1.0), dominant_color

    def draw(self, instance_data: dict, output_path: str):
        """
        Draw density-field abstract art from instance segmentation data.

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

        # Create white canvas
        img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        instances = instance_data["instances"]

        print(f"\nGenerating density field...")
        print(f"  Total dots to scatter: {self.total_dots}")
        print(f"  Dot size: {self.dot_size}px")
        print(f"  Influence radius: {self.influence_radius}px")
        print(f"  Concentration: {self.concentration}")

        # Scatter dots randomly across canvas
        dots_drawn = 0
        attempts = 0
        max_attempts = self.total_dots * 5  # Try up to 5x to get desired number

        dot_radius = self.dot_size / 2.0

        # Safety check
        if len(instances) == 0:
            print("  Warning: No instances found, creating blank canvas")
            img.save(output_path)
            return

        while dots_drawn < self.total_dots and attempts < max_attempts:
            attempts += 1

            # Random position
            x = random.uniform(0, self.canvas_width - 1)
            y = random.uniform(0, canvas_height - 1)

            # Calculate density and color at this point
            density, color = self._calculate_density_at_point(
                x, y, instances, self.canvas_width, canvas_height
            )

            # Decide whether to draw this dot based on density
            # Higher density = higher probability
            if random.random() < density:
                # Draw dot
                bbox = [
                    x - dot_radius,
                    y - dot_radius,
                    x + dot_radius,
                    y + dot_radius
                ]
                draw.ellipse(bbox, fill=color, outline=color)
                dots_drawn += 1

                # Progress indicator
                if dots_drawn % 1000 == 0:
                    print(f"    {dots_drawn}/{self.total_dots} dots drawn...")

        print(f"  Drew {dots_drawn} dots in {attempts} attempts")

        # Save
        img.save(output_path)
        print(f"Density-field abstract art saved to {output_path}")


class DensityFieldDrawerAdvanced:
    """
    Advanced density field drawer with gradient effects.
    Uses a more sophisticated approach with pre-computed density fields.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        dot_size: int = 3,
        grid_size: int = 100,
        dot_density: float = 0.5
    ):
        """
        Initialize advanced drawer.

        Args:
            canvas_width: Canvas width in pixels
            dot_size: Diameter of each dot in pixels
            grid_size: Grid resolution for density calculation
            dot_density: Overall density multiplier (0.1-2.0)
        """
        self.canvas_width = canvas_width
        self.dot_size = dot_size
        self.grid_size = grid_size
        self.dot_density = dot_density

    def _get_category_color(self, category: str) -> tuple[int, int, int]:
        """Get color for a category."""
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

    def _build_density_field(
        self,
        instances: list,
        canvas_width: int,
        canvas_height: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Pre-compute density field and color field.

        Returns:
            Tuple of (density_field, color_field)
        """
        print(f"  Building density field (grid: {self.grid_size}x{self.grid_size})...")

        # Create grids
        density_field = np.zeros((self.grid_size, self.grid_size))
        color_field = np.zeros((self.grid_size, self.grid_size, 3), dtype=np.uint8)

        # Grid cell size
        cell_width = canvas_width / self.grid_size
        cell_height = canvas_height / self.grid_size

        # For each grid cell
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Cell center position
                x = (j + 0.5) * cell_width
                y = (i + 0.5) * cell_height

                max_density = 0
                dominant_color = np.array([200, 200, 200], dtype=np.uint8)

                # Check influence from each instance
                for instance in instances:
                    cx = instance["center"]["x"] * canvas_width
                    cy = instance["center"]["y"] * canvas_height
                    proportion = instance["proportion"]

                    # Distance to instance
                    dist = math.sqrt((x - cx)**2 + (y - cy)**2)

                    # Influence radius proportional to instance size
                    radius = 200 * (1 + proportion * 5)

                    # Avoid division by zero
                    if radius < 1:
                        radius = 1

                    if dist < radius:
                        # Gaussian-like falloff
                        density = math.exp(-(dist / radius)**2) * proportion * 20

                        if density > max_density:
                            max_density = density
                            color = self._get_category_color(instance["category"])
                            dominant_color = np.array(color, dtype=np.uint8)

                density_field[i, j] = min(max_density, 1.0)
                color_field[i, j] = dominant_color

        return density_field, color_field

    def draw(self, instance_data: dict, output_path: str):
        """
        Draw advanced density-field abstract art.

        Args:
            instance_data: Instance segmentation data dictionary
            output_path: Output image path
        """
        # Get dimensions
        orig_width = instance_data["image_dimensions"]["width"]
        orig_height = instance_data["image_dimensions"]["height"]

        # Calculate canvas size
        aspect_ratio = orig_height / orig_width
        canvas_height = int(self.canvas_width * aspect_ratio)

        # Create canvas
        img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        instances = instance_data["instances"]

        print(f"\nGenerating advanced density field...")

        # Build density field
        density_field, color_field = self._build_density_field(
            instances, self.canvas_width, canvas_height
        )

        # Calculate total dots based on canvas size and density
        total_dots = int(self.canvas_width * canvas_height * self.dot_density / 100)
        print(f"  Scattering {total_dots} dots...")

        dot_radius = self.dot_size / 2
        dots_drawn = 0

        # Safety check
        if len(instances) == 0:
            print("  Warning: No instances found, creating blank canvas")
            img.save(output_path)
            return

        # Scatter dots
        for attempt in range(total_dots * 3):  # Try 3x to account for rejections
            if dots_drawn >= total_dots:
                break

            # Random position
            x = random.uniform(0, self.canvas_width - 1)
            y = random.uniform(0, canvas_height - 1)

            # Find corresponding grid cell
            grid_x = int(x / self.canvas_width * self.grid_size)
            grid_y = int(y / canvas_height * self.grid_size)
            grid_x = min(max(grid_x, 0), self.grid_size - 1)
            grid_y = min(max(grid_y, 0), self.grid_size - 1)

            # Get density and color from field
            density = density_field[grid_y, grid_x]
            color = tuple(color_field[grid_y, grid_x])

            # Draw dot with probability based on density
            if random.random() < density:
                bbox = [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius]
                draw.ellipse(bbox, fill=color, outline=color)
                dots_drawn += 1

                # Progress indicator
                if dots_drawn % 1000 == 0:
                    print(f"    {dots_drawn}/{total_dots} dots drawn...")

        print(f"  Drew {dots_drawn} dots")

        # Save
        img.save(output_path)
        print(f"Advanced density-field art saved to {output_path}")
