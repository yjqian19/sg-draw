/**
 * Color scheme management for flow field visualization
 */

const ColorSchemes = {
    ocean: {
        shallow: [135, 206, 250],  // Light blue
        deep: [0, 51, 102]          // Dark blue
    },
    sunset: {
        shallow: [255, 200, 150],   // Light orange
        deep: [100, 50, 150]        // Dark purple
    },
    forest: {
        shallow: [144, 238, 144],   // Light green
        deep: [34, 139, 34]          // Dark green
    },
    rainbow: null  // Special case, uses HSL
};

/**
 * Convert depth value to color based on scheme
 * @param {number} depth - Depth value [0, 1] (0=deep, 1=shallow)
 * @param {string} scheme - Color scheme name
 * @returns {p5.Color} p5.js color object
 */
function depthToColor(depth, scheme = 'ocean') {
    if (scheme === 'rainbow') {
        // Rainbow: HSL color based on depth
        let hue = map(depth, 0, 1, 200, 360);  // Blue to red
        let saturation = 80;
        let lightness = map(depth, 0, 1, 30, 90);  // Dark to light
        return color(hue, saturation, lightness);
    }

    const colors = ColorSchemes[scheme];
    if (!colors) {
        return color(128, 128, 128);  // Default gray
    }

    // Interpolate between shallow and deep
    let r = lerp(colors.deep[0], colors.shallow[0], depth);
    let g = lerp(colors.deep[1], colors.shallow[1], depth);
    let b = lerp(colors.deep[2], colors.shallow[2], depth);

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
