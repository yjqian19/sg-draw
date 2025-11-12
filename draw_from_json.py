"""
Draw abstract art directly from segmentation JSON data.
Skip the segmentation step and quickly try different drawing styles.
"""

import json
from pathlib import Path
from segmentation.drawer import SegmentationDrawer
from segmentation.drawer_dots import DotPatternDrawer
from segmentation.drawer_field import DensityFieldDrawer, DensityFieldDrawerAdvanced
from segmentation.drawer_flower import FlowerDrawer, OrganicFlowerDrawer


# ============================================================
# CONFIGURATION - Edit these variables to change settings
# ============================================================

# Input/Output
json_file = "output/test02_segmentation.json"
output = None  # None = auto-generate based on parameters

# Drawer type: "circle", "dots", "field", "field-advanced", "flower", "flower-organic"
drawer = "flower-organic"

# Dot settings (for "dots" and "field" drawers)
dot_size = 8                   # Dot size in pixels (larger = more visible)
dot_density = 0.3              # For "dots" and "field-advanced" (0.1-1.0)

# Dot pattern (for "dots" drawer): "random", "grid", "spiral"
dot_pattern = "random"

# Field settings (for "field" drawer)
field_total_dots = 60000      # Total number of dots
field_influence = 200         # Influence radius in pixels
field_concentration = 3.0     # Concentration: 1.0 (gradual) to 4.0+ (steep)

# Flower settings (for "flower" drawer)
flower_petals = 8             # Number of petals per flower (5-12)
flower_dots_per_petal = 50    # Dots to fill each petal (more = denser)
flower_petal_curve = 0.7      # Petal curvature: 0 (straight) to 1 (very curved)
flower_randomness = 0.25      # Random variation: 0 (ordered) to 1 (chaotic)
flower_size_multiplier = 2.5  # Flower size multiplier (larger = bigger flowers)
flower_petal_width = 3      # Petal width: 0.5 (narrow) to 3.0 (wide)

# Flower organic settings (for "flower-organic" drawer)
flower_style = "fern"        # Style: "daisy", "sunflower", "spiral", "fern"
flower_density = 2          # Density multiplier

# ============================================================


def main():
    """Draw abstract art from JSON data."""

    # Check if JSON file exists
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_file}")
        return 1

    # Load JSON data
    print(f"Loading data from: {json_file}")
    with open(json_path, 'r') as f:
        instance_data = json.load(f)

    # Validate data
    if "instances" not in instance_data:
        print("Error: Invalid JSON format. Missing 'instances' field.")
        return 1

    print(f"  Found {len(instance_data['instances'])} instances")

    # Auto-generate output path if not specified
    if output is None:
        # Extract base name from JSON file
        json_stem = json_path.stem
        # Remove "_segmentation" suffix to get base name
        if json_stem.endswith('_segmentation'):
            base_name = json_stem[:-len('_segmentation')]  # Get "test02" from "test02_segmentation"
        else:
            base_name = json_stem

        # Build new suffix
        suffix_parts = []
        if drawer == "dots":
            suffix_parts.append("dots")
            if dot_pattern != "random":
                suffix_parts.append(dot_pattern)
            if dot_size != 8:
                suffix_parts.append(f"size{dot_size}")
            if dot_density != 0.3:
                suffix_parts.append(f"d{dot_density}")
        elif drawer in ["field", "field-advanced"]:
            suffix_parts.append(drawer)
            if field_total_dots != 10000:
                suffix_parts.append(f"{field_total_dots}dots")
            if dot_size != 4:
                suffix_parts.append(f"size{dot_size}")
            if drawer == "field" and field_concentration != 2.0:
                suffix_parts.append(f"c{field_concentration}")
        elif drawer == "flower":
            suffix_parts.append("flower")
            if flower_petals != 6:
                suffix_parts.append(f"p{flower_petals}")
            if flower_petal_curve != 0.3:
                suffix_parts.append(f"curve{flower_petal_curve}")
        elif drawer == "flower-organic":
            suffix_parts.append(f"flower-{flower_style}")
            if flower_density != 1.0:
                suffix_parts.append(f"d{flower_density}")
        else:
            suffix_parts.append("circle")

        suffix = "_".join(suffix_parts)
        output_path = json_path.parent / f"{base_name}_{suffix}.png"
    else:
        output_path = Path(output)

    # Create drawer
    if drawer == "dots":
        drawer_obj = DotPatternDrawer(
            dot_size=dot_size,
            dot_density=dot_density
        )
        print(f"\nDrawing with dot pattern drawer...")
        print(f"  Pattern: {dot_pattern}")
        print(f"  Dot size: {dot_size}px")
        print(f"  Dot density: {dot_density}")
        drawer_obj.draw(instance_data, str(output_path), pattern=dot_pattern)

    elif drawer == "field":
        drawer_obj = DensityFieldDrawer(
            dot_size=dot_size,
            total_dots=field_total_dots,
            influence_radius=field_influence,
            concentration=field_concentration
        )
        print(f"\nDrawing with density field drawer...")
        print(f"  Total dots: {field_total_dots}")
        print(f"  Dot size: {dot_size}px")
        print(f"  Influence radius: {field_influence}px")
        print(f"  Concentration: {field_concentration}")
        drawer_obj.draw(instance_data, str(output_path))

    elif drawer == "field-advanced":
        drawer_obj = DensityFieldDrawerAdvanced(
            dot_size=dot_size,
            dot_density=dot_density
        )
        print(f"\nDrawing with advanced density field drawer...")
        print(f"  Dot size: {dot_size}px")
        print(f"  Dot density: {dot_density}")
        drawer_obj.draw(instance_data, str(output_path))

    elif drawer == "flower":
        drawer_obj = FlowerDrawer(
            dot_size=dot_size,
            petals=flower_petals,
            dots_per_petal=flower_dots_per_petal,
            petal_curve=flower_petal_curve,
            randomness=flower_randomness,
            size_multiplier=flower_size_multiplier,
            petal_width=flower_petal_width
        )
        print(f"\nDrawing with flower pattern drawer...")
        print(f"  Petals: {flower_petals}")
        print(f"  Dots per petal: {flower_dots_per_petal}")
        print(f"  Petal curve: {flower_petal_curve}")
        print(f"  Petal width: {flower_petal_width}")
        print(f"  Randomness: {flower_randomness}")
        print(f"  Size multiplier: {flower_size_multiplier}")
        drawer_obj.draw(instance_data, str(output_path))

    elif drawer == "flower-organic":
        drawer_obj = OrganicFlowerDrawer(
            dot_size=dot_size,
            style=flower_style,
            density=flower_density
        )
        print(f"\nDrawing with organic flower drawer...")
        print(f"  Style: {flower_style}")
        print(f"  Density: {flower_density}")
        drawer_obj.draw(instance_data, str(output_path))

    else:
        drawer_obj = SegmentationDrawer()
        print(f"\nDrawing with circle drawer...")
        drawer_obj.draw(instance_data, str(output_path))

    print(f"\n✅ Abstract art saved to: {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
