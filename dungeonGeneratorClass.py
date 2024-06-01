from __future__ import annotations
import pygame
import sys
import random
import math
import copy
import time


# Dungeon Generator Parameters
FINISH_THRESH: float = .3
ROOM_RANDOM: float = .7
DOOR_RANDOM: float = .65
PATH_LENGTH: int = 15
ALLOWED_FAILS: int = 3

# Global Colors
RED: tuple = (255, 0, 0)
GREEN: tuple = (0, 255, 0)
BLUE: tuple = (0, 0, 255)
BLACK: tuple = (0, 0, 0)
WHITE: tuple = (255, 255, 255)
ORANGE: tuple = (245, 164, 2)
YELLOW: tuple = (249, 252, 28)
GRAY: tuple = (105, 101, 100)
PINK: tuple = (252, 3, 223)

ROOM_EDGE_COLOR = ORANGE
DOOR_COLOR = BLUE


# Helper Functions / Objects

def log(message: str, key: str):
    # A function that will print the inputted debugging message if the key's debug type is set to true
    types: dict = {
        'converting': False,
        'add room': False,
        'add line': False,
        'place room': False,
        'generate finish': False,
        'overlap': False,
        'build dungeon': False,
        'rotated prefabs': False,
        'random door': False ,
        'True': True,
        'False': False
    }

    if types[key]:
        print(message)


class PygameDisplay:
    # A bordered pygame window with (0, 0) in bottom left rather than top left (pygame default)
    def __init__(self, innerWidth: int, innerHeight: int, borderThickness: int, backgroundColor: tuple,
                 borderColor: tuple):
        self.innerWidth = innerWidth
        self.innerHeight = innerHeight
        self.windowWidth = innerWidth + (2 * borderThickness)
        self.windowHeight = innerHeight + (2 * borderThickness)
        self.borderThickness = borderThickness
        self.backgroundColor = backgroundColor
        self.borderColor = borderColor
        pygame.init()
        self.screen = pygame.display.set_mode((self.windowWidth, self.windowHeight))
        pygame.display.set_caption("Dungeon Generator")
        self.screen.fill(self.borderColor)
        pygame.draw.rect(self.screen, self.backgroundColor, (self.borderThickness, self.borderThickness,
                                                             self.windowWidth - 2 * self.borderThickness,
                                                             self.windowHeight - 2 * self.borderThickness))

    def reset(self):
        # Reinitialized the pygame window for successive use
        self.screen.fill(self.borderColor)
        pygame.draw.rect(self.screen, self.backgroundColor, (self.borderThickness, self.borderThickness,
                                                             self.windowWidth - 2 * self.borderThickness,
                                                             self.windowHeight - 2 * self.borderThickness))
        pygame.display.update()

    def real(self, point: tuple, y_offset: int = 0):
        # Converts ordered pair from bottom-left-origin (input) to top-left-origin (for pygame built-in functions)
        x = point[0]
        y = point[1]
        log('Converting ' + str(x) + ', ' + str(y), 'converting')
        real_x = x + self.borderThickness
        real_y = self.windowHeight - (y + self.borderThickness + y_offset)
        return real_x, real_y

    def on(self, seconds: int = 100000):
        # Displays the pygame window for a specified amount of time
        start_time = time.time()
        time_dif = 0
        while time_dif <= seconds:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        pygame.image.save(self.screen, f'screenshot_{time.time()}.jpeg')
            current_time = time.time()
            time_dif = current_time - start_time

            pygame.display.update()

    def add_room(self, room: Room, color: tuple):
        # Draws a colored rectangle on pygame window, with smaller rectangles at the relative door locations
        log(room.name, 'add room')
        log('room_x: ' + str(room.x), 'add room')
        log('room_y: ' + str(room.y), 'add room')
        real_x, real_y = self.real((room.x, room.y), room.h)
        log('real_x: ' + str(real_x), 'add room')
        log('real_y: ' + str(real_y), 'add room')

        pygame.draw.rect(self.screen, ROOM_EDGE_COLOR, (real_x, real_y, room.w, room.h))
        pygame.draw.rect(self.screen, color, (real_x + 2, real_y + 2, room.w - 4, room.h - 4))
        # doors
        for door in room.doors:
            x_offset = 0
            y_offset = 0
            if door.d == 'N':
                x_offset = -2
                y_offset = 0
            elif door.d == 'S':
                x_offset = -2
                y_offset = -4
            elif door.d == 'E':
                x_offset = -4
                y_offset = -2
            elif door.d == 'W':
                x_offset = 0
                y_offset = -2

            pygame.draw.rect(self.screen, DOOR_COLOR,
                             (real_x + door.x + x_offset, real_y - door.y + room.h + y_offset, 4, 4))
        pygame.display.update()

    def add_line(self, point1: tuple, point2: tuple, color: tuple):
        # Draws a colored line on the pygame window
        real1 = self.real(point1)
        real2 = self.real(point2)
        log('Line Start: ' + str(point1), 'add line')
        log('Line End: ' + str(point2), 'add line')
        pygame.draw.line(self.screen, color, real1, real2, 2)

    def print(self):
        # Prints details of the pygame window to console
        print('InnerWidth: ' + str(self.innerWidth))
        print('InnerHeight: ' + str(self.innerHeight))
        print('WindowWidth: ' + str(self.windowWidth))
        print('WindowHeight: ' + str(self.windowHeight))
        print('BorderThickness: ' + str(self.borderThickness))


