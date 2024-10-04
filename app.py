import pygame
import sys
import math
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
from datetime import datetime

# Flask setup
app = Flask(__name__)
socketio = SocketIO(app)

# Increase window size and set up scrolling
size = (width, height) = 1420, 420
pygame.init()
win = pygame.display.set_mode(size)
clock = pygame.time.Clock()

rows, cols = 42, 142
COLOR = (255, 100, 98) 
SURFACE_COLOR = (167, 255, 100) 

grid = []
openSet, closeSet = [], []
path = []

# Increase cell size for visibility
cell_size = 10
total_width = cols * cell_size
total_height = rows * cell_size

# Scrolling variables
scroll_x = 0
scroll_y = 0
scroll_speed = 30

class Sprite(pygame.sprite.Sprite):
    def __init__(self, color, height, width):
        super().__init__()
        self.original_image = pygame.Surface([width, height])  # Keep the original unrotated image
        self.original_image.fill(SURFACE_COLOR)
        self.original_image.set_colorkey(COLOR)
        
        pygame.draw.rect(self.original_image, color, pygame.Rect(0, 0, width, height))
        self.image = self.original_image  # This is the image we will rotate
        self.rect = self.image.get_rect()

        self.angle = 0  # Angle of rotation (in degrees)
        self.lidar_range = 80  # Maximum range of lidar
        self.lidar_count = 5  # Number of lidar lines

    def update(self):
        # Rotate the sprite based on its angle relative to the original image
        self.image = pygame.transform.rotate(self.original_image, -self.angle)  # Rotate the original image
        self.rect = self.image.get_rect(center=self.rect.center)  # Update the rect to keep sprite centered

    def draw_lidar(self, screen, walls, sprites):
        center_x = self.rect.centerx
        center_y = self.rect.centery

        for i in range(self.lidar_count):
            # Calculate the angle for each LIDAR line
            angle = self.angle - 50 + (100 / (self.lidar_count - 1)) * i
            angle_rad = math.radians(angle)
            
            end_x = center_x + self.lidar_range * math.cos(angle_rad)
            end_y = center_y + self.lidar_range * math.sin(angle_rad)
            
            # Check for collision with walls
            wall_collision = self.check_collision(center_x, center_y, end_x, end_y, walls)
            
            # Check for collision with other sprites
            sprite_collision = self.check_sprite_collision(center_x, center_y, end_x, end_y, sprites)
            
            # Use the closest collision point
            if wall_collision and sprite_collision:
                collision_point = min(wall_collision, sprite_collision, key=lambda p: (p[0]-center_x)**2 + (p[1]-center_y)**2)
            elif wall_collision:
                collision_point = wall_collision
            elif sprite_collision:
                collision_point = sprite_collision
            else:
                collision_point = (end_x, end_y)
            
            # Draw the lidar line
            pygame.draw.line(screen, (0, 200, 255), (center_x, center_y), collision_point, 2)

    def rotate(self, angle):
        # Update the angle
        self.angle += angle
        self.angle %= 360  # Keep the angle between 0 and 360 degrees

    def check_collision(self, x1, y1, x2, y2, walls):
        closest_point = None
        min_distance = float('inf')

        for wall in walls:
            # Check collision with each side of the wall
            for i in range(4):
                wx1, wy1 = wall.rect.topleft if i == 0 else wall.rect.topright if i == 1 else wall.rect.bottomright if i == 2 else wall.rect.bottomleft
                wx2, wy2 = wall.rect.topright if i == 0 else wall.rect.bottomright if i == 1 else wall.rect.bottomleft if i == 2 else wall.rect.topleft
                
                point = self.line_intersection(((x1, y1), (x2, y2)), ((wx1, wy1), (wx2, wy2)))
                if point:
                    distance = (point[0] - x1)**2 + (point[1] - y1)**2
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = point

        return closest_point

    def check_sprite_collision(self, x1, y1, x2, y2, sprites):
        closest_point = None
        min_distance = float('inf')

        for sprite in sprites:
            if sprite != self:  # Don't check collision with self
                # Check collision with sprite's bounding box
                rect = sprite.rect
                points = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]
                for i in range(4):
                    point = self.line_intersection(((x1, y1), (x2, y2)), (points[i], points[(i+1)%4]))
                    if point:
                        distance = (point[0] - x1)**2 + (point[1] - y1)**2
                        if distance < min_distance:
                            min_distance = distance
                            closest_point = point

        return closest_point

    @staticmethod
    def line_intersection(line1, line2):
        (x1, y1), (x2, y2) = line1
        (x3, y3), (x4, y4) = line2

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if den == 0:
            return None  # Lines are parallel

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 <= t <= 1 and 0 <= u <= 1:
            px = x1 + t * (x2 - x1)
            py = y1 + t * (y2 - y1)
            return (px, py)
        else:
            return None  # Intersection point is not on both line segments
        

# class Sprite(pygame.sprite.Sprite): 
#     def __init__(self, color, height, width): 
#         super().__init__() 

