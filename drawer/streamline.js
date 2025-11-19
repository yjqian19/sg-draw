/**
 * Streamline integration and smooth drawing
 */

/**
 * Integrate a streamline starting from (x0, y0)
 * @param {number} x0 - Starting X coordinate
 * @param {number} y0 - Starting Y coordinate
 * @param {FlowField} flowField - Flow field data
 * @param {number} stepSize - Integration step size
 * @param {number} maxLength - Maximum number of steps
 * @param {number} minSpeed - Minimum speed to continue
 * @returns {Array} Array of {x, y} points
 */
function integrateStreamline(x0, y0, flowField, stepSize = 2.0, maxLength = 1000, minSpeed = 0.001) {
    let points = [{ x: x0, y: y0 }];
    let x = x0;
    let y = y0;
    let visited = new Set();

    for (let i = 0; i < maxLength; i++) {
        // Check bounds
        if (x < 0 || x >= flowField.width - 1 || y < 0 || y >= flowField.height - 1) {
            break;
        }

        // Check if visited (avoid overlapping lines)
        let key = Math.floor(x) + ',' + Math.floor(y);
        if (visited.has(key)) {
            break;
        }
        visited.add(key);

        // Get gradient
        let grad = flowField.getGradient(x, y);
        let u = grad.u;
        let v = grad.v;

        // Check speed
        let speed = Math.sqrt(u * u + v * v);
        if (speed < minSpeed) {
            break;
        }

        // Normalize and step
        u /= (speed + 1e-8);
        v /= (speed + 1e-8);

        x += u * stepSize;
        y += v * stepSize;

        points.push({ x, y });
    }

    return points.length > 10 ? points : [];
}

/**
 * Smooth streamline using Catmull-Rom interpolation
 * @param {Array} points - Array of {x, y} points
 * @returns {Array} Smoothed points
 */
function smoothStreamline(points) {
    if (points.length < 2) return points;

    // Optimize: reduce interpolation points for performance
    // Use adaptive step size based on segment length
    let smoothed = [];
    for (let i = 0; i < points.length - 1; i++) {
        let p0 = i > 0 ? points[i - 1] : points[i];
        let p1 = points[i];
        let p2 = points[i + 1];
        let p3 = i < points.length - 2 ? points[i + 2] : points[i + 1];

        // Calculate segment length to determine interpolation density
        let dx = p2.x - p1.x;
        let dy = p2.y - p1.y;
        let segmentLength = Math.sqrt(dx * dx + dy * dy);

        // Adaptive step: shorter segments = fewer points, longer = more
        let step = segmentLength < 5 ? 0.2 : (segmentLength < 20 ? 0.15 : 0.1);

        // Catmull-Rom interpolation
        for (let t = 0; t < 1; t += step) {
            let x = catmullRom(p0.x, p1.x, p2.x, p3.x, t);
            let y = catmullRom(p0.y, p1.y, p2.y, p3.y, t);
            smoothed.push({ x, y });
        }
    }
    return smoothed;
}

/**
 * Catmull-Rom spline interpolation
 */
function catmullRom(p0, p1, p2, p3, t) {
    let t2 = t * t;
    let t3 = t2 * t;
    return 0.5 * (
        (2 * p1) +
        (-p0 + p2) * t +
        (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
        (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    );
}

/**
 * Draw streamline with smooth curve
 * @param {Array} points - Array of {x, y} points
 * @param {FlowField} flowField - Flow field for depth lookup
 * @param {string} colorScheme - Color scheme name
 * @param {number} lineWidth - Line width
 * @param {boolean} smooth - Use smooth curve interpolation
 */
function drawStreamline(points, flowField, colorScheme = 'ocean', lineWidth = 1.5, smooth = true) {
    if (points.length < 2) return;

    // Smooth if requested
    let drawPoints = smooth ? smoothStreamline(points) : points;

    // Draw line segments with gradient color
    for (let i = 0; i < drawPoints.length - 1; i++) {
        let p1 = drawPoints[i];
        let p2 = drawPoints[i + 1];

        // Get depth at midpoint
        let midX = (p1.x + p2.x) / 2;
        let midY = (p1.y + p2.y) / 2;
        let depth = flowField.getDepth(midX, midY);

        // Get color
        let c = depthToColor(depth, colorScheme);
        stroke(c);
        strokeWeight(lineWidth);

        line(p1.x, p1.y, p2.x, p2.y);
    }
}
