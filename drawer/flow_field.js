/**
 * Flow field data loading and query interface
 */

class FlowField {
    constructor(jsonData) {
        this.width = jsonData.width;
        this.height = jsonData.height;

        // Convert 2D arrays from JSON
        this.depth = jsonData.depth;
        this.U = jsonData.U;
        this.V = jsonData.V;

        // Compute speed (gradient magnitude) for each point
        this.speed = [];
        this.maxSpeed = 0;
        for (let y = 0; y < this.height; y++) {
            this.speed[y] = [];
            for (let x = 0; x < this.width; x++) {
                let u = this.U[y][x];
                let v = this.V[y][x];
                let s = Math.sqrt(u * u + v * v);
                this.speed[y][x] = s;
                if (s > this.maxSpeed) {
                    this.maxSpeed = s;
                }
            }
        }
    }

    /**
     * Bilinear interpolation to get gradient at sub-pixel coordinates
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @returns {Object} {u, v} gradient components
     */
    getGradient(x, y) {
        // Clamp to valid range
        x = constrain(x, 0, this.width - 1);
        y = constrain(y, 0, this.height - 1);

        // Get integer coordinates
        let ix = Math.floor(x);
        let iy = Math.floor(y);

        // Clamp to array bounds
        ix = constrain(ix, 0, this.width - 2);
        iy = constrain(iy, 0, this.height - 2);

        // Fractional parts
        let fx = x - ix;
        let fy = y - iy;

        // Bilinear interpolation
        let u = (1 - fx) * (1 - fy) * this.U[iy][ix] +
                fx * (1 - fy) * this.U[iy][ix + 1] +
                (1 - fx) * fy * this.U[iy + 1][ix] +
                fx * fy * this.U[iy + 1][ix + 1];

        let v = (1 - fx) * (1 - fy) * this.V[iy][ix] +
                fx * (1 - fy) * this.V[iy][ix + 1] +
                (1 - fx) * fy * this.V[iy + 1][ix] +
                fx * fy * this.V[iy + 1][ix + 1];

        return { u, v };
    }

    /**
     * Get depth value at coordinates (with bilinear interpolation)
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @returns {number} Depth value [0, 1]
     */
    getDepth(x, y) {
        x = constrain(x, 0, this.width - 1);
        y = constrain(y, 0, this.height - 1);

        let ix = Math.floor(x);
        let iy = Math.floor(y);

        ix = constrain(ix, 0, this.width - 2);
        iy = constrain(iy, 0, this.height - 2);

        let fx = x - ix;
        let fy = y - iy;

        let depth = (1 - fx) * (1 - fy) * this.depth[iy][ix] +
                    fx * (1 - fy) * this.depth[iy][ix + 1] +
                    (1 - fx) * fy * this.depth[iy + 1][ix] +
                    fx * fy * this.depth[iy + 1][ix + 1];

        return depth;
    }

    /**
     * Get speed at coordinates
     * @param {number} x - X coordinate
     * @param {number} y - Y coordinate
     * @returns {number} Speed value
     */
    getSpeed(x, y) {
        x = constrain(x, 0, this.width - 1);
        y = constrain(y, 0, this.height - 1);

        let ix = Math.floor(x);
        let iy = Math.floor(y);

        ix = constrain(ix, 0, this.width - 2);
        iy = constrain(iy, 0, this.height - 2);

        let fx = x - ix;
        let fy = y - iy;

        let speed = (1 - fx) * (1 - fy) * this.speed[iy][ix] +
                    fx * (1 - fy) * this.speed[iy][ix + 1] +
                    (1 - fx) * fy * this.speed[iy + 1][ix] +
                    fx * fy * this.speed[iy + 1][ix + 1];

        return speed;
    }
}
