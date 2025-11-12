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

## What's Next

- Make the flowers feel more natural
- Try other drawing styles
- Experiment with different types of input images
- Maybe let the computer make some artistic choices on its own

---

*This project explores the tension between structure and spontaneity, between what the photo tells us and what we choose to create from that information.*
