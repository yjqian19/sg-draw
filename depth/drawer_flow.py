"""
Depth Flow Drawer
Generates flow field visualization from depth maps, showing how water would flow
from shallow to deep regions.
"""

from PIL import Image, ImageDraw
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


class DepthFlowDrawer:
    """
    Draw flow field visualization from depth data.

    Generates streamlines showing the direction of flow from shallow (high values)
    to deep (low values) regions, like water flowing downhill.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        density: float = 2.0,
        line_width: float = 1.0,
        blur_size: int = 15,
        color_mode: str = "depth",
        max_length: float = 4.0,
        arrow_size: float = 1.0,
        integration_steps: int = 2000,
        step_size: float = 0.01,
        variable_width: bool = True,
        min_width: float = 0.3,
        max_width: float = 2.5
    ):
        """
        Initialize flow drawer.

        Args:
            canvas_width: Canvas width in pixels
            density: Flow line density (1.0=default, 3.0=dense like 100 contours)
            line_width: Base width of flow lines (used if variable_width=False)
            blur_size: Gaussian blur kernel size (0 to disable, 5-80 for smoothing)
            color_mode: "depth" (colored by depth), "speed" (by gradient magnitude),
                       "uniform" (single color), or "rainbow"
            max_length: Maximum length of streamlines in axes coordinates
            arrow_size: Size of arrow indicators (0 to disable arrows)
            integration_steps: Max steps for manual integration
            step_size: Step size for manual integration
            variable_width: If True, line width varies with depth (thin=shallow, thick=deep)
            min_width: Minimum line width for shallowest areas
            max_width: Maximum line width for deepest areas
        """
        self.canvas_width = canvas_width
        self.density = density
        self.line_width = line_width
        self.blur_size = blur_size
        self.color_mode = color_mode
        self.max_length = max_length
        self.arrow_size = arrow_size
        self.integration_steps = integration_steps
        self.step_size = step_size
        self.variable_width = variable_width
        self.min_width = min_width
        self.max_width = max_width

    def _compute_gradient(self, depth_map: np.ndarray) -> tuple:
        """
        Compute gradient of depth map.

        Args:
            depth_map: 2D depth array [0, 1]

        Returns:
            (U, V): Gradient components (flow direction)
        """
        # Apply Gaussian blur for smoother gradients
        if self.blur_size > 0:
            blur_kernel = self.blur_size if self.blur_size % 2 == 1 else self.blur_size + 1
            depth_blurred = cv2.GaussianBlur(depth_map, (blur_kernel, blur_kernel), 0)
        else:
            depth_blurred = depth_map

        # Compute gradient using Sobel operator (more accurate than np.gradient)
        grad_x = cv2.Sobel(depth_blurred, cv2.CV_64F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(depth_blurred, cv2.CV_64F, 0, 1, ksize=5)

        # Negative gradient: flow from high (shallow) to low (deep) depth
        U = -grad_x
        V = -grad_y

        return U, V

    def _depth_to_color(self, depth_value: float) -> tuple:
        """
        Convert depth value to color.

        Args:
            depth_value: Depth value [0, 1]

        Returns:
            RGB color tuple
        """
        if self.color_mode == "uniform":
            return (40, 40, 40)

        elif self.color_mode == "depth":
            # Blue (far) to red (near)
            if depth_value < 0.33:
                t = depth_value / 0.33
                r = int(0 * (1-t) + 0 * t)
                g = int(50 * (1-t) + 150 * t)
                b = int(150 * (1-t) + 200 * t)
            elif depth_value < 0.67:
                t = (depth_value - 0.33) / 0.34
                r = int(0 * (1-t) + 200 * t)
                g = int(150 * (1-t) + 200 * t)
                b = int(200 * (1-t) + 0 * t)
            else:
                t = (depth_value - 0.67) / 0.33
                r = int(200 * (1-t) + 200 * t)
                g = int(200 * (1-t) + 50 * t)
                b = int(0 * (1-t) + 0 * t)
            return (r, g, b)

        elif self.color_mode == "rainbow":
            import colorsys
            hue = int((1 - depth_value) * 270)
            rgb = colorsys.hsv_to_rgb(hue / 360.0, 0.8, 0.9)
            return tuple(int(c * 255) for c in rgb)

        else:
            return (100, 100, 100)

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

        # Resize depth map to canvas size
        from PIL import Image as PILImage
        depth_image = PILImage.fromarray((depth_map * 255).astype(np.uint8))
        depth_image_resized = depth_image.resize((self.canvas_width, canvas_height))
        depth_map_resized = np.array(depth_image_resized).astype(np.float32) / 255.0

        print(f"\nGenerating depth flow field...")
        print(f"  Canvas: {self.canvas_width}x{canvas_height}")
        print(f"  Density: {self.density}")
        print(f"  Line width: {self.line_width}px")
        print(f"  Blur size: {self.blur_size}")
        print(f"  Color mode: {self.color_mode}")

        # Compute gradient (flow direction)
        print(f"  Computing flow field gradients...")
        U, V = self._compute_gradient(depth_map_resized)

        # Create mesh grid
        height, width = depth_map_resized.shape
        Y, X = np.mgrid[0:height, 0:width]

        # Compute flow speed (gradient magnitude)
        speed = np.sqrt(U**2 + V**2)

        print(f"  Generating streamlines...")

        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(self.canvas_width/100, canvas_height/100), dpi=100)
        # Set coordinate system to match image coordinate system
        ax.set_xlim(0, width)  # X: left to right
        ax.set_ylim(height, 0)  # Y: top to bottom (inverted from matplotlib default)
        ax.set_aspect('equal')
        ax.axis('off')

        # Set white background
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Prepare color data based on mode
        if self.color_mode == "speed":
            color_data = speed
            cmap = 'viridis'
        elif self.color_mode == "depth":
            # Apply non-linear transformation to emphasize deep areas
            depth_inv = 1.0 - depth_map_resized  # 0=shallow, 1=deep
            # Use power function to make color changes more dramatic in deep areas
            color_data = 1.0 - np.power(depth_inv, 1.5)  # Transform back to original range
            # Custom colormap: green (shallow/high depth) -> blue (deep/low depth)
            from matplotlib.colors import LinearSegmentedColormap
            colors = ['#0a4a7a', '#1e88e5', '#42a5f5', '#81c784', '#aed581', '#c5e1a5']  # deep blue -> light green
            n_bins = 256
            cmap = LinearSegmentedColormap.from_list('depth_green_blue', colors, N=n_bins)
        elif self.color_mode == "rainbow":
            color_data = depth_map_resized
            cmap = 'rainbow'
        else:  # uniform
            color_data = np.ones_like(depth_map_resized) * 0.5
            cmap = 'gray'

        # Variable line width based on depth with non-linear mapping
        if self.variable_width:
            # Thin lines in shallow areas (high depth values ~1.0)
            # Thick lines in deep areas (low depth values ~0.0)
            # Use power function to make changes more dramatic in deep areas
            depth_inv = 1.0 - depth_map_resized  # 0=shallow, 1=deep
            # Higher power = more dramatic changes in deep areas
            width_factor = np.power(depth_inv, 2.2)  # Increased from 1.5 to 2.2 for more dramatic effect
            linewidth = self.min_width + (self.max_width - self.min_width) * width_factor
        else:
            linewidth = self.line_width

        # Draw streamlines
        if self.arrow_size > 0:
            # With arrows
            strm = ax.streamplot(
                X[0, :], Y[:, 0], U, V,
                density=self.density,
                color=color_data,
                linewidth=linewidth,
                cmap=cmap,
                arrowsize=self.arrow_size,
                arrowstyle='->',
                maxlength=self.max_length,
                integration_direction='forward'
            )
        else:
            # No arrows - cleaner look
            strm = ax.streamplot(
                X[0, :], Y[:, 0], U, V,
                density=self.density,
                color=color_data,
                linewidth=linewidth,
                cmap=cmap,
                arrowsize=0,
                maxlength=self.max_length,
                integration_direction='forward'
            )

        print(f"  Rendering image...")

        # Remove margins
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)

        # Save figure
        plt.savefig(output_path, dpi=100, bbox_inches='tight', pad_inches=0,
                   facecolor='white', edgecolor='none')
        plt.close(fig)

        print(f"Depth flow field saved to {output_path}")


class DepthFlowDrawerManual:
    """
    Manual flow line drawer with custom streamline integration.

    Provides more control over streamline generation, allowing for very long
    lines and custom styling.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        num_lines: int = 500,
        line_length: int = 1000,
        line_width: float = 1.5,
        blur_size: int = 15,
        color_mode: str = "depth",
        step_size: float = 2.0,
        min_speed: float = 0.001
    ):
        """
        Initialize manual flow drawer.

        Args:
            canvas_width: Canvas width in pixels
            num_lines: Number of flow lines to generate
            line_length: Maximum points per flow line
            line_width: Width of flow lines
            blur_size: Gaussian blur kernel size
            color_mode: Color scheme
            step_size: Integration step size (pixels)
            min_speed: Minimum gradient magnitude to continue line
        """
        self.canvas_width = canvas_width
        self.num_lines = num_lines
        self.line_length = line_length
        self.line_width = line_width
        self.blur_size = blur_size
        self.color_mode = color_mode
        self.step_size = step_size
        self.min_speed = min_speed

    def _compute_gradient(self, depth_map: np.ndarray) -> tuple:
        """Compute gradient of depth map."""
        if self.blur_size > 0:
            blur_kernel = self.blur_size if self.blur_size % 2 == 1 else self.blur_size + 1
            depth_blurred = cv2.GaussianBlur(depth_map, (blur_kernel, blur_kernel), 0)
        else:
            depth_blurred = depth_map

        grad_x = cv2.Sobel(depth_blurred, cv2.CV_64F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(depth_blurred, cv2.CV_64F, 0, 1, ksize=5)

        U = -grad_x
        V = -grad_y

        return U, V

    def _integrate_streamline(self, x0: float, y0: float, U: np.ndarray,
                            V: np.ndarray, visited: np.ndarray) -> list:
        """
        Integrate a streamline starting from (x0, y0).

        Uses simple Euler integration with adaptive stepping.

        Args:
            x0, y0: Starting position
            U, V: Gradient field
            visited: Mask of visited pixels

        Returns:
            List of (x, y) points along streamline
        """
        height, width = U.shape
        points = [(x0, y0)]
        x, y = x0, y0

        for _ in range(self.line_length):
            # Get integer coordinates for array indexing
            ix, iy = int(x), int(y)

            # Check bounds
            if ix < 0 or ix >= width - 1 or iy < 0 or iy >= height - 1:
                break

            # Check if already visited
            if visited[iy, ix]:
                break

            # Mark as visited
            visited[iy, ix] = True

            # Bilinear interpolation of gradient
            fx, fy = x - ix, y - iy
            u = (1 - fx) * (1 - fy) * U[iy, ix] + \
                fx * (1 - fy) * U[iy, ix + 1] + \
                (1 - fx) * fy * U[iy + 1, ix] + \
                fx * fy * U[iy + 1, ix + 1]
            v = (1 - fx) * (1 - fy) * V[iy, ix] + \
                fx * (1 - fy) * V[iy, ix + 1] + \
                (1 - fx) * fy * V[iy + 1, ix] + \
                fx * fy * V[iy + 1, ix + 1]

            # Check speed
            speed = np.sqrt(u**2 + v**2)
            if speed < self.min_speed:
                break

            # Normalize and step
            u /= (speed + 1e-8)
            v /= (speed + 1e-8)

            x += u * self.step_size
            y += v * self.step_size

            points.append((x, y))

        return points if len(points) > 10 else []

    def _depth_to_color(self, depth_value: float) -> tuple:
        """Convert depth value to RGB color."""
        if self.color_mode == "uniform":
            return (40, 40, 40)

        elif self.color_mode == "depth":
            if depth_value < 0.33:
                t = depth_value / 0.33
                r = int(0 * (1-t) + 0 * t)
                g = int(50 * (1-t) + 150 * t)
                b = int(150 * (1-t) + 200 * t)
            elif depth_value < 0.67:
                t = (depth_value - 0.33) / 0.34
                r = int(0 * (1-t) + 200 * t)
                g = int(150 * (1-t) + 200 * t)
                b = int(200 * (1-t) + 0 * t)
            else:
                t = (depth_value - 0.67) / 0.33
                r = int(200 * (1-t) + 200 * t)
                g = int(200 * (1-t) + 50 * t)
                b = int(0 * (1-t) + 0 * t)
            return (r, g, b)

        else:
            return (100, 100, 100)

    def draw(self, depth_data: dict, output_path: str):
        """
        Draw flow field using manual streamline integration.

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

        # Resize depth map
        from PIL import Image as PILImage
        depth_image = PILImage.fromarray((depth_map * 255).astype(np.uint8))
        depth_image_resized = depth_image.resize((self.canvas_width, canvas_height))
        depth_map_resized = np.array(depth_image_resized).astype(np.float32) / 255.0

        print(f"\nGenerating depth flow field (manual integration)...")
        print(f"  Canvas: {self.canvas_width}x{canvas_height}")
        print(f"  Number of lines: {self.num_lines}")
        print(f"  Max line length: {self.line_length} steps")
        print(f"  Step size: {self.step_size}px")

        # Compute gradient
        print(f"  Computing gradients...")
        U, V = self._compute_gradient(depth_map_resized)

        height, width = depth_map_resized.shape

        # Create canvas
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img, 'RGBA')

        # Visited mask to avoid overlapping lines
        visited = np.zeros((height, width), dtype=bool)

        # Generate starting points
        print(f"  Generating streamlines...")

        # Use stratified sampling for better coverage
        grid_size = int(np.sqrt(self.num_lines))
        x_points = np.linspace(0, width - 1, grid_size)
        y_points = np.linspace(0, height - 1, grid_size)

        # Add random jitter
        np.random.seed(42)
        starting_points = []
        for x in x_points:
            for y in y_points:
                jitter_x = np.random.uniform(-width / grid_size / 2, width / grid_size / 2)
                jitter_y = np.random.uniform(-height / grid_size / 2, height / grid_size / 2)
                sx = np.clip(x + jitter_x, 0, width - 1)
                sy = np.clip(y + jitter_y, 0, height - 1)
                starting_points.append((sx, sy))

        lines_drawn = 0
        for i, (x0, y0) in enumerate(starting_points[:self.num_lines]):
            # Integrate streamline
            points = self._integrate_streamline(x0, y0, U, V, visited)

            if len(points) > 10:
                # Get depth at starting point for coloring
                depth_val = depth_map_resized[int(y0), int(x0)]
                color = self._depth_to_color(depth_val)

                # Draw line
                draw.line(points, fill=color + (200,), width=int(self.line_width))
                lines_drawn += 1

            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"    {i + 1}/{len(starting_points)} seeds processed, {lines_drawn} lines drawn...")

        print(f"  Total lines drawn: {lines_drawn}")
        print(f"  Saving image...")

        # Save
        img.save(output_path)
        print(f"Depth flow field saved to {output_path}")
