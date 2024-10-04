// static/script.js

const canvas = document.getElementById('gridCanvas');
const ctx = canvas.getContext('2d');
const startButton = document.getElementById('startButton');

const cellSize = 10;
const rows = 42;
const cols = 70;

// Initialize grid data
let grid = [];

// Fetch grid data from backend
function fetchGrid() {
    fetch('/api/grid')
        .then(response => response.json())
        .then(data => {
            grid = data;
            drawGrid();
        });
}

// Draw the grid on the canvas
function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < rows; i++) {
        for (let j = 0; j < cols; j++) {
            const spot = grid[i][j];
            let color = '#fff'; // Default white

            if (spot.wall) {
                color = '#000'; // Black for walls
            }
            if (spot.charge) {
                color = '#0f0'; // Green for charge
            }

            // Draw each cell
            ctx.fillStyle = color;
            ctx.fillRect(j * cellSize, i * cellSize, cellSize - 1, cellSize - 1);
        }
    }
}

// Handle canvas clicks to set/remove walls
canvas.addEventListener('click', function(event) {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / cellSize);
    const y = Math.floor((event.clientY - rect.top) / cellSize);

    if (x >= 0 && x < cols && y >= 0 && y < rows) {
        const currentState = grid[y][x].wall;
        const newState = !currentState;

        // Update wall state on backend
        fetch('/api/set_wall', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ x: x, y: y, state: newState })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                grid[y][x].wall = newState;
                drawGrid();
            }
        });
    }
});

// Start pathfinding
startButton.addEventListener('click', function() {
    fetch('/api/start_pathfinding', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.path) {
            drawPath(data.path);
        } else if (data.status === 'No Solution') {
            alert('No solution found!');
        }
    });
});

// Draw the path on the canvas
function drawPath(path) {
    path.forEach(point => {
        ctx.fillStyle = '#f00'; // Red for path
        ctx.fillRect(point.x * cellSize, point.y * cellSize, cellSize - 1, cellSize - 1);
    });
}

// Initial fetch and draw
fetchGrid();