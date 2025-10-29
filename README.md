# sg-draw

Two-stage generative pipeline that transforms photos into abstract art driven by scene graph structure.

## Installation

```bash
# Install dependencies with UV
uv add anthropic pillow

# Or sync from existing pyproject.toml
uv sync

# Set API key
export ANTHROPIC_API_KEY="your-key"
```

## Usage

```bash
# Full pipeline: photo → abstract art
uv run python pipeline.py photo.jpg

# Extract scene graph only
uv run python scene_graph_extractor.py photo.jpg scene_graph.json

# Generate abstract drawing only
uv run python abstract_drawer.py scene_graph.json output.png
```

## How It Works

**Stage 1: Scene Graph Extraction**
- Input: Photo
- Process: Analyze image using Claude Vision API
- Output: Structured JSON (objects + relationships)

**Stage 2: Abstract Drawing Generation**
- Input: Scene graph JSON
- Process: Convert semantics to geometric shapes and colors
- Output: Abstract drawing PNG

**Visual Encoding Rules:**
- People/animals → circles, warm colors (red, orange, yellow)
- Devices/machines → rectangles, cool colors (blue, purple)
- Tools/small objects → squares/circles, bright colors
- Surfaces/backgrounds → rectangles, neutral colors

**Relationship Visualization:**
- `on_top_of` → vertical stacking
- `next_to` → horizontal adjacency
- `holding`/`using` → bold connecting lines

## Python API

```python
from pipeline import PhotoToAbstractPipeline

pipeline = PhotoToAbstractPipeline()
scene_graph = pipeline.process("photo.jpg", "output.png")
```