class Door:
    def __init__(self, relative_x: int, relative_y: int, direction: str):
        self.x = relative_x
        self.y = relative_y
        self.d = direction

    def __eq__(self, other: Door):
        if self.x == other.x and self.y == other.y and self.d == other.d:
            return True

    def __str__(self):
        return f'({self.x}, {self.y}, {self.d})'

    def opposite(self):
        output = ''
        if self.d == 'N':
            output = 'S'
        elif self.d == 'S':
            output = 'N'
        elif self.d == 'E':
            output = 'W'
        elif self.d == 'W':
            output = 'E'
        return output


class Room:
    # Object representing dungeon rooms
    def __init__(self, x: int, y: int, w: int, h: int, name: str, doors: list[Door] = []):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.name = name
        self.doors = doors
        self.entrance_i = -1

    def __eq__(self, other: Room):
        if self.w == other.w and self.h == other.h:
            if len(self.doors) == len(other.doors):
                for door in self.doors:
                    if door not in other.doors:
                        return False
                return True
            else:
                return False
        else:
            return False

    def get_door(self, index: int):
        # Returns relative x, y and direction of the indexed door
        x = self.x + self.doors[index].x
        y = self.y + self.doors[index].y
        d = self.doors[index].d
        return Door(x, y, d)

    def get_directions(self):
        # Returns a list of all door directions for the room
        output = []
        for door in self.doors:
            output.append(door.d)
        return output

    def get_door_by_d(self, d: str):
        # Returns the door that faces direction d
        entrance = None
        for door in self.doors:
            if door.d == d:
                entrance = door
                break
        return entrance

    def test_distance(self, active_door: Door, entrance: Door, goal: tuple):
        # Returns the distance of the goal to the closest non-entrance door if the room were placed connected to the active door
        # (Only called on unplaced rooms)
        x_offset = 0
        y_offset = 0
        if entrance.d == 'N':
            y_offset = -1
        elif entrance.d == 'S':
            y_offset = 1
        elif entrance.d == 'E':
            x_offset = -1
        elif entrance.d == 'W':
            x_offset = 1

        test_x = active_door.x - entrance.x + x_offset
        test_y = active_door.y - entrance.y + y_offset

        distances = []
        for door in self.doors:
            if door != entrance:
                dtest_x = test_x + door.x
                dtest_y = test_y + door.y
                distances.append(math.sqrt((goal[0] - dtest_x) ** 2 + (goal[1] - dtest_y) ** 2))

        return max(distances)

    def get_best_door(self, goal: tuple):
        # Returns the non-entrance door that is closest to the goal
        best_distance = 10000
        best_door = None
        for d in range(len(self.doors)):
            if d != self.entrance_i:
                door = self.get_door(d)
                dist = math.sqrt((goal[0] - door.x) ** 2 + (goal[1] - door.y) ** 2)
                if dist < best_distance:
                    best_distance = dist
                    best_door = self.get_door(d)
        return best_door

    def place_room(self, active_door: Door, entrance: Door):
        # Updates the room object to contain actual location data of the room
        # Doesn't draw
        x_offset = 0
        y_offset = 0
        if active_door.d == 'N':
            y_offset = 1
        elif active_door.d == 'S':
            y_offset = -1
        elif active_door.d == 'E':
            x_offset = 1
        elif active_door.d == 'W':
            x_offset = -1

        self.x = active_door.x - entrance.x + x_offset
        self.y = active_door.y - entrance.y + y_offset
        self.entrance_i = self.doors.index(entrance)
        log('Room placed at ' + str(self.x) + ', ' + str(self.y), 'place room')

    def get_edges(self):
        # Returns a list of dicts, with the slope (0 or inf), the x/y value (depends on slope) and the endpoints
        # for each edge of the room
        corners = [
            (self.x, self.y),
            (self.x, self.y + self.h),
            (self.x + self.w, self.y + self.h),
            (self.x + self.w, self.y)
        ]

        edges = []
        for c, corner in enumerate(corners):
            ends = [corner, corners[(c + 1) % 4]]

            if ends[0][0] == ends[1][0]:
                slope = 'inf'
                value = ends[0][0]
            else:
                slope = '0'
                value = ends[0][1]

            if slope == 'inf':
                a = min([ends[0][1], ends[1][1]])
                b = max([ends[0][1], ends[1][1]])
            else:
                a = min([ends[0][0], ends[1][0]])
                b = max([ends[0][0], ends[1][0]])

            edges.append({
                'slope': slope,
                'value': value,
                'a': a,
                'b': b
            })

        return edges

    def get_rotated(self, degree: int):
        # Returns a copy of the room that has been rotated degree degrees
        # Only called on unplaced rooms
        directions = ['N', 'E', 'S', 'W', 'N']

        new_w = self.h
        new_h = self.w
        new_name = self.name + ' r90'

        new_doors = []
        for door in self.doors:
            new_doors.append(Door(door.y, self.w - door.x, directions[directions.index(door.d) + 1]))

        output = Room(0, 0, new_w, new_h, new_name, new_doors)

        if degree > 90:
            degree -= 90
            output = output.get_rotated(degree)

        return output


