"""
Pipeline 1: Scene Graph to Abstract Art
Relationship-driven abstract art generation from scene graphs.
"""

import argparse
from pathlib import Path
from scene_graph.extractor import SceneGraphExtractor
from scene_graph.drawer import AbstractDrawer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SceneGraphPipeline:
    """Two-stage pipeline: Photo -> Scene Graph -> Abstract Art."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "anthropic/claude-3.5-sonnet"
    ):
        """
        Initialize the pipeline.

        Args:
            api_key: OpenRouter API key for scene graph extraction
            model: Model to use for scene graph extraction
        """
        self.extractor = SceneGraphExtractor(api_key=api_key, model=model)
        self.drawer = AbstractDrawer()

    def process(
        self,
        input_image: str,
        output_image: str = "output/scene_graph.png",
        save_scene_graph: bool = True,
        scene_graph_path: str = "output/scene_graph.json"
    ) -> dict:
        """
        Run the full pipeline.

        Args:
            input_image: Path to input photo
            output_image: Path for output abstract drawing
            save_scene_graph: Whether to save intermediate scene graph
            scene_graph_path: Path to save scene graph JSON

        Returns:
            Scene graph dictionary
        """
        print("=" * 60)
        print("SCENE GRAPH PIPELINE - Relationship-Driven Abstract Art")
        print("=" * 60)

        # Stage 1: Extract scene graph
        print("\n[Stage 1] Extracting scene graph from image...")
        print(f"  Input: {input_image}")
        scene_graph = self.extractor.extract(input_image)

        obj_count = len(scene_graph['objects'])
        rel_count = len(scene_graph['relations'])
        print(f"  Detected: {obj_count} objects, {rel_count} relationships")

        # Print objects
        print("\n  Objects:")
        for obj in scene_graph['objects']:
            print(f"    - {obj['id']}: {obj['label']}")

        # Print relations
        print("\n  Relationships:")
        for rel in scene_graph['relations']:
            print(f"    - {rel['subject']} {rel['predicate']} {rel['object']}")

        # Save scene graph
        if save_scene_graph:
            self.extractor.save_scene_graph(scene_graph, scene_graph_path)
            print(f"\n  Scene graph saved: {scene_graph_path}")

        # Stage 2: Generate abstract drawing
        print(f"\n[Stage 2] Generating abstract drawing...")
        print(f"  Output: {output_image}")
        self.drawer.draw(scene_graph, output_image)

        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nResults:")
        print(f"  Scene Graph: {scene_graph_path if save_scene_graph else '(not saved)'}")
        print(f"  Abstract Art: {output_image}")

        return scene_graph


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Transform photos into abstract art via scene graph analysis"
    )

    parser.add_argument(
        "input_image",
        help="Path to input photo"
    )

    parser.add_argument(
        "-o", "--output",
        default="output/scene_graph.png",
        help="Path for output abstract drawing (default: output/scene_graph.png)"
    )

    parser.add_argument(
        "-s", "--scene-graph",
        default="output/scene_graph.json",
        help="Path to save scene graph JSON (default: output/scene_graph.json)"
    )

    parser.add_argument(
        "--no-save-graph",
        action="store_true",
        help="Don't save intermediate scene graph"
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
        pipeline = SceneGraphPipeline(api_key=args.api_key, model=args.model)
        pipeline.process(
            input_image=args.input_image,
            output_image=args.output,
            save_scene_graph=not args.no_save_graph,
            scene_graph_path=args.scene_graph
        )
        return 0

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
