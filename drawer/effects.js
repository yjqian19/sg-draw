/**
 * Visual effects: point distribution, binary text, etc.
 */

/**
 * Convert streamline to points with density variation
 * @param {Array} points - Streamline points
 * @param {number} centerDensity - Points per segment at center
 * @param {number} edgeDensity - Points per segment at edges
 * @returns {Array} Array of {x, y, dist} points (dist is distance from center)
 */
function streamlineToPoints(points, centerDensity = 10, edgeDensity = 2) {
    if (points.length < 2) return [];

    let result = [];
    let centerIdx = points.length / 2;

    for (let i = 0; i < points.length - 1; i++) {
        // Calculate distance from center [0, 1]
        let distFromCenter = Math.abs(i - centerIdx) / points.length;

        // Density function: center dense, edge sparse
        let density = lerp(centerDensity, edgeDensity, distFromCenter);

        // Generate points along this segment
        let p1 = points[i];
        let p2 = points[i + 1];
        let dx = p2.x - p1.x;
        let dy = p2.y - p1.y;
        let segmentLength = Math.sqrt(dx * dx + dy * dy);

        if (segmentLength > 0) {
            let numPoints = Math.floor(density);
            for (let j = 0; j < numPoints; j++) {
                let t = j / numPoints;
                // Add random offset
                let offsetX = random(-1, 1);
                let offsetY = random(-1, 1);

                result.push({
                    x: p1.x + dx * t + offsetX,
                    y: p1.y + dy * t + offsetY,
                    dist: distFromCenter
                });
            }
        }
    }

    return result;
}

/**
 * Draw points from streamline
 * @param {Array} points - Streamline points
 * @param {FlowField} flowField - Flow field for depth lookup
 * @param {string} colorScheme - Color scheme name
 * @param {number} centerDensity - Points at center
 * @param {number} edgeDensity - Points at edge
 */
function drawPointsEffect(points, flowField, colorScheme = 'ocean', centerDensity = 10, edgeDensity = 2) {
    let pointData = streamlineToPoints(points, centerDensity, edgeDensity);

    noStroke();
    for (let p of pointData) {
        let depth = flowField.getDepth(p.x, p.y);
        let c = depthToColor(depth, colorScheme);
        fill(c);

        // Size based on distance from center
        let size = map(p.dist, 0, 1, 3, 1);
        ellipse(p.x, p.y, size, size);
    }
}

/**
 * Draw binary text (0101) along streamline
 * @param {Array} points - Streamline points
 * @param {FlowField} flowField - Flow field for depth lookup
 * @param {string} colorScheme - Color scheme name
 * @param {string} text - Text pattern (default: "0101")
 */
function drawBinaryEffect(points, flowField, colorScheme = 'ocean', text = "0101") {
    if (points.length < 2) return;

    textAlign(CENTER, CENTER);
    textSize(8);

    let spacing = 8;  // Distance between characters
    let currentDist = 0;
    let charIndex = 0;

    for (let i = 0; i < points.length - 1; i++) {
        let p1 = points[i];
        let p2 = points[i + 1];
        let dx = p2.x - p1.x;
        let dy = p2.y - p1.y;
        let segmentLength = Math.sqrt(dx * dx + dy * dy);

        // Calculate angle for text rotation
        let angle = Math.atan2(dy, dx);

        // Place characters along segment
        while (currentDist < segmentLength) {
            let t = currentDist / segmentLength;
            let x = p1.x + dx * t;
            let y = p1.y + dy * t;

            // Get depth and color
            let depth = flowField.getDepth(x, y);
            let c = depthToColor(depth, colorScheme);
            fill(c);

            // Draw character with rotation
            push();
            translate(x, y);
            rotate(angle);
            text(text[charIndex % text.length], 0, 0);
            pop();

            charIndex++;
            currentDist += spacing;
        }

        currentDist -= segmentLength;
    }
}