#         self.image = pygame.Surface([width, height]) 
#         self.image.fill(SURFACE_COLOR) 
#         self.image.set_colorkey(COLOR) 
        
#         pygame.draw.rect(self.image, 
#                         color, 
#                         pygame.Rect(0, 0, width, height)) 

#         self.rect = self.image.get_rect() 

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill((0, 0, 0))  # Fill with black to represent a wall
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Spot:
    def __init__(self, i, j):
        self.x, self.y = i, j
        self.f, self.g, self.h = 0, 0, 0
        self.neighbors = []
        self.prev = None
        self.wall = False
        self.charge = False
        
    def show(self, win, col, walls_group=None):
        x = self.x * cell_size - scroll_x
        y = self.y * cell_size - scroll_y

        if self.wall:
            col = (0, 0, 0)
            if 0 <= x < width and 0 <= y < height:
                # Create a Wall object and add it to the walls group
                wall = Wall(x, y, cell_size, cell_size)
                walls_group.add(wall)
        if self.charge:
            col = (0, 255, 0)

        if 0 <= x < width and 0 <= y < height:
            pygame.draw.rect(win, col, (x, y, cell_size-1, cell_size-1))
    
    def add_neighbors(self, grid):
        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        for dx, dy in directions:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                self.neighbors.append(grid[ny][nx])

def heuristics(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def a_star():
    openSet = [start]
    flag = False
    winner = 0

    while openSet:
        for i in range(len(openSet)):
            if openSet[i].f < openSet[winner].f:
                winner = i

        current = openSet[winner]
        
        if current == end:
            temp = current
            while temp.prev:
                path.append(temp.prev)
                temp = temp.prev 
            if not flag:
                flag = True
                print("Done")
                return path
            else:
                continue

        # print(current.x, current.y)
        if flag == False:
            openSet.remove(current)
            closeSet.append(current)

            for neighbor in current.neighbors:
                if neighbor in closeSet or neighbor.wall:
                    continue
                if current.x != end.x and 0<current.y<5:
                    tempG = current.g + 1
                elif current.x == end.x and current.y>5:
                    tempG = current.g + 1
                else:
                    tempG = current.g + 5

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

    return None

def main():
    global scroll_x, scroll_y
    path = None
    startflag = False

    for wallx in range(12, 140, 12):
        for wallxx in range(8):
            for wally in range(5, rows):
                grid[wally][wallx+wallxx].wall = True
    
    for chargex in range(2,8):
        for chargey in range(5, rows):
            grid[chargey][chargex].charge = True

    for parkx in range(1, cols, 2):
        grid[0][parkx].wall = True


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    startTime = datetime.now()
                    startflag = True

        # Handle scrolling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            scroll_x = max(0, scroll_x - scroll_speed)
        if keys[pygame.K_RIGHT]:
            scroll_x = min(total_width - width, scroll_x + scroll_speed)
        if keys[pygame.K_UP]:
            scroll_y = max(0, scroll_y - scroll_speed)
        if keys[pygame.K_DOWN]:
            scroll_y = min(total_height - height, scroll_y + scroll_speed)

        if startflag and path is None:
            if len(openSet) > 0:
                path = a_star()
                if path == None:
                    Tk().wm_withdraw()
                    messagebox.showinfo("No Solution", "There was no solution" )
                else:
                    print(datetime.now() - startTime)

        win.fill((0, 20, 20))
        walls_group = pygame.sprite.Group()
        for i in range(rows):
            for j in range(cols):
                spot = grid[i][j]
                spot.show(win, (255, 255, 255), walls_group)
                if path and spot in path:
                    spot.show(win, (255, 0, 0))
                elif spot in closeSet:
                    spot.show(win, (222, 165, 164))
                elif spot in openSet:
                    spot.show(win, (173, 208, 179))
                if spot == end:
                    spot.show(win, (0, 120, 255))


        object_.draw_lidar(win, walls_group, all_sprites_list)
        object1_.draw_lidar(win, walls_group, all_sprites_list)
        all_sprites_list.update() 
        all_sprites_list.draw(win) 
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    #Create the grid
    for i in range(rows):
        arr = []
        for j in range(cols):
            arr.append(Spot(j, i))
        grid.append(arr)

    for i in range(rows):
        for j in range(cols):
            grid[i][j].add_neighbors(grid)

    start = grid[0][0]
    end = grid[rows-1][cols-1]

    openSet.append(start)

    all_sprites_list = pygame.sprite.Group() 
    object_ = Sprite((0,0,255), 10, 20) 
    object_.rect.x = 200
    object_.rect.y = 20
    object_.rotate(95)
    all_sprites_list.add(object_) 

    object1_ = Sprite((0,0,255), 10, 20) 
    object1_.rect.x = 250
    object1_.rect.y = 20
    object1_.rotate(180)
    all_sprites_list.add(object1_) 
    main()

@app.route('/')
def index():
    return render_template('index.html')

