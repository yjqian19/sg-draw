#!/usr/bin/env python3
"""
Depth estimation pipeline - Extract depth maps from images

Usage:
    python pipeline_depth.py test02.jpg
    python pipeline_depth.py test02.jpg --output output/
    python pipeline_depth.py test02.jpg --model depth-anything/Depth-Anything-V2-Base-hf
"""

import argparse
from pathlib import Path
from depth.extractor import DepthExtractor


def main():
    parser = argparse.ArgumentParser(
        description='Extract depth map from image using Hugging Face models'
    )
    parser.add_argument(
        'image',
        help='Input image path'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory (default: output/)'
    )
    parser.add_argument(
        '--model', '-m',
        default='depth-anything/Depth-Anything-V2-Small-hf',
        choices=[
            'depth-anything/Depth-Anything-V2-Small-hf',
            'depth-anything/Depth-Anything-V2-Base-hf',
            'depth-anything/Depth-Anything-V2-Large-hf',
            'Intel/dpt-hybrid-midas',
        ],
        help='Depth estimation model (default: Depth-Anything-V2-Small)'
    )

    args = parser.parse_args()

    # Validate input image
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image not found: {args.image}")
        return 1

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize depth extractor
    print(f"\n{'='*60}")
    print(f"Depth Estimation Pipeline")
    print(f"{'='*60}")
    print(f"Input image: {args.image}")
    print(f"Model: {args.model}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")

    extractor = DepthExtractor(model_name=args.model)

    # Extract depth map
    try:
        depth_data = extractor.extract(args.image)
    except Exception as e:
        print(f"\nError during depth extraction: {e}")
        return 1

    # Save depth map
    image_name = image_path.stem
    depth_output_path = output_dir / f"{image_name}_depth_map.png"
    extractor.save_depth_map(depth_data, str(depth_output_path))

    # Print summary
    print(f"\n{'='*60}")
    print(f"Depth Estimation Complete!")
    print(f"{'='*60}")
    print(f"Output: {depth_output_path}")
    print(f"Image size: {depth_data['original_size'][0]}x{depth_data['original_size'][1]}")
    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    exit(main())
