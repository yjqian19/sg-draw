"""
Draw abstract art directly from segmentation JSON data.
Skip the segmentation step and quickly try different drawing styles.
"""

import argparse
import json
from pathlib import Path
from segmentation.drawer import SegmentationDrawer
from segmentation.drawer_dots import DotPatternDrawer


def main():
    """Command-line interface for drawing from JSON."""
    parser = argparse.ArgumentParser(
        description="Draw abstract art from existing segmentation JSON data"
    )

    parser.add_argument(
        "json_file",
        help="Path to segmentation JSON file"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output image path (default: auto-generated based on parameters)"
    )

    parser.add_argument(
        "--drawer",
        choices=["circle", "dots"],
        default="circle",
        help="Drawer type: 'circle' or 'dots' (default: circle)"
    )

    parser.add_argument(
        "--dot-size",
        type=int,
        default=8,
        help="Size of dots for dot pattern drawer (default: 8)"
    )

    parser.add_argument(
        "--dot-density",
        type=float,
        default=0.3,
        help="Density of dots, 0.1-1.0 (default: 0.3)"
    )

    parser.add_argument(
        "--dot-pattern",
        choices=["random", "grid", "spiral"],
        default="random",
        help="Dot pattern style (default: random)"
    )

    args = parser.parse_args()

    # Check if JSON file exists
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: JSON file not found: {args.json_file}")
        return 1

    # Load JSON data
    print(f"Loading data from: {args.json_file}")
    with open(json_path, 'r') as f:
        instance_data = json.load(f)

    # Validate data
    if "instances" not in instance_data:
        print("Error: Invalid JSON format. Missing 'instances' field.")
        return 1

    print(f"  Found {len(instance_data['instances'])} instances")

    # Auto-generate output path if not specified
    if args.output is None:
        # Extract base name from JSON file
        json_stem = json_path.stem
        # Remove "_segmentation" suffix to get base name
        if json_stem.endswith('_segmentation'):
            base_name = json_stem[:-len('_segmentation')]  # Get "test02" from "test02_segmentation"
        else:
            base_name = json_stem

        # Build new suffix
        suffix_parts = []
        if args.drawer == "dots":
            suffix_parts.append("dots")
            if args.dot_pattern != "random":
                suffix_parts.append(args.dot_pattern)
            if args.dot_size != 8:
                suffix_parts.append(f"size{args.dot_size}")
            if args.dot_density != 0.3:
                suffix_parts.append(f"d{args.dot_density}")
        else:
            suffix_parts.append("circle")

        suffix = "_".join(suffix_parts)
        output_path = json_path.parent / f"{base_name}_{suffix}.png"
    else:
        output_path = Path(args.output)

    # Create drawer
    if args.drawer == "dots":
        drawer = DotPatternDrawer(
            dot_size=args.dot_size,
            dot_density=args.dot_density
        )
        print(f"\nDrawing with dot pattern drawer...")
        print(f"  Pattern: {args.dot_pattern}")
        print(f"  Dot size: {args.dot_size}px")
        print(f"  Dot density: {args.dot_density}")
        drawer.draw(instance_data, str(output_path), pattern=args.dot_pattern)
    else:
        drawer = SegmentationDrawer()
        print(f"\nDrawing with circle drawer...")
        drawer.draw(instance_data, str(output_path))

    print(f"\n✅ Abstract art saved to: {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
