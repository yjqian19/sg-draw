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
    smooth: true
};

// UI elements
let densitySlider, stepSizeSlider, maxLengthSlider, lineWidthSlider;
let colorSchemeSelect;

// Debounce timer for streamline generation
let generateTimer = null;

function preload() {
    // Try to load default data file
    // User can also load via file input
}

function setup() {
    // Create canvas with black background
    let container = select('#canvas-container');
    let canvas = createCanvas(canvasWidth, canvasHeight);
    canvas.parent(container);

    // Setup UI controls
    setupControls();
}

function initializeFlowField() {
    if (!flowField) return;

    flowField = new FlowField(flowField);
    canvasWidth = flowField.width;
    canvasHeight = flowField.height;
    resizeCanvas(canvasWidth, canvasHeight);

    // Generate streamlines
    generateStreamlines();
}

function setupControls() {
    // File input
    select('#dataFile').changed(loadDataFile);

    // Density slider (1-30, more dense range)
    densitySlider = select('#density');
    densitySlider.input(() => {
        params.density = parseFloat(densitySlider.value());
        select('#densityValue').html(params.density.toFixed(1));
        debouncedGenerateStreamlines();
    });

    // Step size slider
    stepSizeSlider = select('#stepSize');
    stepSizeSlider.input(() => {
        params.stepSize = parseFloat(stepSizeSlider.value());
        select('#stepSizeValue').html(params.stepSize.toFixed(1));
        debouncedGenerateStreamlines();
    });

    // Max length slider
    maxLengthSlider = select('#maxLength');
    maxLengthSlider.input(() => {
        params.maxLength = parseInt(maxLengthSlider.value());
        select('#maxLengthValue').html(params.maxLength);
        debouncedGenerateStreamlines();
    });

    // Line width slider
    lineWidthSlider = select('#lineWidth');
    lineWidthSlider.input(() => {
        params.lineWidth = parseFloat(lineWidthSlider.value());
        select('#lineWidthValue').html(params.lineWidth.toFixed(1));
    });

    // Color scheme select
    colorSchemeSelect = select('#colorScheme');
    colorSchemeSelect.changed(() => {
        params.colorScheme = colorSchemeSelect.value();
    });

    // Save button
    select('#saveBtn').mousePressed(saveImage);
}

function loadDataFile() {
    let file = select('#dataFile').elt.files[0];
    if (file) {
        let reader = new FileReader();
        reader.onload = function(e) {
            try {
                flowField = JSON.parse(e.target.result);
                initializeFlowField();
            } catch (err) {
                console.error('Error loading file:', err);
                alert('Error loading file. Please check the file format.');
            }
        };
        reader.readAsText(file);
    }
}

// Debounced version - waits for user to stop adjusting
function debouncedGenerateStreamlines() {
    if (generateTimer) {
        clearTimeout(generateTimer);
    }
    generateTimer = setTimeout(() => {
        generateStreamlines();
    }, 300); // Wait 300ms after user stops adjusting
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
    }, 10);
}

function draw() {
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
            params.smooth
        );
    }
}

function keyPressed() {
    if (key === 's' || key === 'S') {
        saveImage();
    }
}

function saveImage() {
    if (!flowField) return;

    let filename = 'flow_field_' + new Date().getTime() + '.png';
    saveCanvas(filename);
    console.log('Image saved:', filename);
}
