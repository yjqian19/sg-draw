#!/usr/bin/env python3
"""
Depth estimation pipeline - Extract depth maps and analyze flow fields

Usage:
    # Extract depth map only
    python analyzer/pipeline_depth.py test02.jpg

    # Analyze flow field and generate gradient preview
    python analyzer/pipeline_depth.py test02.jpg --analyze

    # Export flow field data for frontend
    python analyzer/pipeline_depth.py test02.jpg --export

    # Both analyze and export
    python analyzer/pipeline_depth.py test02.jpg --analyze --export

    # Use different model
    python analyzer/pipeline_depth.py test02.jpg --model depth-anything/Depth-Anything-V2-Base-hf --analyze --export

    # Custom blur size
    python analyzer/pipeline_depth.py test02.jpg --analyze --export --blur-size 30
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analyzer.depth.extractor import DepthExtractor
from analyzer.depth.flow_field import FlowFieldAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description='Extract depth map from image and analyze flow field',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'image',
        help='Input image path'
    )
    parser.add_argument(
        '--output', '-o',
        default='output/analyzer',
        help='Output directory (default: output/analyzer)'
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
    parser.add_argument(
        '--blur-size',
        type=int,
        default=15,
        help='Gaussian blur kernel size for flow field (default: 15)'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze flow field and generate gradient preview'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export flow field data as JSON for frontend'
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

    # Flow field analysis
    if args.analyze or args.export:
        print(f"\n{'='*60}")
        print(f"Flow Field Analysis")
        print(f"{'='*60}\n")

        analyzer = FlowFieldAnalyzer()
        flow_data = analyzer.compute_from_depth_data(
            depth_data,
            blur_size=args.blur_size
        )

        # Generate gradient preview
        if args.analyze:
            gradient_output_path = output_dir / f"{image_name}_gradient_map.png"
            analyzer.visualize_gradient(flow_data, str(gradient_output_path))

        # Export JSON data
        if args.export:
            json_output_path = output_dir / f"{image_name}_flow_field.json"
            analyzer.export_json(flow_data, depth_data, str(json_output_path))

        print(f"\n{'='*60}")
        print(f"Flow Field Analysis Complete!")
        print(f"{'='*60}")
        if args.analyze:
            print(f"Gradient preview: {output_dir / f'{image_name}_gradient_map.png'}")
        if args.export:
            print(f"Flow field data: {output_dir / f'{image_name}_flow_field.json'}")
        print(f"{'='*60}\n")

    # Print summary
    print(f"\n{'='*60}")
    print(f"Pipeline Complete!")
    print(f"{'='*60}")
    print(f"Depth map: {depth_output_path}")
    if args.analyze:
        print(f"Gradient preview: {output_dir / f'{image_name}_gradient_map.png'}")
    if args.export:
        print(f"Flow field data: {output_dir / f'{image_name}_flow_field.json'}")
    print(f"Image size: {depth_data['original_size'][0]}x{depth_data['original_size'][1]}")
    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    exit(main())
