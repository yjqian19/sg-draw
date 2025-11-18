"""
Depth estimation extractor using Hugging Face models
"""

from transformers import pipeline
from PIL import Image
import numpy as np
from pathlib import Path


class DepthExtractor:
    """
    Extract depth maps from images using pre-trained depth estimation models.

    Supported models:
    - depth-anything/Depth-Anything-V2-Small-hf (default, fast)
    - depth-anything/Depth-Anything-V2-Base-hf (better quality)
    - depth-anything/Depth-Anything-V2-Large-hf (best quality)
    - Intel/dpt-hybrid-midas (classic choice)
    """

    def __init__(self, model_name="depth-anything/Depth-Anything-V2-Small-hf"):
        """
        Initialize depth estimator.

        Args:
            model_name: HuggingFace model name for depth estimation
        """
        self.model_name = model_name
        self.pipe = None

    def load_model(self):
        """Load the depth estimation model (lazy loading)"""
        if self.pipe is None:
            print(f"Loading depth estimation model: {self.model_name}")
            self.pipe = pipeline("depth-estimation", model=self.model_name)
            print("Model loaded successfully!")

    def extract(self, image_path: str) -> dict:
        """
        Extract depth map from an image.

        Args:
            image_path: Path to input image

        Returns:
            dict containing:
                - 'depth_map': numpy array (H, W) with normalized depth values [0, 1]
                - 'depth_image': PIL Image of the depth visualization
                - 'original_size': (width, height) of original image
                - 'min_depth': minimum depth value
                - 'max_depth': maximum depth value
                - 'mean_depth': mean depth value
        """
        self.load_model()

        # Load image
        image = Image.open(image_path).convert('RGB')
        original_size = image.size

        print(f"Processing image: {Path(image_path).name} ({original_size[0]}x{original_size[1]})")

        # Run depth estimation
        result = self.pipe(image)

        # Process depth map
        depth_map = self._process_depth_map(result)

        # Calculate statistics
        stats = {
            'depth_map': depth_map,
            'depth_image': result['depth'],
            'original_size': original_size,
            'min_depth': float(depth_map.min()),
            'max_depth': float(depth_map.max()),
            'mean_depth': float(depth_map.mean()),
        }

        print(f"Depth extraction complete:")
        print(f"  Min depth: {stats['min_depth']:.4f}")
        print(f"  Max depth: {stats['max_depth']:.4f}")
        print(f"  Mean depth: {stats['mean_depth']:.4f}")

        return stats

    def _process_depth_map(self, result):
        """
        Process raw depth estimation result into normalized array.

        Args:
            result: Output from the depth estimation pipeline

        Returns:
            numpy array with depth values normalized to [0, 1]
        """
        # Convert PIL Image to numpy array
        depth_array = np.array(result['depth'])

        # Normalize to [0, 1] range
        depth_min = depth_array.min()
        depth_max = depth_array.max()

        if depth_max > depth_min:
            depth_normalized = (depth_array - depth_min) / (depth_max - depth_min)
        else:
            # Edge case: uniform depth
            depth_normalized = np.zeros_like(depth_array, dtype=np.float32)

        return depth_normalized

    def save_depth_map(self, depth_data: dict, output_path: str):
        """
        Save depth map visualization to file.

        Args:
            depth_data: Dictionary returned by extract()
            output_path: Path where to save the depth map image
        """
        depth_image = depth_data['depth_image']
        depth_image.save(output_path)
        print(f"Depth map saved to: {output_path}")

    def get_depth_at_point(self, depth_data: dict, x: int, y: int) -> float:
        """
        Get depth value at specific pixel coordinates.

        Args:
            depth_data: Dictionary returned by extract()
            x: X coordinate (horizontal)
            y: Y coordinate (vertical)

        Returns:
            Depth value at (x, y) in range [0, 1]
        """
        depth_map = depth_data['depth_map']
        h, w = depth_map.shape

        # Clamp coordinates to valid range
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))

        return float(depth_map[y, x])

    def compute_depth_gradient(self, depth_data: dict) -> tuple:
        """
        Compute depth gradients (useful for detecting edges and perspective lines).

        Args:
            depth_data: Dictionary returned by extract()

        Returns:
            tuple of (gradient_x, gradient_y) as numpy arrays
        """
        depth_map = depth_data['depth_map']

        # Compute gradients using numpy
        gradient_y, gradient_x = np.gradient(depth_map)

        return gradient_x, gradient_y
