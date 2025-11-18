#!/usr/bin/env python3
"""
Depth estimation pipeline - Extract depth maps and create flow visualizations

Usage:
    # Extract depth map only
    python pipeline_depth.py test02.jpg

    # Create contour map (topographic style)
    python pipeline_depth.py test02.jpg --draw contour

    # Use different model
    python pipeline_depth.py test02.jpg --model depth-anything/Depth-Anything-V2-Base-hf --draw contour

    # Customize contour parameters
    python pipeline_depth.py test02.jpg --draw contour --num-levels 100 --blur-size 80
"""

import argparse
from pathlib import Path
from depth.extractor import DepthExtractor
from depth.drawer_contour import DepthContourDrawer


def main():
    parser = argparse.ArgumentParser(
        description='Extract depth map from image and create artistic visualizations',
        formatter_class=argparse.RawDescriptionHelpFormatter
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

    # Drawing options
    parser.add_argument(
        '--draw',
        choices=['contour'],
        help='Create artistic visualization (contour: topographic map)'
    )

    # Contour parameters
    parser.add_argument(
        '--line-width',
        type=int,
        default=2,
        help='Width of contour lines in pixels (default: 2)'
    )
    parser.add_argument(
        '--color-mode',
        choices=['depth', 'uniform', 'rainbow'],
        default='depth',
        help='Color mode for contours (default: depth)'
    )
    parser.add_argument(
        '--num-levels',
        type=int,
        default=20,
        help='Number of contour levels (default: 20)'
    )
    parser.add_argument(
        '--blur-size',
        type=int,
        default=15,
        help='Gaussian blur kernel size for smoothing (5-31, default: 15)'
    )
    parser.add_argument(
        '--smoothness',
        type=float,
        default=0.5,
        help='Contour smoothness (0=precise, 1-5=smooth, default: 0.5)'
    )
    parser.add_argument(
        '--contour-fill',
        action='store_true',
        help='Fill areas between contours'
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

    # Create visualization if requested
    if args.draw == 'contour':
        print(f"\n{'='*60}")
        print(f"Creating Contour Map Visualization")
        print(f"{'='*60}\n")

        drawer = DepthContourDrawer(
            canvas_width=1200,
            num_levels=args.num_levels,
            line_width=args.line_width,
            color_mode=args.color_mode,
            fill_contours=args.contour_fill,
            blur_size=args.blur_size,
            contour_smoothness=args.smoothness
        )

        contour_output_path = output_dir / f"{image_name}_depth_contour.png"
        drawer.draw(depth_data, str(contour_output_path))

        print(f"\n{'='*60}")
        print(f"Contour Map Visualization Complete!")
        print(f"{'='*60}")
        print(f"Contour output: {contour_output_path}")
        print(f"{'='*60}\n")

    # Print summary
    print(f"\n{'='*60}")
    print(f"Pipeline Complete!")
    print(f"{'='*60}")
    print(f"Depth map: {depth_output_path}")
    if args.draw == 'contour':
        print(f"Visualization: {output_dir / f'{image_name}_depth_contour.png'}")
    print(f"Image size: {depth_data['original_size'][0]}x{depth_data['original_size'][1]}")
    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    exit(main())