class DungeonGenerator:
    # Class that contains functions to generate a list of (room, active_door) that represents the dungeon
    def __init__(self, start: Room, grid_w: int, grid_h: int, prefabs: list[Room]):
        self.start: Room = start
        self.goal = None
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.prefabs = prefabs
        self.path = [(start, start.get_door(0))]

    def generate_goal(self):
        # Randomly picks a point in the grid to be the goal which the dungeon builds towards
        # Minimum distance from start determined by FINISH_THRESH global
        valid = False
        while not valid:
            x = random.randint(0, self.grid_w - 10)
            y = random.randint(0, self.grid_h - 10)
            log('Possible Finish: ' + str(x) + ', ' + str(y), 'generate finish')
            if abs((self.start.x / self.grid_w) - (x / self.grid_w)) < FINISH_THRESH \
                    or abs((self.start.y / self.grid_h) - (y / self.grid_h)) < FINISH_THRESH:
                valid = False
                log('Invalid', 'generate finish')
            else:
                valid = True
        self.goal = (x, y)
        log('Goal: ' + str(self.goal), 'generate finish')

    def show_prefabs(self, window: PygameDisplay):
        # Draws the generators prefabs on the Pygame window
        x = 10
        y = 10
        for room in self.prefabs:
            room.x = x
            room.y = y
            window.add_room(room, GREEN)
            if x > 400:
                x = 10
                y += 100
            else:
                x += 100

    def add_rotated_prefabs(self):
        # Adds all rotated versions of the prefabs (no duplicates) to the prefabs
        full_prefabs = self.prefabs

        for room in self.prefabs:
            for degree in [90, 180, 270]:
                rotated_room = room.get_rotated(degree)
                if rotated_room not in full_prefabs:
                    full_prefabs.append(rotated_room)
                    log('Adding rotated room ' + rotated_room.name, 'rotated prefabs')

        self.prefabs = full_prefabs

    def overlaps(self, test_room: Room):
        # Returns true if an unplaced test_room would overlap with any existing room or grid edges
        if not 0 <= test_room.x <= self.grid_w - test_room.w or not 0 <= test_room.y <= self.grid_h - test_room.h:
            return True

        test_edges = test_room.get_edges()
        exist_edges = []
        for room, door in self.path:
            new_edges = room.get_edges()
            for edge in new_edges:
                exist_edges.append(edge)
        for test in test_edges:
            for edge in exist_edges:
                if test['slope'] != edge['slope']:
                    if test['slope'] == 'inf':
                        vert = test
                        hor = edge
                    else:
                        vert = edge
                        hor = test
                    intersect = (vert['value'], hor['value'])
                    if (hor['a'] <= intersect[0] <= hor['b'] and
                            vert['a'] <= intersect[1] <= vert['b']):
                        return True
        return False

    def build_dungeon(self):
        # Main logic for generating dungeon
        start_time = time.time()
        self.generate_goal()
        failed_rooms = []
        while self.path[-1][0].name != 'finish':
            # Loops until the last room in the path is the finish
            active_room = self.path[-1][0]
            active_door = self.path[-1][1]
            log('Active room: ' + active_room.name, 'build dungeon')

            # Creates list of rooms with a door opposite/that could connect to the active_door
            available_rooms = []
            if len(self.path) >= PATH_LENGTH:
                # Forces the only available room to be the finish if the path is at its desired length
                available_rooms = [Room(0, 0, 20, 20, 'finish',
                                        [Door(10, 0, 'S'), Door(10, 20, 'N'), Door(0, 10, 'W'), Door(20, 10, 'E')])]
            else:
                for room in prefabs:
                    directions = room.get_directions()
                    if active_door.opposite() in directions:
                        if active_room.name != room.name and active_room.name not in failed_rooms:
                            available_rooms.append(room)

            log('Available Rooms: ' + str(available_rooms), 'False')

            # Gets the room with the door closest to goal (chance to pick a random room based on ROOM_RANDOM)
            next_room = None
            best_distance = 10000
            for room in available_rooms:
                entrance = room.get_door_by_d(active_door.opposite())
                dist = room.test_distance(active_door, entrance, self.goal)
                log(room.name + ': ' + str(dist), 'build dungeon')
                if dist < best_distance:
                    best_distance = dist
                    next_room = room
            room_chance = random.randint(1, 100) / 100
            if room_chance > ROOM_RANDOM:
                log('Best Room: ' + str(next_room.name), 'build dungeon')
                next_room = random.choice(available_rooms)
                log('Random Room Triggered', 'build dungeon')
            log(next_room.name, 'build dungeon')

            # Turns prefab into an actual room
            copied_next = copy.deepcopy(next_room)
            copied_next.place_room(active_door, copied_next.get_door_by_d(active_door.opposite()))

            # Gets best door (chance to get random door based on DOOR_RANDOM)
            next_door = copied_next.get_best_door(self.goal)

            door_chance = random.randint(1, 100) / 100
            log('door_chance: ' + str(door_chance), 'random door')
            if door_chance > DOOR_RANDOM and len(copied_next.doors) > 2:

                log('Random Door Triggered', 'random door')
                log(copied_next.name, 'random door')
                log('Best Door: ' + str(next_door), 'random door')
                log('Entrance i: ' + str(copied_next.entrance_i), 'random door')
                invalid = True
                while invalid:
                    random_i = random.randint(0, len(copied_next.doors) - 1)
                    log('Random i: ' + str(random_i), 'random door')
                    next_door = copied_next.get_door(random_i)
                    log('Random door: ' + str(next_door), 'random door')
                    if random_i != copied_next.entrance_i:
                        invalid = False

                log('Choosing door instead: ' + str(next_door), 'random door')

            log('Next door: ' + str(next_door), 'build dungeon')

            if not self.overlaps(copied_next):
                # Adds room to path and resets the failure count/list
                self.path.append((copied_next, next_door))
                log('Added ' + str((copied_next.name, next_door)) + ' to path', 'build dungeon')
                failed_rooms = []
            else:
                # Adds room to the failure list and tries again with a room not in the list
                log('Room overlapped. Trying again...', 'build dungeon')
                failed_rooms.append(copied_next.name)
                if len(failed_rooms) < ALLOWED_FAILS:
                    # Removes the last room added to path and prevents that room from being chosen again if fail count
                    # exceeds ALLOWED_FAILS to prevent a path where no rooms can be placed
                    popped, door = self.path.pop(len(self.path) - 1)
                    log('Too many fails. Popping ' + popped.name, 'build dungeon')
                    failed_rooms = [popped.name]

            #self.print_path()

        # Calculates the amount of time the generator took
        # Used to verify no excessive looping
        end_time = time.time()
        return end_time - start_time

    def new_dungeon(self):
        # Clears dungeon information and creates a new dungeon with the same generator
        self.path = [(start, start.get_door(0))]
        self.build_dungeon()

    def draw(self, window: PygameDisplay, end_sleep: int = 100000):
        # Turns on Pygame window displaying the full dungeon for end_sleep seconds
        window.add_room(self.start, GREEN)
        for room, door in self.path:
            if room.name != 'start' and room.name != 'finish':
                window.add_room(room, YELLOW)
            elif room.name == 'finish':
                window.add_room(room, RED)
        # Optional line showing optimal path from start to goal
        #window.add_line(self.start.get_door(0), finish_center, YELLOW)
        window.add_room(Room(self.goal[0], self.goal[1], 10, 10, 'goal'), PINK)
        window.on(end_sleep)

    def draw_by_room(self, window: PygameDisplay, room_sleep: float, end_sleep: int = 100000):
        # Turns on Pygame display and draws rooms in dungeon one at a time, with room_sleep seconds between each room
        for room, door in self.path:
            color = YELLOW
            if room.name == 'start':
                color = GREEN
            elif room.name == 'finish':
                color = RED
            window.add_room(room, color)
            pygame.display.update()
            time.sleep(room_sleep)
        window.on(end_sleep)
        self.print_path()

    def print_path(self):
        # Prints the list of (room, door)
        print('Path:')
        for room, door in self.path:
            print((room.name, room.x, room.y, str(door)))


