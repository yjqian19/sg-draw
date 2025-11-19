/**
 * Main p5.js sketch for flow field visualization
 * Focus: Streamline drawing only
 */

let flowField = null;
let streamlines = [];
let canvasWidth = 1200;
let canvasHeight = 675;

// Parameters
let params = {
    density: 4.5,
    stepSize: 2.0,
    maxLength: 1000,
    lineWidth: 1.5,
    colorScheme: 'ocean',
    depthPower: 1.5,
    invertDepth: false,
    smooth: true
};

// UI elements
let densitySlider, stepSizeSlider, maxLengthSlider, lineWidthSlider;
let colorSchemeSelect, depthPowerSlider, invertDepthCheckbox;
let densityValue, stepSizeValue, maxLengthValue, lineWidthValue;

function getNumberInputValue(element, fallback, min = -Infinity, max = Infinity) {
    let val = parseFloat(element.value());
    if (isNaN(val)) {
        val = fallback;
    }
    val = constrain(val, min, max);
    element.value(val);
    return val;
}


function setup() {
    // Create canvas with black background
    let container = select('#canvas-container');
    let canvas = createCanvas(canvasWidth, canvasHeight);
    canvas.parent(container);

    // Stop the draw loop - we'll only draw when Generate is clicked
    noLoop();

    // Setup UI controls
    setupControls();
}

function initializeFlowField() {
    if (!flowField) return;

    flowField = new FlowField(flowField);
    canvasWidth = flowField.width;
    canvasHeight = flowField.height;
    resizeCanvas(canvasWidth, canvasHeight);

    // Clear existing streamlines - user must click Generate to create new ones
    streamlines = [];

    // Render initial state (empty canvas with message)
    renderFlowField();
}

function setupControls() {
    // File input - still auto-loads when file is selected
    select('#dataFile').changed(loadDataFile);

    // Store references to UI elements
    densitySlider = select('#density');
    stepSizeSlider = select('#stepSize');
    maxLengthSlider = select('#maxLength');
    lineWidthSlider = select('#lineWidth');
    colorSchemeSelect = select('#colorScheme');
    depthPowerSlider = select('#depthPower');
    invertDepthCheckbox = select('#invertDepth');

    // Value display elements
    densityValue = select('#densityValue');
    stepSizeValue = select('#stepSizeValue');
    maxLengthValue = select('#maxLengthValue');
    lineWidthValue = select('#lineWidthValue');

    // Update display values when sliders change (but don't generate)
    // Use throttled updates to reduce DOM manipulation frequency
    const createThrottledUpdater = (display, formatter) => {
        let rafId = null;
        return (value) => {
            if (rafId) {
                cancelAnimationFrame(rafId);
            }
            rafId = requestAnimationFrame(() => {
                display.elt.textContent = formatter(value);
                rafId = null;
            });
        };
    };

    const updateDensity = createThrottledUpdater(densityValue, (v) => parseFloat(v).toFixed(1));
    const updateStepSize = createThrottledUpdater(stepSizeValue, (v) => parseFloat(v).toFixed(1));
    const updateMaxLength = createThrottledUpdater(maxLengthValue, (v) => parseInt(v));
    const updateLineWidth = createThrottledUpdater(lineWidthValue, (v) => parseFloat(v).toFixed(1));

    // Use native DOM events for better performance
    densitySlider.elt.addEventListener('input', (e) => {
        updateDensity(e.target.value);
    });
    stepSizeSlider.elt.addEventListener('input', (e) => {
        updateStepSize(e.target.value);
    });
    maxLengthSlider.elt.addEventListener('input', (e) => {
        updateMaxLength(e.target.value);
    });
    lineWidthSlider.elt.addEventListener('input', (e) => {
        updateLineWidth(e.target.value);
    });

    // Reset button
    select('#resetBtn').elt.addEventListener('click', (e) => {
        e.preventDefault();
        resetCanvas();
    });

    // Generate button - reads all values and generates
    select('#generateBtn').mousePressed(() => {
        if (!flowField) {
            alert('Please load a flow field JSON file first.');
            return;
        }
        // Read all input values when Generate is clicked
        updateParamsFromUI();
        generateStreamlines();
    });

    // Export SVG button
    select('#exportSvgBtn').mousePressed(() => {
        if (!flowField || streamlines.length === 0) {
            alert('Please generate a flow field first.');
            return;
        }
        exportSVGForLaser();
    });
}

function updateParamsFromUI() {
    // Read all values from UI elements and update params
    // For sliders, use .value() method
    params.density = parseFloat(densitySlider.value());
    params.stepSize = parseFloat(stepSizeSlider.value());
    params.maxLength = parseInt(maxLengthSlider.value());
    params.lineWidth = parseFloat(lineWidthSlider.value());
    params.colorScheme = colorSchemeSelect.value();
    params.depthPower = getNumberInputValue(depthPowerSlider, params.depthPower, 0.01, 2.5);
    params.invertDepth = invertDepthCheckbox.elt.checked;
}

