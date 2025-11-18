# SG-Draw

## The Idea

I believe that good photographs have something universal in their composition - the way things are arranged, their proportions, the balance between elements. What if we could extract this underlying order and use it as a foundation for new creative work?

So the process goes: **Photo → Extract composition → Create something new based on that structure**

## How It Works

### Finding the Structure
I tried a few different ways to understand what's in a photo:

**First attempt:** Used a Vision Language Model (OpenAI's API) to describe the image. It could tell me what was there, but the descriptions were too vague - "several people on a street" doesn't give me the precise positions and proportions I needed.

**Second attempt:** Tried Semantic Segmentation (SegFormer model) to identify types of objects like "sky", "road", "building". Better, but it groups everything together - all people become one blob, losing the individual elements that make composition interesting.

**Final approach:** Switched to Instance Segmentation (Mask2Former from Hugging Face). This recognizes each individual thing separately - every person, every car, every tree as its own element with its own position and size.

This last one worked best because it preserves the individual pieces that create the composition's rhythm and balance.

### Drawing with Dots

Once I know where everything is and how big it is, I can redraw the scene in different ways. I tried a few styles:

**Circles** - Just simple circles for each element. Clean and geometric.

**Density Field** - Dots scattered across the canvas, clustering where things were in the original photo. Like pointillism, but driven by the photo's composition.

**Flowers** - Each element becomes a flower made of dots. Different colors for different types of objects. Petals can be wide or narrow, curved or straight. Each flower randomly rotates so it feels more organic.

## Current Results

It's still a work in progress. The flowers sometimes look a bit stiff, the density fields can be too chaotic or too organized. But the core idea works - you can feel the original composition in the abstract result.

## Pipelines

### Segmentation
Extract and visualize elements from photos:
```bash
python pipeline_segmentation.py test02.jpg
```

### Depth Estimation
Extract depth maps and create depth-based visualizations:
```bash
python pipeline_depth.py test02.jpg
```

## What's Next

- Use depth information to detect composition guidelines (perspective lines, vanishing points)
- Explore depth-tangent flows (lines following contours instead of crossing them)
- Combine segmentation with depth for layered compositions
- Make the flowers feel more natural
- Try other drawing styles
- Experiment with different types of input images

---

## Drawing with Depth

Depth estimation opened a different way of seeing. Not just what's in the frame, but how space is organized - what's close, what's far, how the eye travels through layers.

I use Depth-Anything-V2, which gives me a depth map: a grayscale image where darker means farther, lighter means closer. But a depth map alone is just data. The interesting question is how to make that spatial structure visible, tangible.

### Contour Lines

My first approach was to treat depth like topography. Just as contour lines on a map connect points of equal elevation, I draw lines connecting points of equal depth. The result feels like a topographic map of the image's spatial structure - dense lines where depth changes rapidly (edges, details), sparse lines in flat areas.

The dimensions I had to balance:
- **Density**: how many levels to slice the depth into
- **Smoothness**: how much to blur before extracting contours
- **Precision**: how closely contours follow depth changes
- **Color mapping**: encoding depth through gradients

It's like carving the image into layers and looking at it edge-on. You see the sculptural quality - how a face is not flat, how a building recedes, how a landscape folds.

### Flow Fields

Then I thought: what if depth was like a landscape, and I could show how water would flow through it?

Flow lines follow the gradient - they run perpendicular to contours, always moving from shallow (near) to deep (far). This creates something different: dynamic, directional, showing the pull of depth rather than its levels.

The technical challenge was making the lines feel right. I wanted them to:
- **Vary in width**: thin in flat areas, thick where depth changes dramatically
- **Respond non-linearly**: dramatic in deep areas, subtle in shallow ones
- **Fill the space**: dense but not cluttered
- **Feel natural**: color gradients from shallow (green) to deep (blue)
- **Match the organic quality** of the contour lines

The flow lines reveal depth structure in a way that feels like wind patterns or magnetic fields - something invisible made visible. They're neither realistic nor completely abstract, somewhere in between.

---

*This project explores the tension between structure and spontaneity, between what the photo tells us and what we choose to create from that information.*
