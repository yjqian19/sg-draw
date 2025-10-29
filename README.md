# sg-draw

Two independent generative pipelines that transform photos into abstract art.

## Two Pipelines

### Pipeline 1: Relationship-Driven Abstract Art
Visualizes spatial and functional relationships between objects.

- **Focus**: Object relationships (on_top_of, next_to, using, etc.)
- **Output**: Shapes arranged based on scene structure
- **Style**: Relationship-driven composition

### Pipeline 2: Proportion-Driven Abstract Art
Visualizes the visual composition and area proportions of objects.

- **Focus**: Visual area proportions of each object instance
- **Output**: Shapes sized by their visual area coverage
- **Style**: Proportion-driven collage

## Installation

```bash
# Install dependencies with UV
uv sync

# Create .env file and add your OpenRouter API key
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY=your-key-here
```

## Usage

### Pipeline 1: Scene Graph

```bash
# Basic usage (uses Claude 3.5 Sonnet by default)
python pipeline_scene_graph.py test01.jpg

# Use a different model
python pipeline_scene_graph.py test01.jpg --model openai/gpt-4o

# Custom output paths
python pipeline_scene_graph.py test01.jpg -o my_output.png -s my_graph.json
```

**Output:**
- `output/scene_graph.json` - Structured scene graph with objects and relationships
- `output/scene_graph.png` - Abstract art showing relationships

### Pipeline 2: Proportion

```bash
# Basic usage
python pipeline_proportion.py test01.jpg

# Use a different model
python pipeline_proportion.py test01.jpg --model google/gemini-pro-1.5

# Custom output paths
python pipeline_proportion.py test01.jpg -o my_output.png -p my_proportion.json
```

**Output:**
- `output/proportion.json` - Each object instance with its visual area proportion
- `output/proportion.png` - Abstract art with sizes representing proportions

## Supported Models

Via OpenRouter, you can use any vision-capable model:
- `anthropic/claude-3.5-sonnet` (default, recommended)
- `openai/gpt-4o`
- `google/gemini-pro-1.5`
- `openai/gpt-4-vision-preview`
- And many more at [openrouter.ai/models](https://openrouter.ai/models)

## How It Works

### Pipeline 1: Scene Graph → Abstract Art

**Stage 1: Scene Graph Extraction**
- Input: Photo
- Process: Analyze image using vision model via OpenRouter
- Output: JSON with objects and their spatial/functional relationships

Example output:
```json
{
  "objects": [
    {"id": "o1", "label": "person"},
    {"id": "o2", "label": "laptop"},
    {"id": "o3", "label": "desk"}
  ],
  "relations": [
    {"subject": "o1", "predicate": "using", "object": "o2"},
    {"subject": "o2", "predicate": "on_top_of", "object": "o3"}
  ]
}
```

**Stage 2: Abstract Drawing**
- Shapes arranged based on relationships
- Vertical stacking for `on_top_of`
- Horizontal adjacency for `next_to`
- Color-coded by object category

### Pipeline 2: Proportion → Abstract Art

**Stage 1: Proportion Analysis**
- Input: Photo
- Process: Identify each object instance and estimate its visual area proportion
- Output: JSON with each object and its proportion (0.0 to 1.0)

Example output:
```json
{
  "objects": [
    {"id": "1", "label": "sky", "proportion": 0.40},
    {"id": "2", "label": "building", "proportion": 0.35},
    {"id": "3", "label": "window", "proportion": 0.02},
    {"id": "4", "label": "window", "proportion": 0.02}
  ]
}
```

**Stage 2: Abstract Drawing**
- Each object becomes a shape
- Shape area = canvas area × proportion
- Random placement (overlapping allowed)
- Color-coded by object category

## Visual Encoding Rules

Both pipelines use the same color and shape mapping:

**Colors:**
- People/animals → warm colors (red, orange, yellow)
- Devices/machines → cool colors (blue, purple, teal)
- Tools/small objects → bright colors (pink, lime, cyan)
- Surfaces/backgrounds → neutral colors (gray, silver)

**Shapes:**
- People/animals → circles
- Devices/machines → rectangles
- Tools/small objects → circles or squares
- Surfaces → rectangles

## Project Structure

```
sg-draw/
├── scene_graph/              # Pipeline 1
│   ├── extractor.py         # Scene graph extraction
│   └── drawer.py            # Relationship-driven drawing
├── proportion/              # Pipeline 2
│   ├── extractor.py         # Proportion analysis
│   └── drawer.py            # Proportion-driven drawing
├── output/                  # Generated outputs (JSON and PNG)
├── pipeline_scene_graph.py  # Pipeline 1 entry point
├── pipeline_proportion.py   # Pipeline 2 entry point
├── test01.jpg              # Test images
├── .env                    # API configuration
├── pyproject.toml          # UV dependencies
└── README.md               # This file
```

## Python API

### Pipeline 1

```python
from scene_graph.extractor import SceneGraphExtractor
from scene_graph.drawer import AbstractDrawer

# Extract scene graph
extractor = SceneGraphExtractor(model="anthropic/claude-3.5-sonnet")
scene_graph = extractor.extract("photo.jpg")

# Generate abstract art
drawer = AbstractDrawer()
drawer.draw(scene_graph, "output.png")
```

### Pipeline 2

```python
from proportion.extractor import ProportionExtractor
from proportion.drawer import ProportionDrawer

# Extract proportions
extractor = ProportionExtractor(model="openai/gpt-4o")
proportion_data = extractor.extract("photo.jpg")

# Generate abstract art
drawer = ProportionDrawer()
drawer.draw(proportion_data, "output.png")
```

## Requirements

- Python 3.12+
- UV package manager
- OpenRouter API key

## License

MIT License