function loadDataFile() {
    let file = select('#dataFile').elt.files[0];
    if (file) {
        let reader = new FileReader();
        reader.onload = function(e) {
            try {
                flowField = JSON.parse(e.target.result);
                initializeFlowField();
                // File loaded successfully - user must click Generate to create streamlines
            } catch (err) {
                console.error('Error loading file:', err);
                alert('Error loading file. Please check the file format.');
            }
        };
        reader.readAsText(file);
    }
}

function showLoading() {
    let loading = select('#loading').elt;
    loading.classList.add('show');
}

function hideLoading() {
    let loading = select('#loading').elt;
    loading.classList.remove('show');
}

function generateStreamlines() {
    if (!flowField) return;

    // Show loading indicator
    showLoading();

    // Use setTimeout to allow UI to update before heavy computation
    setTimeout(() => {
        console.log('Generating streamlines...');
        let startTime = performance.now();

        streamlines = [];

        // Generate starting points using stratified sampling
        // Density controls the grid size: higher density = more streamlines
        let gridSize = Math.floor(Math.sqrt(params.density * 100));
        let xStep = flowField.width / gridSize;
        let yStep = flowField.height / gridSize;

        for (let i = 0; i < gridSize; i++) {
            for (let j = 0; j < gridSize; j++) {
                // Add random jitter
                let x = i * xStep + random(-xStep / 2, xStep / 2);
                let y = j * yStep + random(-yStep / 2, yStep / 2);

                x = constrain(x, 0, flowField.width - 1);
                y = constrain(y, 0, flowField.height - 1);

                let points = integrateStreamline(
                    x, y,
                    flowField,
                    params.stepSize,
                    params.maxLength
                );

                if (points.length > 10) {
                    streamlines.push(points);
                }
            }
        }

        let endTime = performance.now();
        console.log(`Generated ${streamlines.length} streamlines in ${(endTime - startTime).toFixed(0)}ms`);

        // Hide loading indicator
        hideLoading();

        // Render once after generation is complete
        renderFlowField();
    }, 10);
}

function renderFlowField() {
    // Single render pass - draw everything once
    // Black background
    background(0);

    if (!flowField || streamlines.length === 0) {
        fill(100);
        textAlign(CENTER, CENTER);
        textSize(14);
        text('Load a flow field JSON file to begin', width / 2, height / 2);
        return;
    }

    // Draw streamlines
    for (let points of streamlines) {
        drawStreamline(
            points,
            flowField,
            params.colorScheme,
            params.lineWidth,
            params.smooth,
            {
                depthPower: params.depthPower,
                invertDepth: params.invertDepth
            }
        );
    }
}

function draw() {
    // Called once initially after setup() (noLoop() stops continuous drawing)
    // Delegate to renderFlowField() to avoid code duplication
    renderFlowField();
}

function resetCanvas() {
    // Clear streamlines
    streamlines = [];

    // Re-render to show empty state
    renderFlowField();
}

function exportSVGForLaser() {
    console.log('Exporting SVG for laser engraving...');

    // Create SVG header with precise dimensions
    let svg = '<?xml version="1.0" encoding="UTF-8"?>\n';
    svg += `<svg xmlns="http://www.w3.org/2000/svg" `;
    svg += `width="${canvasWidth}mm" height="${canvasHeight}mm" `;
    svg += `viewBox="0 0 ${canvasWidth} ${canvasHeight}">\n`;

    // Optional: Add metadata
    svg += `  <title>Flow Field for Laser Engraving</title>\n`;
    svg += `  <desc>Generated from flow field visualization - ${new Date().toISOString()}</desc>\n\n`;

    // Main group for all paths
    svg += `  <g id="flow-lines" stroke="black" fill="none" stroke-width="0.3" stroke-linecap="round" stroke-linejoin="round">\n`;

    // Convert each streamline to SVG path
    let pathCount = 0;
    for (let points of streamlines) {
        if (points.length < 2) continue; // Skip invalid paths

        // Build path data
        let pathData = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;

        for (let i = 1; i < points.length; i++) {
            pathData += ` L ${points[i].x.toFixed(2)} ${points[i].y.toFixed(2)}`;
        }

        svg += `    <path d="${pathData}" />\n`;
        pathCount++;
    }

    svg += `  </g>\n`;
    svg += `</svg>`;

    // Create download
    let filename = 'flow_field_laser_' + new Date().getTime() + '.svg';
    let blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    let url = URL.createObjectURL(blob);

    let link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Cleanup
    setTimeout(() => {
        URL.revokeObjectURL(url);
    }, 100);

    console.log(`SVG exported: ${filename} (${pathCount} paths)`);
}
