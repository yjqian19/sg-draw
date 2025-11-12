"""
Flower/Plant Pattern Drawing
Generates abstract art using organic flower/plant-like patterns.
Dots are distributed along petal-like branches radiating from instance centers.
"""

from PIL import Image, ImageDraw
import math
import random
import numpy as np


class FlowerDrawer:
    """Draws flower/plant-like patterns from instance segmentation data."""

    def __init__(
        self,
        canvas_width: int = 1200,
        dot_size: int = 6,
        petals: int = 6,
        dots_per_petal: int = 80,
        petal_length_ratio: float = 0.8,
        petal_curve: float = 0.3,
        randomness: float = 0.2,
        size_multiplier: float = 2.0,
        petal_width: float = 0.4
    ):
        """
        Initialize flower drawer.

        Args:
            canvas_width: Canvas width in pixels
            dot_size: Diameter of each dot in pixels (default: 6)
            petals: Number of petals/branches per flower (default: 6)
            dots_per_petal: Number of dots along each petal (default: 80)
            petal_length_ratio: Petal length relative to instance size (default: 0.8)
            petal_curve: How curved the petals are, 0-1 (default: 0.3)
            randomness: Random variation in dot positions, 0-1 (default: 0.2)
            size_multiplier: Overall size multiplier for flowers (default: 2.0)
            petal_width: Width of petals relative to length (default: 0.4)
        """
        self.canvas_width = canvas_width
        self.dot_size = dot_size
        self.petals = petals
        self.dots_per_petal = dots_per_petal
        self.petal_length_ratio = petal_length_ratio
        self.petal_curve = petal_curve
        self.randomness = randomness
        self.size_multiplier = size_multiplier
        self.petal_width = petal_width

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

    def _calculate_petal_point(
        self,
        center_x: float,
        center_y: float,
        petal_angle: float,
        distance: float,
        max_distance: float
    ) -> tuple[float, float]:
        """
        Calculate a point along a petal curve.

        Args:
            center_x, center_y: Flower center
            petal_angle: Angle of this petal
            distance: Distance along petal (0 to max_distance)
            max_distance: Maximum petal length

        Returns:
            (x, y) coordinates of the point
        """
        # Normalize distance (0 to 1)
        t = distance / max_distance

        # Add curvature using Bezier-like curve
        # Start straight, curve out, then back
        curve_offset = self.petal_curve * max_distance * math.sin(t * math.pi)

        # Calculate radial position
        r = distance
        angle = petal_angle + curve_offset / (max_distance + 1) * 0.5

        # Add some width variation (thicker at base, thinner at tip)
        width_variation = (1 - t**0.5) * self.randomness * 20
        angle += random.uniform(-width_variation, width_variation) * 0.01

        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)

        return x, y

    def _draw_flower(
        self,
        draw: ImageDraw.Draw,
        instance: dict,
        canvas_width: int,
        canvas_height: int,
        color: tuple[int, int, int]
    ):
        """
        Draw a single flower for an instance.

        Args:
            draw: PIL ImageDraw object
            instance: Instance data dict
            canvas_width, canvas_height: Canvas dimensions
            color: Flower color
        """
        # Instance center
        cx = instance["center"]["x"] * canvas_width
        cy = instance["center"]["y"] * canvas_height
        proportion = instance["proportion"]

        # Calculate flower size based on instance proportion
        canvas_area = canvas_width * canvas_height
        flower_radius = math.sqrt(canvas_area * proportion / math.pi) * self.petal_length_ratio

        # Apply size multiplier
        flower_radius *= self.size_multiplier

        # Minimum and maximum flower size (increased)
        flower_radius = max(flower_radius, 40)
        flower_radius = min(flower_radius, 600)

        dot_radius = self.dot_size / 2.0

        # Draw center dot (pistil) - larger and more prominent
        center_radius = dot_radius * 2.5
        bbox = [cx - center_radius, cy - center_radius,
                cx + center_radius, cy + center_radius]
        draw.ellipse(bbox, fill=color, outline=color)

        # Random rotation for this flower (0 to 2π)
        flower_rotation = random.uniform(0, 2 * math.pi)

        # Draw petals - fill the petal area with dots
        for petal_idx in range(self.petals):
            # Base angle for this petal + random rotation
            petal_angle = (2 * math.pi * petal_idx / self.petals) + flower_rotation + random.uniform(-0.1, 0.1)

            # Calculate angular width of petal (in radians)
            # This creates the "wedge" shape
            petal_angular_width = self.petal_width * math.pi / self.petals

            # Draw dots to fill the petal area
            for dot_idx in range(self.dots_per_petal):
                # Distance from center (0 to flower_radius)
                # Not uniform - more dots near base
                t = (dot_idx + 1) / self.dots_per_petal

                # Add randomness to distance for more organic look
                distance_variation = random.uniform(0.85, 1.15)
                distance = flower_radius * t * distance_variation

                # Skip if too close to center (avoid overlap with center dot)
                if distance < flower_radius * 0.1:
                    continue

                # Angular position within the petal wedge
                # Narrower at tip, wider at base
                max_angle_offset = petal_angular_width * (1 - t**0.6) * 0.5
                angle_offset = random.uniform(-max_angle_offset, max_angle_offset)

                # Final angle with curve
                angle = petal_angle + angle_offset

                # Add curve to the petal
                curve_offset = self.petal_curve * math.sin(t * math.pi) * 0.3
                angle += curve_offset

                # Calculate position
                x = cx + distance * math.cos(angle)
                y = cy + distance * math.sin(angle)

                # Add jitter for natural look
                jitter = self.randomness * self.dot_size * 2
                x += random.uniform(-jitter, jitter)
                y += random.uniform(-jitter, jitter)

                # Vary dot size (larger at base, smaller at tip)
                size_scale = 1.3 - t * 0.3
                dot_r = dot_radius * size_scale

                # Draw dot
                bbox = [x - dot_r, y - dot_r, x + dot_r, y + dot_r]
                draw.ellipse(bbox, fill=color, outline=color)

    def draw(self, instance_data: dict, output_path: str):
        """
        Draw flower-pattern abstract art from instance segmentation data.

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

        # Create white canvas
        img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        instances = instance_data["instances"]

        print(f"\nGenerating flower pattern...")
        print(f"  Petals per flower: {self.petals}")
        print(f"  Dots per petal: {self.dots_per_petal}")
        print(f"  Dot size: {self.dot_size}px")
        print(f"  Petal curve: {self.petal_curve}")
        print(f"  Randomness: {self.randomness}")
        print(f"  Total flowers: {len(instances)}")

        # Safety check
        if len(instances) == 0:
            print("  Warning: No instances found, creating blank canvas")
            img.save(output_path)
            return

        # Draw flowers (largest first, in background)
        sorted_instances = sorted(instances, key=lambda x: x["proportion"], reverse=True)

        for idx, instance in enumerate(sorted_instances):
            category = instance["category"]
            color = self._get_category_color(category)

            self._draw_flower(
                draw, instance, self.canvas_width, canvas_height, color
            )

            if (idx + 1) % 10 == 0:
                print(f"    Drew {idx + 1}/{len(instances)} flowers...")

        print(f"  Drew {len(instances)} flowers")

        # Save
        img.save(output_path)
        print(f"Flower-pattern art saved to {output_path}")


class OrganicFlowerDrawer:
    """
    More organic flower drawer with branching and varied petal shapes.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        dot_size: int = 3,
        style: str = "daisy",  # "daisy", "sunflower", "spiral", "fern"
        density: float = 1.0
    ):
        """
        Initialize organic flower drawer.

        Args:
            canvas_width: Canvas width in pixels
            dot_size: Diameter of each dot in pixels
            style: Flower style preset
            density: Dot density multiplier
        """
        self.canvas_width = canvas_width
        self.dot_size = dot_size
        self.style = style
        self.density = density

        # Style presets
        self.style_configs = {
            "daisy": {
                "petals": 8,
                "dots_per_petal": 40,
                "petal_curve": 0.1,
                "randomness": 0.15
            },
            "sunflower": {
                "petals": 13,
                "dots_per_petal": 60,
                "petal_curve": 0.4,
                "randomness": 0.3
            },
            "spiral": {
                "petals": 21,  # Fibonacci
                "dots_per_petal": 30,
                "petal_curve": 0.8,
                "randomness": 0.1
            },
            "fern": {
                "petals": 5,
                "dots_per_petal": 80,
                "petal_curve": 0.6,
                "randomness": 0.25
            }
        }

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

    def draw(self, instance_data: dict, output_path: str):
        """
        Draw organic flower-pattern art.

        Args:
            instance_data: Instance segmentation data dictionary
            output_path: Output image path
        """
        # Get style config
        config = self.style_configs.get(self.style, self.style_configs["daisy"])

        # Create base drawer with style settings
        base_drawer = FlowerDrawer(
            canvas_width=self.canvas_width,
            dot_size=self.dot_size,
            petals=config["petals"],
            dots_per_petal=int(config["dots_per_petal"] * self.density),
            petal_curve=config["petal_curve"],
            randomness=config["randomness"]
        )

        print(f"Using '{self.style}' flower style")
        base_drawer.draw(instance_data, output_path)
