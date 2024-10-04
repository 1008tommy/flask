# pathfinding.py
import math

class Spot:
    def __init__(self, i, j):
        self.x, self.y = i, j
        self.f, self.g, self.h = 0, 0, 0
        self.neighbors = []
        self.prev = None
        self.wall = False
        self.charge = False

    def add_neighbors(self, grid, cols, rows):
        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        for dx, dy in directions:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                self.neighbors.append(grid[ny][nx])

def heuristics(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def create_grid(rows, cols):
    grid = []
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append(Spot(j, i))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            grid[i][j].add_neighbors(grid, cols, rows)
    return grid

def a_star(grid, start, end):
    openSet = [start]
    closeSet = []
    path = []
    flag = False

    while openSet:
        winner = 0
        for i in range(len(openSet)):
            if openSet[i].f < openSet[winner].f:
                winner = i
        current = openSet[winner]

        if current == end:
            temp = current
            while temp.prev:
                path.append({'x': temp.x, 'y': temp.y})
                temp = temp.prev
            flag = True
            return path

        openSet.pop(winner)
        closeSet.append(current)

        for neighbor in current.neighbors:
            if neighbor in closeSet or neighbor.wall:
                continue
            tempG = current.g + 1  # Adjust as needed for your logic

            newPath = False
            if neighbor in openSet:
                if tempG < neighbor.g:
                    neighbor.g = tempG
                    newPath = True
            else:
                neighbor.g = tempG
                newPath = True
                openSet.append(neighbor)

            if newPath:
                neighbor.h = heuristics(neighbor, end)
                neighbor.f = neighbor.g + neighbor.h
                neighbor.prev = current

    return None  # No path found