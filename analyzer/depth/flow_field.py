"""
Flow field analyzer - Compute flow field from depth maps and export data
"""

import json
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt


class FlowFieldAnalyzer:
    """
    Analyze flow field from depth data.

    Computes gradient field (U, V) from depth maps, generates preview visualizations,
    and exports data for frontend use.
    """

    def __init__(self, canvas_width: int = 1200):
        """
        Initialize flow field analyzer.

        Args:
            canvas_width: Canvas width for resizing (default: 1200)
        """
        self.canvas_width = canvas_width

    def _compute_flow_field(self, depth_map: np.ndarray, blur_size: int = 15) -> dict:
        """
        Compute flow field from depth map.

        Args:
            depth_map: 2D depth array [0, 1]
            blur_size: Gaussian blur kernel size

        Returns:
            dict containing:
                - 'U': X direction gradient (numpy array)
                - 'V': Y direction gradient (numpy array)
                - 'speed': Gradient magnitude (numpy array)
                - 'depth_map': Processed depth map (numpy array)
        """
        # Apply Gaussian blur for smoother gradients
        if blur_size > 0:
            blur_kernel = blur_size if blur_size % 2 == 1 else blur_size + 1
            depth_blurred = cv2.GaussianBlur(depth_map, (blur_kernel, blur_kernel), 0)
        else:
            depth_blurred = depth_map

        # Compute gradient using Sobel operator
        grad_x = cv2.Sobel(depth_blurred, cv2.CV_64F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(depth_blurred, cv2.CV_64F, 0, 1, ksize=5)

        # Negative gradient: flow from high (shallow) to low (deep) depth
        U = -grad_x
        V = -grad_y

        # Compute speed (gradient magnitude)
        speed = np.sqrt(U**2 + V**2)

        return {
            'U': U,
            'V': V,
            'speed': speed,
            'depth_map': depth_map
        }

    def compute_from_depth_data(self, depth_data: dict, blur_size: int = 15) -> dict:
        """
        Compute flow field from depth data dictionary.

        Args:
            depth_data: Dictionary from DepthExtractor.extract()
            blur_size: Gaussian blur kernel size

        Returns:
            dict: Flow field data (U, V, speed, depth_map)
        """
        depth_map = depth_data['depth_map']
        orig_width, orig_height = depth_data['original_size']

        # Resize depth map to canvas size
        aspect_ratio = orig_height / orig_width
        canvas_height = int(self.canvas_width * aspect_ratio)

        depth_image = Image.fromarray((depth_map * 255).astype(np.uint8))
        depth_image_resized = depth_image.resize((self.canvas_width, canvas_height))
        depth_map_resized = np.array(depth_image_resized).astype(np.float32) / 255.0

        print(f"Computing flow field...")
        print(f"  Canvas: {self.canvas_width}x{canvas_height}")
        print(f"  Blur size: {blur_size}")

        return self._compute_flow_field(depth_map_resized, blur_size)

    def compute_from_depth_image(self, depth_image_path: str, blur_size: int = 15) -> dict:
        """
        Compute flow field from saved depth map image file.

        Args:
            depth_image_path: Path to depth map image (PNG)
            blur_size: Gaussian blur kernel size

        Returns:
            dict: Flow field data (U, V, speed, depth_map)
        """
        print(f"Loading depth map from: {depth_image_path}")

        # Load depth image
        depth_img = Image.open(depth_image_path).convert('L')
        depth_array = np.array(depth_img)

        # Normalize to [0, 1]
        depth_normalized = depth_array.astype(np.float32) / 255.0

        print(f"Computing flow field from depth image...")
        print(f"  Image size: {depth_img.size[0]}x{depth_img.size[1]}")
        print(f"  Blur size: {blur_size}")

        return self._compute_flow_field(depth_normalized, blur_size)

    def visualize_gradient(self, flow_data: dict, output_path: str, scale: float = 20.0):
        """
        Generate gradient visualization preview (arrow plot).

        Args:
            flow_data: Flow field data from compute_* methods
            output_path: Output image path
            scale: Arrow scale factor (default: 20.0)
        """
        U = flow_data['U']
        V = flow_data['V']
        height, width = U.shape

        print(f"Generating gradient preview...")
        print(f"  Size: {width}x{height}")
        print(f"  Arrow scale: {scale}")

        # Create figure
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)  # Inverted Y axis
        ax.set_aspect('equal')
        ax.axis('off')

        # Create mesh grid
        Y, X = np.mgrid[0:height, 0:width]

        # Downsample for cleaner visualization
        step = max(1, min(width, height) // 50)
        X_sub = X[::step, ::step]
        Y_sub = Y[::step, ::step]
        U_sub = U[::step, ::step]
        V_sub = V[::step, ::step]

        # Draw quiver plot
        ax.quiver(
            X_sub, Y_sub, U_sub, V_sub,
            scale=scale,
            width=0.003,
            headwidth=3,
            headlength=4,
            headaxislength=3,
            color='#1e88e5',
            alpha=0.7
        )

        # Remove margins
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)

        # Save
        plt.savefig(output_path, dpi=100, bbox_inches='tight', pad_inches=0,
                   facecolor='white', edgecolor='none')
        plt.close(fig)

        print(f"Gradient preview saved to: {output_path}")

    def export_json(self, flow_data: dict, depth_data: dict, output_path: str):
        """
        Export flow field data as JSON for frontend use.

        Args:
            flow_data: Flow field data from compute_* methods
            depth_data: Depth data dictionary (for depth map)
            output_path: Output JSON file path
        """
        U = flow_data['U']
        V = flow_data['V']
        depth_map = flow_data['depth_map']

        height, width = U.shape

        print(f"Exporting flow field data...")
        print(f"  Size: {width}x{height}")

        # Prepare data (convert numpy arrays to lists)
        data = {
            'width': int(width),
            'height': int(height),
            'depth': depth_map.tolist(),
            'U': U.tolist(),
            'V': V.tolist()
        }

        # Save JSON
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f)

        print(f"Flow field data exported to: {output_path}")


