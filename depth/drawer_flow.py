"""
Depth Flow Field Drawer
Generates flow lines following depth gradients - creates a sense of spatial movement.
"""

from PIL import Image, ImageDraw
import numpy as np
import random
import math


class DepthFlowDrawer:
    """
    Draw flow lines that follow depth gradients.

    Lines flow from near to far (or vice versa), creating a dynamic
    visualization of spatial depth changes in the image.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        num_lines: int = 500,
        line_length: int = 100,
        line_width: int = 2,
        step_size: float = 3.0,
        flow_direction: str = "near_to_far",
        color_mode: str = "depth",
        seed_strategy: str = "random"
    ):
        """
        Initialize depth flow drawer.

        Args:
            canvas_width: Canvas width in pixels
            num_lines: Number of flow lines to draw
            line_length: Maximum number of steps per line
            line_width: Width of each line in pixels
            step_size: Distance of each step along gradient (pixels)
            flow_direction: "near_to_far" or "far_to_near"
            color_mode: "depth" (colored by depth), "gradient" (colored by gradient strength),
                       or "uniform" (single color)
            seed_strategy: "random", "grid", or "depth_based"
        """
        self.canvas_width = canvas_width
        self.num_lines = num_lines
        self.line_length = line_length
        self.line_width = line_width
        self.step_size = step_size
        self.flow_direction = flow_direction
        self.color_mode = color_mode
        self.seed_strategy = seed_strategy

    def _depth_to_color(self, depth_value: float) -> tuple:
        """
        Convert depth value to color.

        Args:
            depth_value: Depth in range [0, 1]

        Returns:
            RGB color tuple
        """
        # Color gradient from blue (far) to red (near)
        if depth_value < 0.33:
            # Far: blue to cyan
            t = depth_value / 0.33
            r = int(0 * (1-t) + 0 * t)
            g = int(0 * (1-t) + 200 * t)
            b = int(200 * (1-t) + 255 * t)
        elif depth_value < 0.67:
            # Mid: cyan to yellow
            t = (depth_value - 0.33) / 0.34
            r = int(0 * (1-t) + 255 * t)
            g = int(200 * (1-t) + 255 * t)
            b = int(255 * (1-t) + 0 * t)
        else:
            # Near: yellow to red
            t = (depth_value - 0.67) / 0.33
            r = int(255 * (1-t) + 255 * t)
            g = int(255 * (1-t) + 100 * t)
            b = int(0 * (1-t) + 100 * t)

        return (r, g, b)

    def _gradient_to_color(self, gradient_magnitude: float) -> tuple:
        """
        Convert gradient magnitude to color.

        Args:
            gradient_magnitude: Normalized gradient strength [0, 1]

        Returns:
            RGB color tuple
        """
        # From light gray (weak gradient) to dark gray (strong gradient)
        intensity = int(255 * (1 - gradient_magnitude * 0.8))
        return (intensity, intensity, intensity)

    def _generate_seed_points(
        self,
        canvas_width: int,
        canvas_height: int,
        depth_map: np.ndarray
    ) -> list:
        """
        Generate starting points for flow lines.

        Args:
            canvas_width, canvas_height: Canvas dimensions
            depth_map: Depth map array

        Returns:
            List of (x, y) tuples
        """
        seeds = []

        if self.seed_strategy == "random":
            # Completely random distribution
            for _ in range(self.num_lines):
                x = random.uniform(0, canvas_width - 1)
                y = random.uniform(0, canvas_height - 1)
                seeds.append((x, y))

        elif self.seed_strategy == "grid":
            # Regular grid pattern
            cols = int(math.sqrt(self.num_lines * canvas_width / canvas_height))
            rows = int(self.num_lines / cols) + 1

            for i in range(rows):
                for j in range(cols):
                    if len(seeds) >= self.num_lines:
                        break
                    x = (j + 0.5 + random.uniform(-0.3, 0.3)) * canvas_width / cols
                    y = (i + 0.5 + random.uniform(-0.3, 0.3)) * canvas_height / rows
                    seeds.append((x, y))

        elif self.seed_strategy == "depth_based":
            # Seed more densely in areas with high depth variation
            grad_y, grad_x = np.gradient(depth_map)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # Normalize
            grad_max = gradient_magnitude.max()
            if grad_max > 0:
                gradient_magnitude /= grad_max

            # Sample based on gradient magnitude
            h, w = depth_map.shape
            for _ in range(self.num_lines * 3):  # Try 3x, reject low-gradient areas
                if len(seeds) >= self.num_lines:
                    break

                x = random.uniform(0, canvas_width - 1)
                y = random.uniform(0, canvas_height - 1)

                # Map to depth map coordinates
                dx = int(x / canvas_width * w)
                dy = int(y / canvas_height * h)
                dx = min(max(dx, 0), w - 1)
                dy = min(max(dy, 0), h - 1)

                # Accept with probability proportional to gradient
                if random.random() < gradient_magnitude[dy, dx] ** 0.5:
                    seeds.append((x, y))

        return seeds

    def _trace_flow_line(
        self,
        start_x: float,
        start_y: float,
        grad_x: np.ndarray,
        grad_y: np.ndarray,
        depth_map: np.ndarray,
        canvas_width: int,
        canvas_height: int
    ) -> list:
        """
        Trace a single flow line following the gradient.

        Args:
            start_x, start_y: Starting position
            grad_x, grad_y: Gradient fields
            depth_map: Depth map
            canvas_width, canvas_height: Canvas dimensions

        Returns:
            List of (x, y, depth) tuples representing the flow line
        """
        points = []
        x, y = start_x, start_y
        h, w = depth_map.shape

        # Direction multiplier
        direction = 1 if self.flow_direction == "near_to_far" else -1

        for step in range(self.line_length):
            # Check bounds
            if x < 0 or x >= canvas_width or y < 0 or y >= canvas_height:
                break

            # Map to depth map coordinates
            dx = int(x / canvas_width * w)
            dy = int(y / canvas_height * h)
            dx = min(max(dx, 0), w - 1)
            dy = min(max(dy, 0), h - 1)

            # Get current depth
            depth = depth_map[dy, dx]
            points.append((x, y, depth))

            # Get gradient at current position
            gx = grad_x[dy, dx]
            gy = grad_y[dy, dx]

            # Gradient magnitude
            grad_mag = math.sqrt(gx**2 + gy**2)

            # Stop if gradient is too small (flat area)
            if grad_mag < 0.001:
                break

            # Normalize gradient
            gx /= grad_mag
            gy /= grad_mag

            # Move along gradient direction
            # Positive gradient = increasing depth (moving away)
            x += gx * self.step_size * direction
            y += gy * self.step_size * direction

            # Add some randomness for organic feel
            x += random.uniform(-0.5, 0.5)
            y += random.uniform(-0.5, 0.5)

        return points

    def draw(self, depth_data: dict, output_path: str):
        """
        Draw flow field visualization from depth data.

        Args:
            depth_data: Depth data dictionary from DepthExtractor
            output_path: Output image path
        """
        # Get depth map and dimensions
        depth_map = depth_data['depth_map']
        orig_width, orig_height = depth_data['original_size']

        # Calculate canvas dimensions
        aspect_ratio = orig_height / orig_width
        canvas_height = int(self.canvas_width * aspect_ratio)

        # Resize depth map to canvas size for accurate flow tracing
        from PIL import Image as PILImage
        depth_image = PILImage.fromarray((depth_map * 255).astype(np.uint8))
        depth_image_resized = depth_image.resize((self.canvas_width, canvas_height))
        depth_map_resized = np.array(depth_image_resized) / 255.0

        # Compute gradients
        grad_y, grad_x = np.gradient(depth_map_resized)

        # Create canvas
        img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        print(f"\nGenerating depth flow field...")
        print(f"  Number of flow lines: {self.num_lines}")
        print(f"  Flow direction: {self.flow_direction}")
        print(f"  Color mode: {self.color_mode}")
        print(f"  Seed strategy: {self.seed_strategy}")

        # Generate seed points
        seed_points = self._generate_seed_points(
            self.canvas_width, canvas_height, depth_map_resized
        )

        print(f"  Tracing flow lines...")

        # Draw each flow line
        for i, (start_x, start_y) in enumerate(seed_points):
            # Trace the flow line
            points = self._trace_flow_line(
                start_x, start_y,
                grad_x, grad_y,
                depth_map_resized,
                self.canvas_width, canvas_height
            )

            # Skip if line is too short
            if len(points) < 3:
                continue

            # Draw the line
            if self.color_mode == "depth":
                # Color by depth value
                for j in range(len(points) - 1):
                    x1, y1, d1 = points[j]
                    x2, y2, d2 = points[j + 1]
                    depth_avg = (d1 + d2) / 2
                    color = self._depth_to_color(depth_avg)
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=self.line_width)

            elif self.color_mode == "gradient":
                # Color by gradient strength
                for j in range(len(points) - 1):
                    x1, y1, _ = points[j]
                    x2, y2, _ = points[j + 1]

                    # Get gradient magnitude at this point
                    dx = int(x1 / self.canvas_width * grad_x.shape[1])
                    dy = int(y1 / canvas_height * grad_y.shape[0])
                    dx = min(max(dx, 0), grad_x.shape[1] - 1)
                    dy = min(max(dy, 0), grad_y.shape[0] - 1)

                    grad_mag = math.sqrt(grad_x[dy, dx]**2 + grad_y[dy, dx]**2)
                    grad_mag = min(grad_mag * 10, 1.0)  # Normalize and scale

                    color = self._gradient_to_color(grad_mag)
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=self.line_width)

            else:  # uniform
                # Single color
                color = (50, 50, 50)
                for j in range(len(points) - 1):
                    x1, y1, _ = points[j]
                    x2, y2, _ = points[j + 1]
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=self.line_width)

            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"    {i + 1}/{len(seed_points)} lines drawn...")

        print(f"  Flow field complete!")

        # Save
        img.save(output_path)
        print(f"Depth flow field saved to {output_path}")
