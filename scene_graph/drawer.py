"""
Abstract Drawing Generation
Generates minimalist abstract drawings from scene graphs using color and geometry.
"""

import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw
from dataclasses import dataclass


@dataclass
class NodeLayout:
    """Layout information for a graph node."""
    id: str
    label: str
    x: float
    y: float
    width: float
    height: float
    color: Tuple[int, int, int]
    shape: str  # 'circle', 'square', 'rectangle'


class AbstractDrawer:
    """Generates abstract drawings from scene graphs."""

    # Color palettes by category
    WARM_COLORS = [
        (255, 107, 107),  # coral red
        (255, 159, 64),   # orange
        (255, 205, 86),   # yellow
        (255, 140, 105),  # peach
        (239, 71, 111),   # pink
    ]

    COOL_COLORS = [
        (54, 162, 235),   # blue
        (75, 192, 192),   # teal
        (153, 102, 255),  # purple
        (100, 149, 237),  # cornflower
        (72, 201, 176),   # turquoise
    ]

    BRIGHT_COLORS = [
        (255, 99, 132),   # bright pink
        (255, 206, 86),   # bright yellow
        (75, 255, 107),   # lime
        (255, 0, 255),    # magenta
        (0, 255, 255),    # cyan
    ]

    NEUTRAL_COLORS = [
        (201, 203, 207),  # light gray
        (169, 169, 169),  # gray
        (211, 211, 211),  # light gray 2
        (192, 192, 192),  # silver
        (220, 220, 220),  # very light gray
    ]

    # Object category mappings
    LIVING_ENTITIES = {'person', 'man', 'woman', 'child', 'baby', 'dog', 'cat', 'bird', 'animal', 'human', 'people'}
    DEVICES = {'laptop', 'computer', 'phone', 'tablet', 'monitor', 'screen', 'keyboard', 'mouse', 'device', 'machine', 'tv', 'camera'}
    TOOLS = {'cup', 'mug', 'glass', 'bottle', 'fork', 'knife', 'spoon', 'pen', 'pencil', 'book', 'plate', 'bowl'}
    SURFACES = {'desk', 'table', 'floor', 'ground', 'wall', 'shelf', 'counter', 'surface', 'bed', 'sofa', 'chair'}

    def __init__(self, canvas_size: Tuple[int, int] = (1200, 800)):
        """
        Initialize the drawer.

        Args:
            canvas_size: (width, height) of output image
        """
        self.canvas_size = canvas_size
        self.margin = 80

    def _categorize_object(self, label: str) -> str:
        """
        Categorize an object label into color groups.

        Args:
            label: Object label

        Returns:
            Category name: 'living', 'device', 'tool', or 'surface'
        """
        label_lower = label.lower()

        if label_lower in self.LIVING_ENTITIES:
            return 'living'
        elif label_lower in self.DEVICES:
            return 'device'
        elif label_lower in self.TOOLS:
            return 'tool'
        elif label_lower in self.SURFACES:
            return 'surface'
        else:
            # Default categorization by heuristics
            if any(word in label_lower for word in ['person', 'man', 'woman', 'animal']):
                return 'living'
            elif any(word in label_lower for word in ['desk', 'table', 'floor', 'wall']):
                return 'surface'
            else:
                return 'tool'

    def _assign_color(self, label: str) -> Tuple[int, int, int]:
        """
        Assign color based on object category.

        Args:
            label: Object label

        Returns:
            RGB color tuple
        """
        category = self._categorize_object(label)

        if category == 'living':
            return random.choice(self.WARM_COLORS)
        elif category == 'device':
            return random.choice(self.COOL_COLORS)
        elif category == 'tool':
            return random.choice(self.BRIGHT_COLORS)
        else:  # surface
            return random.choice(self.NEUTRAL_COLORS)

    def _assign_shape(self, label: str) -> str:
        """
        Assign shape based on object category.

        Args:
            label: Object label

        Returns:
            Shape name: 'circle', 'square', or 'rectangle'
        """
        category = self._categorize_object(label)

        if category == 'living':
            return 'circle'
        elif category == 'device':
            return 'rectangle'
        elif category == 'tool':
            return random.choice(['circle', 'square'])
        else:  # surface
            return 'rectangle'

    def _compute_layout(self, scene_graph: Dict) -> List[NodeLayout]:
        """
        Compute spatial layout for objects based on relationships.

        Args:
            scene_graph: Scene graph dictionary

        Returns:
            List of NodeLayout objects
        """
        objects = scene_graph['objects']
        relations = scene_graph['relations']

        # Build relationship graph
        on_top_of = {}  # maps object_id -> list of subjects on top

        for rel in relations:
            subj = rel['subject']
            pred = rel['predicate']
            obj = rel['object']

            if pred == 'on_top_of':
                if obj not in on_top_of:
                    on_top_of[obj] = []
                on_top_of[obj].append(subj)

        # Determine base objects (those on bottom / supporting others)
        obj_ids = {o['id'] for o in objects}
        base_objects = [oid for oid in obj_ids if oid in on_top_of and oid not in [rel['subject'] for rel in relations if rel['predicate'] == 'on_top_of']]

        # If no clear base, treat surfaces as base
        if not base_objects:
            base_objects = [o['id'] for o in objects if self._categorize_object(o['label']) == 'surface']

        # If still none, use first object
        if not base_objects:
            base_objects = [objects[0]['id']]

        # Assign positions
        layouts = []
        positioned = set()
        width, height = self.canvas_size

        # Position base objects at bottom
        base_y = height - self.margin - 100
        base_x_start = self.margin
        base_spacing = (width - 2 * self.margin) / max(len(base_objects), 1)

        for i, obj_id in enumerate(base_objects):
            obj = next(o for o in objects if o['id'] == obj_id)
            x = base_x_start + i * base_spacing + base_spacing / 2
            y = base_y

            layouts.append(NodeLayout(
                id=obj_id,
                label=obj['label'],
                x=x,
                y=y,
                width=150,
                height=80,
                color=self._assign_color(obj['label']),
                shape=self._assign_shape(obj['label'])
            ))
            positioned.add(obj_id)

        # Position objects on top of base objects
        for base_id in base_objects:
            if base_id in on_top_of:
                base_layout = next(l for l in layouts if l.id == base_id)
                stack = on_top_of[base_id]

                for j, obj_id in enumerate(stack):
                    obj = next(o for o in objects if o['id'] == obj_id)
                    y = base_layout.y - (j + 1) * 120

                    layouts.append(NodeLayout(
                        id=obj_id,
                        label=obj['label'],
                        x=base_layout.x,
                        y=y,
                        width=100,
                        height=80,
                        color=self._assign_color(obj['label']),
                        shape=self._assign_shape(obj['label'])
                    ))
                    positioned.add(obj_id)

        # Position remaining objects in grid
        remaining = [o for o in objects if o['id'] not in positioned]
        if remaining:
            grid_cols = math.ceil(math.sqrt(len(remaining)))
            grid_spacing_x = (width - 2 * self.margin) / max(grid_cols, 1)
            grid_spacing_y = 150

            for i, obj in enumerate(remaining):
                col = i % grid_cols
                row = i // grid_cols
                x = self.margin + col * grid_spacing_x + grid_spacing_x / 2
                y = self.margin + row * grid_spacing_y + 100

                layouts.append(NodeLayout(
                    id=obj['id'],
                    label=obj['label'],
                    x=x,
                    y=y,
                    width=100,
                    height=80,
                    color=self._assign_color(obj['label']),
                    shape=self._assign_shape(obj['label'])
                ))

        return layouts

    def _draw_shape(self, draw: ImageDraw.Draw, layout: NodeLayout):
        """
        Draw a shape on the canvas (no outline).

        Args:
            draw: PIL ImageDraw object
            layout: Node layout information
        """
        x, y = layout.x, layout.y
        w, h = layout.width, layout.height

        if layout.shape == 'circle':
            radius = min(w, h) / 2
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=layout.color
            )
        elif layout.shape == 'square':
            side = min(w, h)
            draw.rectangle(
                [x - side/2, y - side/2, x + side/2, y + side/2],
                fill=layout.color
            )
        else:  # rectangle
            draw.rectangle(
                [x - w/2, y - h/2, x + w/2, y + h/2],
                fill=layout.color
            )

    def draw(self, scene_graph: Dict, output_path: str):
        """
        Generate abstract drawing from scene graph.

        Args:
            scene_graph: Scene graph dictionary
            output_path: Path to save output image
        """
        # Create canvas
        img = Image.new('RGB', self.canvas_size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Compute layout
        layouts = self._compute_layout(scene_graph)

        # Draw shapes (no connection lines)
        for layout in layouts:
            self._draw_shape(draw, layout)

        # Draw labels
        for layout in layouts:
            text = layout.label
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            draw.text(
                (layout.x - text_width/2, layout.y - text_height/2),
                text,
                fill=(0, 0, 0)
            )

        # Save
        img.save(output_path)
        print(f"Abstract drawing saved to {output_path}")

    def draw_from_file(self, scene_graph_path: str, output_path: str):
        """
        Generate abstract drawing from scene graph JSON file.

        Args:
            scene_graph_path: Path to scene graph JSON
            output_path: Path to save output image
        """
        with open(scene_graph_path, 'r') as f:
            scene_graph = json.load(f)

        self.draw(scene_graph, output_path)