def main():
    """Command line interface for standalone use."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Compute flow field from depth map image'
    )
    parser.add_argument(
        '--depth-image',
        required=True,
        help='Path to depth map image file'
    )
    parser.add_argument(
        '--blur-size',
        type=int,
        default=15,
        help='Gaussian blur kernel size (default: 15)'
    )
    parser.add_argument(
        '--preview',
        help='Output path for gradient preview image'
    )
    parser.add_argument(
        '--export',
        help='Output path for JSON data'
    )
    parser.add_argument(
        '--output', '-o',
        default='output/analyzer',
        help='Output directory (default: output/analyzer)'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = FlowFieldAnalyzer()

    # Compute flow field
    flow_data = analyzer.compute_from_depth_image(
        args.depth_image,
        blur_size=args.blur_size
    )

    # Generate preview if requested
    if args.preview:
        analyzer.visualize_gradient(flow_data, args.preview)
    elif not args.export:
        # Default preview path if only --export is not specified
        depth_path = Path(args.depth_image)
        default_preview = Path(args.output) / f"{depth_path.stem}_gradient_map.png"
        analyzer.visualize_gradient(flow_data, str(default_preview))

    # Export JSON if requested
    if args.export:
        depth_data = {'depth_map': flow_data['depth_map']}
        analyzer.export_json(flow_data, depth_data, args.export)
    else:
        # Default export path
        depth_path = Path(args.depth_image)
        default_export = Path(args.output) / f"{depth_path.stem}_flow_field.json"
        depth_data = {'depth_map': flow_data['depth_map']}
        analyzer.export_json(flow_data, depth_data, str(default_export))


if __name__ == '__main__':
    main()
