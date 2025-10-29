"""
Pipeline 2: Proportion to Abstract Art
Proportion-driven abstract art generation based on visual area analysis.
"""

import argparse
from pathlib import Path
from proportion.extractor import ProportionExtractor
from proportion.drawer import ProportionDrawer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ProportionPipeline:
    """Two-stage pipeline: Photo -> Proportion Analysis -> Abstract Art."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "anthropic/claude-3.5-sonnet"
    ):
        """
        Initialize the pipeline.

        Args:
            api_key: OpenRouter API key for proportion extraction
            model: Model to use for proportion extraction
        """
        self.extractor = ProportionExtractor(api_key=api_key, model=model)
        self.drawer = ProportionDrawer()

    def process(
        self,
        input_image: str,
        output_image: str = "output/proportion.png",
        save_proportion_data: bool = True,
        proportion_path: str = "output/proportion.json"
    ) -> dict:
        """
        Run the full pipeline.

        Args:
            input_image: Path to input photo
            output_image: Path for output abstract drawing
            save_proportion_data: Whether to save intermediate proportion data
            proportion_path: Path to save proportion data JSON

        Returns:
            Proportion data dictionary
        """
        print("=" * 60)
        print("PROPORTION PIPELINE - Proportion-Driven Abstract Art")
        print("=" * 60)

        # Stage 1: Extract proportions
        print("\n[Stage 1] Analyzing object proportions...")
        print(f"  Input: {input_image}")
        proportion_data = self.extractor.extract(input_image)

        obj_count = len(proportion_data['objects'])
        total_proportion = sum(obj['proportion'] for obj in proportion_data['objects'])
        print(f"  Detected: {obj_count} objects")
        print(f"  Total proportion: {total_proportion:.2f}")

        # Print objects
        print("\n  Objects with proportions:")
        for obj in proportion_data['objects']:
            print(f"    - {obj['id']}: {obj['label']} ({obj['proportion']:.3f})")

        # Save proportion data
        if save_proportion_data:
            self.extractor.save_proportion_data(proportion_data, proportion_path)
            print(f"\n  Proportion data saved: {proportion_path}")

        # Stage 2: Generate abstract drawing
        print(f"\n[Stage 2] Generating proportion-based abstract drawing...")
        print(f"  Output: {output_image}")
        self.drawer.draw(proportion_data, output_image)

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nResults:")
        print(f"  Proportion Data: {proportion_path if save_proportion_data else '(not saved)'}")
        print(f"  Abstract Art: {output_image}")

        return proportion_data


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Transform photos into abstract art via proportion analysis"
    )

    parser.add_argument(
        "input_image",
        help="Path to input photo"
    )

    parser.add_argument(
        "-o", "--output",
        default="output/proportion.png",
        help="Path for output abstract drawing (default: output/proportion.png)"
    )

    parser.add_argument(
        "-p", "--proportion",
        default="output/proportion.json",
        help="Path to save proportion data JSON (default: output/proportion.json)"
    )

    parser.add_argument(
        "--no-save-data",
        action="store_true",
        help="Don't save intermediate proportion data"
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

    args = parser.parse_args()

    # Check input exists
    if not Path(args.input_image).exists():
        print(f"Error: Input image not found: {args.input_image}")
        return 1

    # Run pipeline
    try:
        pipeline = ProportionPipeline(api_key=args.api_key, model=args.model)
        pipeline.process(
            input_image=args.input_image,
            output_image=args.output,
            save_proportion_data=not args.no_save_data,
            proportion_path=args.proportion
        )
        return 0

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
