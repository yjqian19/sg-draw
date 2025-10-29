"""
Pipeline 3: Position to Abstract Art
Position-based abstract art generation with proportional sizes at actual locations.
"""

import argparse
from pathlib import Path
from position.extractor import PositionExtractor
from position.drawer import PositionDrawer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PositionPipeline:
    """Two-stage pipeline: Photo -> Position Analysis -> Abstract Art."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "anthropic/claude-3.5-sonnet",
        canvas_width: int = 1200
    ):
        """
        Initialize the pipeline.

        Args:
            api_key: OpenRouter API key for position extraction
            model: Model to use for position extraction
            canvas_width: Output canvas width in pixels (height auto-calculated)
        """
        self.extractor = PositionExtractor(api_key=api_key, model=model, canvas_width=canvas_width)
        self.drawer = PositionDrawer()

    def process(
        self,
        input_image: str,
        output_image: str = "output/position.png",
        save_position_data: bool = True,
        position_path: str = "output/position.json"
    ) -> dict:
        """
        Run the full pipeline.

        Args:
            input_image: Path to input photo
            output_image: Path for output abstract drawing
            save_position_data: Whether to save intermediate position data
            position_path: Path to save position data JSON

        Returns:
            Position data dictionary
        """
        print("=" * 60)
        print("POSITION PIPELINE - Position-Based Abstract Art")
        print("=" * 60)

        # Stage 1: Extract positions
        print("\n[Stage 1] Analyzing object positions and proportions...")
        print(f"  Input: {input_image}")
        position_data = self.extractor.extract(input_image)

        obj_count = len(position_data['objects'])
        total_proportion = sum(obj['proportion'] for obj in position_data['objects'])

        orig_dims = position_data['image_dimensions']['original']
        out_dims = position_data['image_dimensions']['output']

        print(f"  Detected: {obj_count} objects")
        print(f"  Total proportion: {total_proportion:.2f}")
        print(f"  Original image: {orig_dims['width']}x{orig_dims['height']}")
        print(f"  Output canvas: {out_dims['width']}x{out_dims['height']}")

        # Print objects with positions
        print("\n  Objects with positions and proportions:")
        for obj in position_data['objects']:
            pos = obj['position']
            print(f"    - {obj['id']}: {obj['label']} @ ({pos['x']:.2f}, {pos['y']:.2f}) [{obj['proportion']:.3f}]")

        # Save position data
        if save_position_data:
            self.extractor.save_position_data(position_data, position_path)
            print(f"\n  Position data saved: {position_path}")

        # Stage 2: Generate abstract drawing
        print(f"\n[Stage 2] Generating position-based abstract drawing...")
        print(f"  Output: {output_image}")
        self.drawer.draw(position_data, output_image)

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nResults:")
        print(f"  Position Data: {position_path if save_position_data else '(not saved)'}")
        print(f"  Abstract Art: {output_image}")

        return position_data


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Transform photos into abstract art via position analysis"
    )

    parser.add_argument(
        "input_image",
        help="Path to input photo"
    )

    parser.add_argument(
        "-o", "--output",
        default="output/position.png",
        help="Path for output abstract drawing (default: output/position.png)"
    )

    parser.add_argument(
        "-p", "--position",
        default="output/position.json",
        help="Path to save position data JSON (default: output/position.json)"
    )

    parser.add_argument(
        "--no-save-data",
        action="store_true",
        help="Don't save intermediate position data"
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )

    parser.add_argument(
        "-m", "--model",
        default="anthropic/claude-3.5-sonnet",
        help="Model to use (default: anthropic/claude-3.5-sonnet)"
    )

    parser.add_argument(
        "-w", "--width",
        type=int,
        default=1200,
        help="Output canvas width in pixels (default: 1200)"
    )

    args = parser.parse_args()

    # Check input exists
    if not Path(args.input_image).exists():
        print(f"Error: Input image not found: {args.input_image}")
        return 1

    # Run pipeline
    try:
        pipeline = PositionPipeline(
            api_key=args.api_key,
            model=args.model,
            canvas_width=args.width
        )
        pipeline.process(
            input_image=args.input_image,
            output_image=args.output,
            save_position_data=not args.no_save_data,
            position_path=args.position
        )
        return 0

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
