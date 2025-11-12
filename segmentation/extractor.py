"""
Instance Segmentation Extraction
Uses Mask2Former model from Hugging Face for instance segmentation.
"""

from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
from PIL import Image, ImageDraw, ImageFont
import torch
import numpy as np
import json


class SegmentationExtractor:
    """Extracts instance segmentation from images using Mask2Former."""

    def __init__(self, model_name: str = "facebook/mask2former-swin-small-coco-instance"):
        """
        Initialize instance segmentation model.

        Args:
            model_name: Hugging Face model name
                Recommended:
                - facebook/mask2former-swin-small-coco-instance (balanced)
                - facebook/mask2former-swin-tiny-coco-instance (faster)
                - facebook/mask2former-swin-large-coco-instance (higher accuracy)
        """
        print(f"Loading model: {model_name}")
        self.model_name = model_name
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = Mask2FormerForUniversalSegmentation.from_pretrained(model_name)
        self.id2label = self.model.config.id2label

    def extract(self, image_path: str) -> tuple[dict, np.ndarray]:
        """
        Extract instance segmentation from image.

        Args:
            image_path: Path to input image

        Returns:
            Tuple of (instance data dict, segmentation map array)
        """
        # Load image
        image = Image.open(image_path)
        orig_width, orig_height = image.size
        total_pixels = orig_width * orig_height

        # Preprocess
        inputs = self.processor(images=image, return_tensors="pt")

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Post-process to get instance segmentation
        # This returns a list of dicts with 'segmentation' and 'segments_info'
        results = self.processor.post_process_instance_segmentation(
            outputs,
            target_sizes=[(orig_height, orig_width)]
        )[0]

        # Get segmentation map (HxW array where each pixel has an instance ID)
        pred_seg = results["segmentation"].cpu().numpy()

        # Get instance information
        segments_info = results["segments_info"]

        # Analyze each instance
        instances = []

        for instance_info in segments_info:
            instance_id = instance_info["id"]
            label_id = instance_info["label_id"]
            score = instance_info.get("score", 1.0)

            # Get mask for this instance
            mask = (pred_seg == instance_id)
            pixel_count = np.sum(mask)

            if pixel_count == 0:
                continue

            # Calculate proportion
            proportion = pixel_count / total_pixels

            # Calculate center point
            y_coords, x_coords = np.where(mask)
            center_x = np.mean(x_coords) / orig_width
            center_y = np.mean(y_coords) / orig_height

            # Get label name (category)
            category = self.id2label.get(int(label_id), f"class_{label_id}")

            instances.append({
                "id": str(instance_id),
                "category": category,  # Use 'category' instead of 'label'
                "score": float(score),
                "proportion": float(proportion),
                "center": {
                    "x": float(center_x),
                    "y": float(center_y)
                }
            })

        # Sort by proportion (largest first)
        instances.sort(key=lambda s: s["proportion"], reverse=True)

        instance_data = {
            "model": self.model_name,
            "image_dimensions": {
                "width": orig_width,
                "height": orig_height
            },
            "total_instances": len(instances),
            "instances": instances
        }

        return instance_data, pred_seg

    def save_data(self, instance_data: dict, output_path: str):
        """Save instance segmentation data to JSON."""
        with open(output_path, 'w') as f:
            json.dump(instance_data, f, indent=2)
        print(f"Instance segmentation data saved to {output_path}")

    def save_segmentation_map(
        self,
        image_path: str,
        instance_data: dict,
        pred_seg: np.ndarray,
        output_path: str
    ):
        """
        Save instance segmentation map (colored by category).
        Each instance gets a color based on its category.

        Args:
            image_path: Path to original image (used only for dimensions)
            instance_data: Instance segmentation data dictionary
            pred_seg: Predicted segmentation map - HxW array of instance IDs
            output_path: Path to save visualization
        """
        # Get image dimensions
        height, width = pred_seg.shape

        # Create color map: convert instance IDs to RGB colors
        colored_seg = np.zeros((height, width, 3), dtype=np.uint8)

        # Define category-based color mapping
        # All instances of the same category get the same color
        category_colors = {
            "person": [255, 100, 100],      # Red
            "bicycle": [100, 255, 100],     # Green
            "car": [100, 100, 255],         # Blue
            "motorcycle": [255, 255, 100],  # Yellow
            "bus": [255, 100, 255],         # Magenta
            "truck": [100, 255, 255],       # Cyan
            "traffic light": [255, 165, 0], # Orange
            "stop sign": [255, 0, 0],       # Red
            "bird": [255, 192, 203],        # Pink
            "cat": [255, 140, 0],           # Dark orange
            "dog": [210, 105, 30],          # Chocolate
            "backpack": [128, 0, 128],      # Purple
            "umbrella": [0, 128, 128],      # Teal
            "handbag": [139, 69, 19],       # Saddle brown
            "tie": [75, 0, 130],            # Indigo
            "suitcase": [106, 90, 205],     # Slate blue
        }

        # Default color for unknown categories
        default_color = [128, 128, 128]  # Gray

        # Map each instance to its category color
        for instance in instance_data["instances"]:
            instance_id = int(instance["id"])
            category = instance["category"]

            # Get color for this category
            color = category_colors.get(category, default_color)

            # Apply color to all pixels of this instance
            mask = (pred_seg == instance_id)
            colored_seg[mask] = color

        # Convert numpy array to PIL Image
        seg_img = Image.fromarray(colored_seg)

        # Add legend with labels
        # Expand canvas to add legend on the right
        legend_width = 200
        final_width = width + legend_width
        final = Image.new('RGB', (final_width, height), (255, 255, 255))
        final.paste(seg_img, (0, 0))

        # Draw legend
        draw = ImageDraw.Draw(final)
        y_offset = 10

        draw.text((width + 10, y_offset), "Segments:", fill=(0, 0, 0))
        y_offset += 25

        # Use same category colors as main segmentation
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
        default_color = (128, 128, 128)

        # Group instances by category and show summary
        category_counts = {}
        for instance in instance_data['instances']:
            cat = instance['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Show category summary in legend
        y_offset_start = y_offset
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1])[:10]:
            color = category_colors.get(category, default_color)

            # Draw color box
            draw.rectangle(
                [width + 10, y_offset, width + 25, y_offset + 12],
                fill=color
            )

            # Draw text with count
            text = f"{category[:12]} ×{count}"
            draw.text((width + 30, y_offset), text, fill=(0, 0, 0))

            y_offset += 18

            if y_offset > height - 20:
                break

        # Save
        final.save(output_path)
        print(f"Segmentation map saved to {output_path}")
