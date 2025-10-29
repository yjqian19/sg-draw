# sg-draw

Two-stage generative pipeline that transforms photos into abstract art driven by scene graph structure.

## Installation

```bash
# Install dependencies with UV
uv sync

# Create .env file from example
cp .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=your-key-here
```

## Usage

```bash
# Full pipeline: photo → abstract art (uses Claude 3.5 Sonnet by default)
uv run python pipeline.py photo.jpg

# Use a different model
uv run python pipeline.py photo.jpg --model openai/gpt-4o

# Extract scene graph only
uv run python scene_graph_extractor.py photo.jpg scene_graph.json

# Use different model for extraction
uv run python scene_graph_extractor.py photo.jpg scene_graph.json google/gemini-pro-1.5

# Generate abstract drawing only
uv run python abstract_drawer.py scene_graph.json output.png
```

## Supported Models

Via OpenRouter, you can use any vision-capable model:
- `anthropic/claude-3.5-sonnet` (default, recommended)
- `openai/gpt-4o`
- `google/gemini-pro-1.5`
- `openai/gpt-4-vision-preview`
- And many more at [openrouter.ai/models](https://openrouter.ai/models)

## How It Works

**Stage 1: Scene Graph Extraction**
- Input: Photo
- Process: Analyze image using vision model via OpenRouter
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

# Use default model (Claude 3.5 Sonnet)
pipeline = PhotoToAbstractPipeline()
scene_graph = pipeline.process("photo.jpg", "output.png")

# Use a different model
pipeline = PhotoToAbstractPipeline(model="openai/gpt-4o")
scene_graph = pipeline.process("photo.jpg", "output.png")
```