# Prefabs
prefabs = [
    Room(0, 0, 60, 60, 'big square', [Door(30, 0, 'S'), Door(30, 60, 'N'), Door(0, 30, 'W'), Door(60, 30, 'E')]),
    Room(0, 0, 10, 50, 'long hall', [Door(5, 0, 'S'), Door(5, 50, 'N')]),
    Room(0, 0, 30, 40, 't shaped', [Door(15, 0, 'S'), Door(0, 35, 'W'), Door(30, 35, 'E')]),
    Room(0, 0, 50, 20, 'u turn', [Door(10, 0, 'S'), Door(40, 0, 'S')]),
    Room(0, 0, 30, 30, 'left turn', [Door(15, 0, 'S'), Door(0, 15, 'W')]),
    Room(0, 0, 30, 30, 'right turn', [Door(15, 0, 'S'), Door(30, 15, 'E')]),
    Room(0, 0, 20, 20, 'small square', [Door(10, 0, 'S'), Door(10, 20, 'N'), Door(0, 10, 'W'), Door(20, 10, 'E')]),
    Room(0, 0, 30, 40, 'upside down t', [Door(15, 40, 'N'), Door(0, 35, 'W'), Door(30, 35, 'E')])
]

# Main
window = PygameDisplay(500, 500, 10, BLACK, WHITE)
start = Room(230, 0, 20, 10, 'start', [Door(10, 10, 'N')])
g = DungeonGenerator(start, 500, 500, prefabs)
g.add_rotated_prefabs()
# g.show_prefabs(window)
build_dungeon_time = g.build_dungeon()
# g.print_path()
# g.draw(window)
g.draw_by_room(window, .25, 2)
print('Dungeon Build Time: ' + str(build_dungeon_time))
while True:
    window.reset()
    g.new_dungeon()
    g.draw_by_room(window, .25, 2)
    g.print_path()
    print('Dungeon Build Time: ' + str(build_dungeon_time))
