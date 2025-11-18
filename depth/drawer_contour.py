"""
Depth Contour Drawer
Generates contour lines (iso-depth lines) like topographic maps.
"""

from PIL import Image, ImageDraw
import numpy as np
import cv2


class DepthContourDrawer:
    """
    Draw contour lines connecting points of equal depth.

    Creates a topographic map-like visualization where each line
    represents a specific depth level.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        num_levels: int = 20,
        line_width: int = 2,
        color_mode: str = "depth",
        fill_contours: bool = False,
        min_contour_length: int = 20,
        blur_size: int = 15,
        contour_smoothness: float = 0.5
    ):
        """
        Initialize contour drawer.

        Args:
            canvas_width: Canvas width in pixels
            num_levels: Number of contour levels (depth slices)
            line_width: Width of contour lines in pixels
            color_mode: "depth" (colored by depth), "uniform" (single color),
                       or "rainbow" (full spectrum)
            fill_contours: If True, fill areas between contours
            min_contour_length: Minimum points in a contour to draw it
            blur_size: Gaussian blur kernel size (0 to disable, 5-31 for smoothing)
            contour_smoothness: Contour approximation epsilon (0=precise, 1-5=smooth)
        """
        self.canvas_width = canvas_width
        self.num_levels = num_levels
        self.line_width = line_width
        self.color_mode = color_mode
        self.fill_contours = fill_contours
        self.min_contour_length = min_contour_length
        self.blur_size = blur_size
        self.contour_smoothness = contour_smoothness

    def _depth_to_color(self, depth_value: float, total_levels: int, level_idx: int) -> tuple:
        """
        Convert depth level to color.

        Args:
            depth_value: Depth value [0, 1]
            total_levels: Total number of levels
            level_idx: Current level index

        Returns:
            RGB color tuple
        """
        if self.color_mode == "uniform":
            # Single dark color
            return (40, 40, 40)

        elif self.color_mode == "depth":
            # Blue (far) to red (near)
            if depth_value < 0.33:
                # Far: dark blue to cyan
                t = depth_value / 0.33
                r = int(0 * (1-t) + 0 * t)
                g = int(50 * (1-t) + 150 * t)
                b = int(150 * (1-t) + 200 * t)
            elif depth_value < 0.67:
                # Mid: cyan to yellow
                t = (depth_value - 0.33) / 0.34
                r = int(0 * (1-t) + 200 * t)
                g = int(150 * (1-t) + 200 * t)
                b = int(200 * (1-t) + 0 * t)
            else:
                # Near: yellow to red
                t = (depth_value - 0.67) / 0.33
                r = int(200 * (1-t) + 200 * t)
                g = int(200 * (1-t) + 50 * t)
                b = int(0 * (1-t) + 0 * t)
            return (r, g, b)

        elif self.color_mode == "rainbow":
            # Full rainbow spectrum
            hue = int((1 - depth_value) * 270)  # 270 degrees (blue to red)
            import colorsys
            rgb = colorsys.hsv_to_rgb(hue / 360.0, 0.8, 0.9)
            return tuple(int(c * 255) for c in rgb)

        else:
            return (100, 100, 100)

    def _depth_to_fill_color(self, depth_value: float) -> tuple:
        """
        Convert depth to fill color (lighter version for filled contours).

        Args:
            depth_value: Depth value [0, 1]

        Returns:
            RGBA color tuple with alpha
        """
        if self.color_mode == "depth":
            # Lighter, semi-transparent versions
            if depth_value < 0.33:
                r, g, b = 150, 200, 240
            elif depth_value < 0.67:
                r, g, b = 240, 240, 150
            else:
                r, g, b = 240, 180, 150
            return (r, g, b, 180)  # Semi-transparent
        else:
            # Light gray
            intensity = int(255 - depth_value * 100)
            return (intensity, intensity, intensity, 150)

    def draw(self, depth_data: dict, output_path: str):
        """
        Draw contour line visualization from depth data.

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

        print(f"\nGenerating depth contour map...")
        print(f"  Number of contour levels: {self.num_levels}")
        print(f"  Line width: {self.line_width}px")
        print(f"  Color mode: {self.color_mode}")
        print(f"  Fill contours: {self.fill_contours}")
        print(f"  Blur size: {self.blur_size}")
        print(f"  Contour smoothness: {self.contour_smoothness}")

        # Create canvas
        if self.fill_contours:
            # Use RGBA for transparency
            img = Image.new('RGBA', (self.canvas_width, canvas_height), (255, 255, 255, 255))
        else:
            img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Convert depth map to uint8 for OpenCV
        depth_uint8 = (depth_map_resized * 255).astype(np.uint8)

        # Apply Gaussian blur for smoother contours
        if self.blur_size > 0:
            # Ensure blur_size is odd
            blur_kernel = self.blur_size if self.blur_size % 2 == 1 else self.blur_size + 1
            depth_uint8 = cv2.GaussianBlur(depth_uint8, (blur_kernel, blur_kernel), 0)
            print(f"  Applied Gaussian blur with kernel size {blur_kernel}")

        # Generate contour levels
        levels = np.linspace(0, 255, self.num_levels + 2)[1:-1]  # Exclude 0 and 255

        print(f"  Extracting contours...")

        # Store contours for each level (for filled mode)
        all_contours = []

        # Extract and draw contours for each level
        for i, level in enumerate(levels):
            # Threshold at this level
            _, binary = cv2.threshold(depth_uint8, level, 255, cv2.THRESH_BINARY)

            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            # Calculate depth value for this level
            depth_value = level / 255.0

            # Get color for this depth level
            color = self._depth_to_color(depth_value, self.num_levels, i)

            # Draw each contour
            for contour in contours:
                # Skip very small contours (noise)
                if len(contour) < self.min_contour_length:
                    continue

                # Apply contour smoothing if requested
                if self.contour_smoothness > 0:
                    epsilon = self.contour_smoothness
                    contour = cv2.approxPolyDP(contour, epsilon, True)

                # Convert contour to list of tuples for PIL
                points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]

                if len(points) < 2:
                    continue

                # Draw contour line
                if len(points) == 2:
                    draw.line(points, fill=color, width=self.line_width)
                else:
                    # Draw as polygon outline
                    draw.line(points + [points[0]], fill=color, width=self.line_width)

                # Store for filled mode
                if self.fill_contours:
                    all_contours.append((depth_value, points))

            # Progress indicator
            if (i + 1) % 5 == 0:
                print(f"    {i + 1}/{len(levels)} levels processed...")

        # Fill contours if requested
        if self.fill_contours:
            print(f"  Filling {len(all_contours)} contour regions...")

            # Create a new layer for fills
            fill_layer = Image.new('RGBA', (self.canvas_width, canvas_height), (255, 255, 255, 0))
            fill_draw = ImageDraw.Draw(fill_layer)

            # Sort by depth (far to near) to draw background first
            all_contours.sort(key=lambda x: x[0])

            for depth_value, points in all_contours:
                if len(points) >= 3:
                    fill_color = self._depth_to_fill_color(depth_value)
                    fill_draw.polygon(points, fill=fill_color)

            # Composite fill layer under the line layer
            background = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
            background.paste(fill_layer, (0, 0), fill_layer)

            # Convert main image to RGBA if needed
            if img.mode == 'RGB':
                img = img.convert('RGBA')

            # Composite
            background.paste(img, (0, 0), img)
            img = background.convert('RGB')

        print(f"  Contour map complete!")

        # Save
        img.save(output_path)
        print(f"Depth contour map saved to {output_path}")


