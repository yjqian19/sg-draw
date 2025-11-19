/**
 * Color scheme management for flow field visualization
 */

const ColorSchemes = {
    ocean: {
        // Deep blue -> light blue/green (similar to Python version)
        shallow: [174, 225, 165],   // Light green (#aed581)
        deep: [10, 74, 122]          // Deep blue (#0a4a7a)
    },
    sunset: {
        shallow: [255, 200, 150],   // Light orange
        deep: [100, 50, 150]        // Dark purple
    },
    white: {
        shallow: [255, 255, 255],   // White (near)
        deep: [255, 255, 255],      // White (far, but will be transparent)
        useAlpha: true              // Use alpha channel for transparency
    }
};

/**
 * Apply non-linear transformation to emphasize deep areas
 * Uses power function to make color changes more dramatic in deep areas
 * @param {number} depth - Depth value [0, 1] (0=deep, 1=shallow)
 * @param {number} power - Power factor (default: 1.5, higher = more dramatic)
 * @returns {number} Transformed depth value
 */
function transformDepth(depth, power = 1.5) {
    // Invert: 0=shallow, 1=deep
    let depthInv = 1.0 - depth;
    // Apply power function to emphasize deep areas
    let transformed = 1.0 - Math.pow(depthInv, power);
    return transformed;
}

/**
 * Convert depth value to color based on scheme
 * @param {number} depth - Depth value [0, 1] (0=deep, 1=shallow)
 * @param {string} scheme - Color scheme name
 * @param {boolean} emphasizeDeep - Apply non-linear transformation (default: true)
 * @returns {p5.Color} p5.js color object
 */
function depthToColor(depth, scheme = 'ocean', emphasizeDeep = true) {
    // Apply non-linear transformation to emphasize deep areas
    let transformedDepth = emphasizeDeep ? transformDepth(depth, 1.5) : depth;

    const colors = ColorSchemes[scheme];
    if (!colors) {
        return color(128, 128, 128);  // Default gray
    }

    // White scheme: white (near/shallow) to transparent (far/deep)
    if (scheme === 'white' && colors.useAlpha) {
        // Depth: 0=deep (transparent), 1=shallow (white)
        // Alpha: 0 (transparent) to 255 (opaque)
        let alpha = map(transformedDepth, 0, 1, 0, 255);
        return color(255, 255, 255, alpha);
    }

    // Interpolate between shallow and deep using transformed depth
    let r = lerp(colors.deep[0], colors.shallow[0], transformedDepth);
    let g = lerp(colors.deep[1], colors.shallow[1], transformedDepth);
    let b = lerp(colors.deep[2], colors.shallow[2], transformedDepth);

    return color(r, g, b);
}

/**
 * Get color for speed (gradient magnitude)
 * @param {number} speed - Speed value
 * @param {number} maxSpeed - Maximum speed for normalization
 * @returns {p5.Color} p5.js color object
 */
function speedToColor(speed, maxSpeed = 1.0) {
    let normalized = constrain(speed / maxSpeed, 0, 1);
    // Use viridis-like colormap: dark blue -> green -> yellow
    let hue = map(normalized, 0, 1, 240, 60);
    let saturation = 80;
    let lightness = map(normalized, 0, 1, 20, 90);
    return color(hue, saturation, lightness);
}
