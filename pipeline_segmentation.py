"""
Pipeline: Instance Segmentation to Abstract Art
Uses Mask2Former for instance segmentation-based abstract art generation.
Each instance becomes a separate circle, colored by category.
"""

import argparse
from pathlib import Path
from segmentation.extractor import SegmentationExtractor
from segmentation.drawer import SegmentationDrawer


class SegmentationPipeline:
    """Two-stage pipeline: Photo -> Instance Segmentation -> Abstract Art."""

    def __init__(self, model_name: str | None = None):
        """
        Initialize pipeline.

        Args:
            model_name: Hugging Face model name (optional)
                Default: facebook/mask2former-swin-small-coco-instance
        """
        if model_name:
            self.extractor = SegmentationExtractor(model_name=model_name)
        else:
            self.extractor = SegmentationExtractor()

        # Always use circle drawer
        self.drawer = SegmentationDrawer()

    def process(
        self,
        input_image: str,
        output_image: str | None = None,
        save_data: bool = True,
        data_path: str | None = None,
        save_segmap: bool = True,
        segmap_path: str | None = None
    ) -> dict:
        """
        Run the pipeline.

        Args:
            input_image: Input image path
            output_image: Output image path (optional, auto-generated from input name if None)
            save_data: Whether to save segmentation data
            data_path: Path to save data JSON (optional, auto-generated if None)
            save_segmap: Whether to save segmentation map visualization
            segmap_path: Path to save segmentation map (optional, auto-generated if None)

        Returns:
            Segmentation data dictionary
        """
        # Auto-generate output paths from input image name and parameters
        input_path = Path(input_image)
        input_stem = input_path.stem  # filename without extension

        # Auto-generate paths with fixed naming
        if data_path is None:
            data_path = f"output/{input_stem}_segmentation.json"
        if segmap_path is None:
            segmap_path = f"output/{input_stem}_segmentation_map.png"
        if output_image is None:
            output_image = f"output/{input_stem}_circle.png"

        print("=" * 60)
        print("INSTANCE SEGMENTATION PIPELINE")
        print("=" * 60)

        # Stage 1: Instance Segmentation
        print("\n[Stage 1] Running instance segmentation...")
        print(f"  Input: {input_image}")
        instance_data, pred_seg = self.extractor.extract(input_image)

        instance_count = instance_data['total_instances']
        print(f"  Found {instance_count} instances")

        # Count by category
        category_counts = {}
        for inst in instance_data['instances']:
            cat = inst['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Print category summary
        print("\n  Detected categories:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    - {cat}: {count} instance(s)")

        # Save data
        if save_data:
            self.extractor.save_data(instance_data, data_path)

        # Save segmentation map
        if save_segmap:
            print(f"\n  Saving instance segmentation map: {segmap_path}")
            self.extractor.save_segmentation_map(
                input_image, instance_data, pred_seg, segmap_path
            )

        # Stage 2: Draw
        print(f"\n[Stage 2] Drawing abstract art with circles...")
        print(f"  Output: {output_image}")
        self.drawer.draw(instance_data, output_image)

        print("\n" + "=" * 60)
        print("COMPLETE!")
        print("=" * 60)
        print(f"\nResults:")
        print(f"  Segmentation Data: {data_path if save_data else '(not saved)'}")
        print(f"  Segmentation Map: {segmap_path if save_segmap else '(not saved)'}")
        print(f"  Abstract Art: {output_image}")

        return instance_data


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Transform photos into circle abstract art via instance segmentation"
    )

    parser.add_argument(
        "input_image",
        help="Path to input photo"
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output image path (default: output/{input_name}_segmentation.png)"
    )

    parser.add_argument(
        "-d", "--data",
        default=None,
        help="Output data path (default: output/{input_name}_segmentation.json)"
    )

    parser.add_argument(
        "--model",
        help="Hugging Face model name (default: facebook/mask2former-swin-small-coco-instance)"
    )

    parser.add_argument(
        "-m", "--segmap",
        default=None,
        help="Path to save segmentation map (default: output/{input_name}_segmentation_map.png)"
    )

    parser.add_argument(
        "--no-save-segmap",
        action="store_true",
        help="Don't save segmentation map visualization"
    )

    args = parser.parse_args()

    # Check input exists
    if not Path(args.input_image).exists():
        print(f"Error: Input image not found: {args.input_image}")
        return 1

    # Run pipeline
    try:
        pipeline = SegmentationPipeline(model_name=args.model)
        pipeline.process(
            input_image=args.input_image,
            output_image=args.output,
            data_path=args.data,
            save_segmap=not args.no_save_segmap,
            segmap_path=args.segmap
        )
        return 0

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