class DepthContourDrawerAdvanced:
    """
    Advanced contour drawer with more sophisticated rendering options.
    """

    def __init__(
        self,
        canvas_width: int = 1200,
        num_levels: int = 30,
        line_width: int = 1,
        style: str = "classic"
    ):
        """
        Initialize advanced contour drawer.

        Args:
            canvas_width: Canvas width in pixels
            num_levels: Number of contour levels
            line_width: Width of contour lines
            style: "classic" (topographic), "zebra" (alternating fill),
                   or "gradient" (smooth gradient with contours)
        """
        self.canvas_width = canvas_width
        self.num_levels = num_levels
        self.line_width = line_width
        self.style = style

    def draw(self, depth_data: dict, output_path: str):
        """
        Draw advanced contour visualization.

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

        print(f"\nGenerating advanced contour map (style: {self.style})...")

        if self.style == "gradient":
            # Smooth gradient with contour lines overlay
            # Convert depth to color gradient
            colored = np.zeros((canvas_height, self.canvas_width, 3), dtype=np.uint8)

            for i in range(canvas_height):
                for j in range(self.canvas_width):
                    d = depth_map_resized[i, j]
                    # Blue to red gradient
                    if d < 0.5:
                        t = d * 2
                        colored[i, j] = [0, int(t * 200), int((1-t) * 200 + t * 100)]
                    else:
                        t = (d - 0.5) * 2
                        colored[i, j] = [int(t * 200), int((1-t) * 200), 0]

            img = Image.fromarray(colored)
            draw = ImageDraw.Draw(img)

            # Overlay contour lines
            depth_uint8 = (depth_map_resized * 255).astype(np.uint8)
            levels = np.linspace(0, 255, self.num_levels + 2)[1:-1]

            for level in levels:
                _, binary = cv2.threshold(depth_uint8, level, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    if len(contour) >= 20:
                        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
                        if len(points) >= 2:
                            draw.line(points + [points[0]], fill=(40, 40, 40), width=self.line_width)

        elif self.style == "zebra":
            # Alternating filled regions
            img = Image.new('RGB', (self.canvas_width, canvas_height), (255, 255, 255))
            draw = ImageDraw.Draw(img)

            depth_uint8 = (depth_map_resized * 255).astype(np.uint8)
            levels = np.linspace(0, 255, self.num_levels + 2)[1:-1]

            for i, level in enumerate(levels):
                _, binary = cv2.threshold(depth_uint8, level, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

                # Alternate between filled and outlined
                fill_color = (230, 230, 230) if i % 2 == 0 else (255, 255, 255)
                line_color = (50, 50, 50)

                for contour in contours:
                    if len(contour) >= 20:
                        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
                        if len(points) >= 3:
                            draw.polygon(points, fill=fill_color, outline=line_color)

        else:  # classic
            # Standard topographic style
            img = Image.new('RGB', (self.canvas_width, canvas_height), (250, 245, 235))
            draw = ImageDraw.Draw(img)

            depth_uint8 = (depth_map_resized * 255).astype(np.uint8)
            levels = np.linspace(0, 255, self.num_levels + 2)[1:-1]

            for level in levels:
                _, binary = cv2.threshold(depth_uint8, level, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    if len(contour) >= 20:
                        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
                        if len(points) >= 2:
                            draw.line(points + [points[0]], fill=(100, 70, 50), width=self.line_width)

        # Save
        img.save(output_path)
        print(f"Advanced contour map saved to {output_path}")
