import pygame
import sys
from pygame import Vector2
import time
import math

# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 800
BLOCK_SIZE = 50
GRID_SIZE = WINDOW_SIZE // BLOCK_SIZE
FPS = 60
MOVE_DELAY = 150  # Milliseconds between moves

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
BROWN = (165, 42, 42)
GRAY = (128, 128, 128)

# Color dictionary for color mechanics
COLORS = {
    "red": RED,
    "blue": BLUE,
    "green": GREEN,
    "yellow": YELLOW,
    "purple": PURPLE,
    "orange": ORANGE
}

class Block:
    def __init__(self, pos, color, block_type="wall"):
        self.pos = Vector2(pos[0], pos[1])
        self.color = color
        self.block_type = block_type
        self.rect = pygame.Rect(pos[0] * BLOCK_SIZE, pos[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        self.is_active = True
        self.direction = Vector2(0, 0)  # For moving platforms and rotating blocks
        self.speed = 0.02  # For moving platforms
        self.original_pos = Vector2(pos[0], pos[1])  # For moving platforms
        self.move_range = 5  # For moving platforms
        self.rotation = 0  # For rotating blocks
        self.cooldown = 0  # For teleporters
        self.color_key = None  # For color switches
        self._last_update = pygame.time.get_ticks()  # For teleporter cooldown

    def move(self, direction):
        self.pos += Vector2(direction)
        self.rect.x = self.pos.x * BLOCK_SIZE
        self.rect.y = self.pos.y * BLOCK_SIZE

    def draw(self, screen):
        if self.is_active:
            if self.block_type == "rotating_block":
                # Draw rotating block with lines showing rotation
                pygame.draw.rect(screen, self.color, self.rect)
                center = self.rect.center
                end_pos = (
                    center[0] + math.cos(self.rotation) * BLOCK_SIZE/2,
                    center[1] + math.sin(self.rotation) * BLOCK_SIZE/2
                )
                pygame.draw.line(screen, BLACK, center, end_pos, 2)
            elif self.block_type == "teleporter":
                # Draw teleporter with cooldown indicator
                pygame.draw.rect(screen, self.color, self.rect)
                if self.cooldown > 0:
                    cooldown_height = (self.cooldown / 1000) * BLOCK_SIZE
                    cooldown_rect = pygame.Rect(
                        self.rect.x, 
                        self.rect.y + BLOCK_SIZE - cooldown_height,
                        BLOCK_SIZE,
                        cooldown_height
                    )
                    pygame.draw.rect(screen, (100, 100, 100), cooldown_rect)
            else:
                pygame.draw.rect(screen, self.color, self.rect)
            
            pygame.draw.rect(screen, BLACK, self.rect, 1)
            
            if self.block_type == "one_way":
                # Draw direction arrow
                arrow_points = []
                if self.direction.x == 1:  # Right
                    arrow_points = [(self.rect.left + 10, self.rect.centery - 10),
                                  (self.rect.right - 10, self.rect.centery),
                                  (self.rect.left + 10, self.rect.centery + 10)]
                elif self.direction.x == -1:  # Left
                    arrow_points = [(self.rect.right - 10, self.rect.centery - 10),
                                  (self.rect.left + 10, self.rect.centery),
                                  (self.rect.right - 10, self.rect.centery + 10)]
                elif self.direction.y == 1:  # Down
                    arrow_points = [(self.rect.centerx - 10, self.rect.top + 10),
                                  (self.rect.centerx, self.rect.bottom - 10),
                                  (self.rect.centerx + 10, self.rect.top + 10)]
                elif self.direction.y == -1:  # Up
                    arrow_points = [(self.rect.centerx - 10, self.rect.bottom - 10),
                                  (self.rect.centerx, self.rect.top + 10),
                                  (self.rect.centerx + 10, self.rect.bottom - 10)]
                if arrow_points:
                    pygame.draw.polygon(screen, BLACK, arrow_points)

    def update(self):
        current_time = pygame.time.get_ticks()
        
        if self.block_type == "moving_platform":
            # Update position based on movement pattern
            offset = pygame.math.Vector2(
                self.original_pos.x + self.direction.x * self.move_range * abs(math.sin(current_time * self.speed)),
                self.original_pos.y + self.direction.y * self.move_range * abs(math.sin(current_time * self.speed))
            )
            self.pos = Vector2(offset.x, offset.y)
            self.rect.x = self.pos.x * BLOCK_SIZE
            self.rect.y = self.pos.y * BLOCK_SIZE
        elif self.block_type == "rotating_block":
            # Update rotation
            self.rotation = (current_time * self.speed) % (2 * math.pi)
            # Update direction vector based on rotation
            rot_x = math.cos(self.rotation)
            rot_y = math.sin(self.rotation)
            self.direction = Vector2(rot_x, rot_y).normalize()
        elif self.block_type == "teleporter":
            # Update cooldown
            if self.cooldown > 0:
                self.cooldown = max(0, self.cooldown - (current_time - self._last_update))
                self._last_update = current_time

class Level:
    def __init__(self, level_data):
        self.walls = []
        self.moving_platforms = []
        self.rotating_blocks = []
        self.teleporters = []
        self.portals = []
        self.ice = []
        self.one_way_paths = []
        self.color_switches = []
        self.color_doors = []
        self.buttons = []
        self.doors = []
        self.keys = []
        
        # Add walls
        for wall_pos in level_data.get("walls", []):
            if 0 <= wall_pos[0] < GRID_SIZE and 0 <= wall_pos[1] < GRID_SIZE:
                wall = Block(wall_pos, GRAY)
                self.walls.append(wall)
            
        # Add moving platforms
        for platform_data in level_data.get("moving_platforms", []):
            pos = platform_data["pos"]
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                platform = Block(pos, BLUE, "moving_platform")
                dir_x, dir_y = platform_data["direction"]
                platform.direction = Vector2(dir_x, dir_y)
                platform.move_range = platform_data.get("range", 3)
                platform.speed = platform_data.get("speed", 0.02)
                self.moving_platforms.append(platform)
            
        # Add rotating blocks
        for block_data in level_data.get("rotating_blocks", []):
            pos = block_data["pos"]
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                block = Block(pos, BROWN, "rotating_block")
                block.speed = block_data.get("speed", 0.001)
                dir_x, dir_y = block_data.get("direction", (1, 0))
                block.direction = Vector2(dir_x, dir_y)
                self.rotating_blocks.append(block)
            
        # Add teleporters
        for teleporter_data in level_data.get("teleporters", []):
            pos = teleporter_data["pos"]
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                teleporter = Block(pos, PURPLE, "teleporter")
                target_x, target_y = teleporter_data["target"]
                teleporter.target = Vector2(target_x, target_y)
                self.teleporters.append(teleporter)
            
        # Add portals
        portals = level_data.get("portals", [])
        for i in range(0, len(portals), 2):
            if i + 1 < len(portals):
                portal1_pos = portals[i]
                portal2_pos = portals[i + 1]
                if (0 <= portal1_pos[0] < GRID_SIZE and 0 <= portal1_pos[1] < GRID_SIZE and
                    0 <= portal2_pos[0] < GRID_SIZE and 0 <= portal2_pos[1] < GRID_SIZE):
                    portal1 = Block(portal1_pos, CYAN, "portal")
                    portal2 = Block(portal2_pos, CYAN, "portal")
                    self.portals.extend([portal1, portal2])
            
        # Add ice blocks
        for ice_pos in level_data.get("ice", []):
            if 0 <= ice_pos[0] < GRID_SIZE and 0 <= ice_pos[1] < GRID_SIZE:
                ice = Block(ice_pos, WHITE, "ice")
                self.ice.append(ice)
            
        # Add one-way paths
        for path_data in level_data.get("one_way_paths", []):
            pos = path_data["pos"]
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                path = Block(pos, YELLOW, "one_way_path")
                dir_x, dir_y = path_data["direction"]
                path.direction = Vector2(dir_x, dir_y)
                self.one_way_paths.append(path)
            
        # Add color switches
        for switch_data in level_data.get("color_switches", []):
            pos = switch_data["pos"]
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                switch = Block(pos, COLORS[switch_data["color"]], "color_switch")
                switch.color_key = switch_data["color"]
                self.color_switches.append(switch)
            
        # Add color doors
        for door_data in level_data.get("color_doors", []):
            pos = door_data["pos"]
            if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                door = Block(pos, COLORS[door_data["color"]], "color_door")
                door.color_key = door_data["color"]
                self.color_doors.append(door)
            
        # Add buttons and doors
        for i, button_pos in enumerate(level_data.get("buttons", [])):
            if 0 <= button_pos[0] < GRID_SIZE and 0 <= button_pos[1] < GRID_SIZE:
                button = Block(button_pos, RED, "button")
                self.buttons.append(button)
            
        for i, door_pos in enumerate(level_data.get("doors", [])):
            if 0 <= door_pos[0] < GRID_SIZE and 0 <= door_pos[1] < GRID_SIZE:
                door = Block(door_pos, ORANGE, "door")
                self.doors.append(door)
            
        # Add keys
        for key_pos in level_data.get("keys", []):
            if 0 <= key_pos[0] < GRID_SIZE and 0 <= key_pos[1] < GRID_SIZE:
                key = Block(key_pos, YELLOW, "key")
                self.keys.append(key)
            
        # Ensure player and goal positions are valid
        player_pos = level_data["player"]
        goal_pos = level_data["goal"]
        if not (0 <= player_pos[0] < GRID_SIZE and 0 <= player_pos[1] < GRID_SIZE):
            player_pos = (1, 1)
        if not (0 <= goal_pos[0] < GRID_SIZE and 0 <= goal_pos[1] < GRID_SIZE):
            goal_pos = (GRID_SIZE-2, GRID_SIZE-2)
        
        self.player = Block(player_pos, RED, "player")
        self.goal = Block(goal_pos, BLUE, "goal")
        self.start_time = time.time()
        self.moves = 0
        self.sliding = False
        self.slide_direction = Vector2(0, 0)
        self.active_color = None
        
    def draw(self, screen):
        for ice in self.ice:
            ice.draw(screen)
        for path in self.one_way_paths:
            path.draw(screen)
        for platform in self.moving_platforms:
            platform.draw(screen)
        for wall in self.walls:
            wall.draw(screen)
        for button in self.buttons:
            button.draw(screen)
        for door in self.doors:
            door.draw(screen)
        for key in self.keys:
            key.draw(screen)
        for portal in self.portals:
            portal.draw(screen)
        for block in self.rotating_blocks:
            block.draw(screen)
        for teleporter in self.teleporters:
            teleporter.draw(screen)
        for switch in self.color_switches:
            switch.draw(screen)
        for door in self.color_doors:
            door.draw(screen)
        self.goal.draw(screen)
        self.player.draw(screen)

    def update(self):
        # Update all blocks that need updating
        for block in (self.moving_platforms + self.rotating_blocks + self.teleporters):
            block.update()

    def is_collision(self, pos):
        return any(wall.pos == pos and wall.is_active for wall in self.walls + self.doors + self.moving_platforms)

    def check_button_press(self, pos):
        for i, button in enumerate(self.buttons):
            if button.pos == pos and button.is_active:
                self.doors[i].is_active = not self.doors[i].is_active
                return True
        return False

    def collect_key(self, pos):
        for key in self.keys:
            if key.pos == pos and key.is_active:
                key.is_active = False
                return True
        return False

    def check_portal(self, pos):
        for i in range(0, len(self.portals), 2):
            if self.portals[i].pos == pos:
                return self.portals[i + 1].pos
            elif self.portals[i + 1].pos == pos:
                return self.portals[i].pos
        return None

    def check_one_way_path(self, pos, move_direction):
        for path in self.one_way_paths:
            if path.pos == pos:
                # Only allow movement in the path's direction
                return bool(path.direction.dot(move_direction) > 0)
        return True

    def check_ice(self, pos):
        return any(ice.pos == pos for ice in self.ice)

    def check_rotating_block(self, pos):
        for block in self.rotating_blocks:
            if block.pos == pos:
                # Check if player's movement aligns with block's current direction
                return block.direction
        return None

    def check_teleporter(self, pos):
        for teleporter in self.teleporters:
            if teleporter.pos == pos and teleporter.cooldown <= 0:
                teleporter.cooldown = 1000  # 1 second cooldown
                return teleporter.target
        return None

    def check_color_switch(self, pos):
        for switch in self.color_switches:
            if switch.pos == pos:
                self.active_color = switch.color_key
                # Update color doors
                for door in self.color_doors:
                    door.is_active = (door.color_key != self.active_color)
                return True
        return False

    def move_player(self, direction):
        if self.sliding:
            # Continue sliding in the same direction
            new_pos = self.player.pos + self.slide_direction
            if not self.is_collision(new_pos) and self.check_one_way_path(new_pos, self.slide_direction):
                self.player.pos = new_pos
                self.player.rect.x = self.player.pos.x * BLOCK_SIZE
                self.player.rect.y = self.player.pos.y * BLOCK_SIZE
                if not self.check_ice(new_pos):
                    self.sliding = False
            else:
                self.sliding = False
        else:
            new_pos = self.player.pos + direction
            if not self.is_collision(new_pos) and self.check_one_way_path(new_pos, direction):
                self.moves += 1
                
                # Check all special blocks
                rotating_dir = self.check_rotating_block(new_pos)
                if rotating_dir:
                    direction = rotating_dir
                
                teleport_pos = self.check_teleporter(new_pos)
                if teleport_pos is not None:
                    self.player.pos = teleport_pos
                    self.player.rect.x = self.player.pos.x * BLOCK_SIZE
                    self.player.rect.y = self.player.pos.y * BLOCK_SIZE
                    return
                
                self.check_button_press(new_pos)
                self.collect_key(new_pos)
                self.check_color_switch(new_pos)
                
                portal_pos = self.check_portal(new_pos)
                if portal_pos is not None:
                    self.player.pos = portal_pos
                    self.player.rect.x = self.player.pos.x * BLOCK_SIZE
                    self.player.rect.y = self.player.pos.y * BLOCK_SIZE
                else:
                    self.player.pos = new_pos
                    self.player.rect.x = self.player.pos.x * BLOCK_SIZE
                    self.player.rect.y = self.player.pos.y * BLOCK_SIZE
                
                # Check if landed on ice
                if self.check_ice(new_pos):
                    self.sliding = True
                    self.slide_direction = direction

    def is_complete(self):
        return self.player.pos == self.goal.pos

    def get_score(self):
        time_taken = int(time.time() - self.start_time)
        return max(1000 - (time_taken * 10) - (self.moves * 5), 0)

def get_levels():
    levels = [
        # Level 1: Simple Walls
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)] +
                    [(3, i) for i in range(3, 12)] +
                    [(11, i) for i in range(3, 12)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 2: Moving Platforms
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)],
            "moving_platforms": [
                {"pos": (4, 4), "direction": (1, 0), "range": 3, "speed": 0.02},
                {"pos": (10, 10), "direction": (0, 1), "range": 3, "speed": 0.02}
            ],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 3: Buttons and Keys
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)] +
                    [(7, i) for i in range(5, 12)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [(3, 3)],
            "doors": [(7, 7)],
            "keys": [(5, 5)]
        },
        # Level 4: Ice Blocks
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [(i, 7) for i in range(3, 12)],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 5: One Way Paths
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [
                {"pos": (7, i), "direction": (1, 0)} for i in range(3, 12)
            ],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 6: Color Switches
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)] +
                    [(7, i) for i in range(3, 12)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [
                {"pos": (3, 3), "color": "red"},
                {"pos": (11, 11), "color": "blue"}
            ],
            "color_doors": [
                {"pos": (7, 5), "color": "red"},
                {"pos": (7, 9), "color": "blue"}
            ],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 7: Rotating Blocks
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)],
            "moving_platforms": [],
            "rotating_blocks": [
                {"pos": (7, 7), "speed": 0.001},
                {"pos": (7, 8), "speed": 0.002}
            ],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 8: Teleporters
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)] +
                    [(7, i) for i in range(3, 12)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [
                {"pos": (3, 3), "target": (11, 3)},
                {"pos": (3, 11), "target": (11, 11)}
            ],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 9: Portals
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)] +
                    [(7, i) for i in range(3, 12)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [(3, 3), (11, 3), (3, 11), (11, 11)],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        },
        # Level 10: Mixed Mechanics
        {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(i, 0) for i in range(GRID_SIZE)] +
                    [(i, GRID_SIZE-1) for i in range(GRID_SIZE)] +
                    [(0, i) for i in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, i) for i in range(GRID_SIZE)],
            "moving_platforms": [
                {"pos": (7, 7), "direction": (1, 0), "range": 3, "speed": 0.02}
            ],
            "rotating_blocks": [{"pos": (3, 3), "speed": 0.001}],
            "teleporters": [{"pos": (11, 11), "target": (3, 11)}],
            "portals": [(5, 5), (9, 9)],
            "ice": [(i, 7) for i in range(4, 6)],
            "one_way_paths": [{"pos": (7, 3), "direction": (1, 0)}],
            "color_switches": [{"pos": (2, 2), "color": "red"}],
            "color_doors": [{"pos": (12, 12), "color": "red"}],
            "buttons": [(4, 4)],
            "doors": [(8, 8)],
            "keys": [(6, 6)]
        }
    ]
    
    # Add remaining levels (11-100) with EXTREME challenge
    for i in range(11, 101):
        level = {
            "player": (1, 1),
            "goal": (13, 13),
            "walls": [(x, 0) for x in range(GRID_SIZE)] +
                    [(x, GRID_SIZE-1) for x in range(GRID_SIZE)] +
                    [(0, y) for y in range(GRID_SIZE)] +
                    [(GRID_SIZE-1, y) for y in range(GRID_SIZE)],
            "moving_platforms": [],
            "rotating_blocks": [],
            "teleporters": [],
            "portals": [],
            "ice": [],
            "one_way_paths": [],
            "color_switches": [],
            "color_doors": [],
            "buttons": [],
            "doors": [],
            "keys": []
        }
        
        # Extreme difficulty scaling (0-15)
        difficulty = min(15, (i - 11) // 6)  # Faster scaling
        
        # Add more mechanics at once (up to 8)
        mechanics = [(i + offset) % 8 for offset in range(min(5 + difficulty // 2, 8))]
        
        # Moving Platforms - EXTREME speed and complexity
        if 0 in mechanics:
            platform_count = min(4 + difficulty // 2, 8)  # More platforms
            for p in range(platform_count):
                speed = 0.08 + (difficulty * 0.015)  # MUCH faster
                range_val = 4 + difficulty
                pos = (0, 0)
                direction = (0, 0)
                
                if p % 4 == 0:
                    pos = (4 + (p % 2) * 6, 4)
                    direction = (1, 1) if p % 2 == 0 else (-1, 1)
                elif p % 4 == 1:
                    pos = (4, 4 + (p % 2) * 6)
                    direction = (1, -1) if p % 2 == 0 else (1, 1)
                elif p % 4 == 2:
                    pos = (10 - (p % 2) * 6, 10)
                    direction = (-1, -1) if p % 2 == 0 else (1, -1)
                else:
                    pos = (7, 7 + (p % 2) * 4)
                    direction = (-1, 1) if p % 2 == 0 else (1, 1)
                
                if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                    level["moving_platforms"].append({
                        "pos": pos,
                        "direction": direction,
                        "range": range_val,
                        "speed": speed * (1.5 if abs(direction[0] + direction[1]) > 1 else 1)  # Even faster diagonals
                    })
        
        # Rotating Blocks - EXTREME rotation speed
        if 1 in mechanics:
            positions = [(7, 7), (4, 4), (10, 10), (4, 10), (10, 4), (7, 4), (4, 7), (10, 7)]
            block_count = min(3 + difficulty // 2, len(positions))
            base_speed = 0.006 * (1.6 ** difficulty)  # Much faster base rotation
            
            for b in range(block_count):
                pos = positions[b]
                if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                    level["rotating_blocks"].append({
                        "pos": pos,
                        "speed": base_speed * (1.4 ** b)  # Faster speed increase per block
                    })
        
        # Teleporters - Complex network with chain reactions
        if 2 in mechanics:
            positions = [(3, 3), (11, 11), (3, 11), (11, 3), (7, 3), (7, 11), (3, 7), (11, 7),
                        (5, 5), (9, 9), (5, 9), (9, 5)]  # More teleporter positions
            teleporter_count = min(6 + difficulty // 2, len(positions))
            teleporter_count = teleporter_count - (teleporter_count % 2)
            
            for t in range(0, teleporter_count, 2):
                if t + 1 < teleporter_count:
                    pos1, pos2 = positions[t], positions[t + 1]
                    if (0 <= pos1[0] < GRID_SIZE and 0 <= pos1[1] < GRID_SIZE and
                        0 <= pos2[0] < GRID_SIZE and 0 <= pos2[1] < GRID_SIZE):
                        # Create chain teleportation
                        next_t = (t + 2) % teleporter_count
                        next_pos = positions[next_t]
                        level["teleporters"].extend([
                            {"pos": pos1, "target": pos2},
                            {"pos": pos2, "target": next_pos}
                        ])
        
        # Portals - Complex portal maze
        if 3 in mechanics:
            positions = [(3, 3), (11, 3), (3, 11), (11, 11), (7, 3), (7, 11), (3, 7), (11, 7),
                        (5, 5), (9, 9), (5, 9), (9, 5)]  # More portal positions
            portal_count = min(4 + difficulty // 2, len(positions))
            portal_count = portal_count - (portal_count % 2)
            
            for p in range(0, portal_count, 2):
                if p + 1 < len(positions):
                    pos = positions[p]
                    if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                        level["portals"].append(pos)
        
        # Ice - EXTREME ice patterns
        if 4 in mechanics:
            ice_positions = []
            if difficulty > 8:
                # Spiral maze pattern
                for d in range(1, min(6, GRID_SIZE // 2)):
                    for x in range(3+d, 12-d):
                        if 0 <= x < GRID_SIZE and 0 <= 3+d < GRID_SIZE:
                            ice_positions.append((x, 3+d))
                        if 0 <= x < GRID_SIZE and 0 <= 11-d < GRID_SIZE:
                            ice_positions.append((x, 11-d))
                    for y in range(4+d, 11-d):
                        if 0 <= 3+d < GRID_SIZE and 0 <= y < GRID_SIZE:
                            ice_positions.append((3+d, y))
                        if 0 <= 11-d < GRID_SIZE and 0 <= y < GRID_SIZE:
                            ice_positions.append((11-d, y))
            elif difficulty > 4:
                # Complex cross with diagonals
                for x in range(3, 12):
                    if x < GRID_SIZE:
                        # Main cross
                        ice_positions.append((x, 7))
                        ice_positions.append((7, x))
                        # Diagonals
                        if x < GRID_SIZE and x < GRID_SIZE:
                            ice_positions.append((x, x))
                        if x < GRID_SIZE and (14-x) < GRID_SIZE:
                            ice_positions.append((x, 14-x))
                        # Extra diagonals
                        if x-2 < GRID_SIZE and x+2 < GRID_SIZE:
                            ice_positions.append((x-2, x+2))
                        if x+2 < GRID_SIZE and x-2 < GRID_SIZE:
                            ice_positions.append((x+2, x-2))
            else:
                # Double cross pattern
                for x in range(3, 12):
                    if x < GRID_SIZE:
                        ice_positions.append((x, 5))
                        ice_positions.append((x, 9))
                        ice_positions.append((5, x))
                        ice_positions.append((9, x))
            
            level["ice"] = list(set(ice_positions))  # Remove duplicates
        
        # One-way Paths - Complex maze with forced routes
        if 5 in mechanics:
            positions = [(7, 3), (7, 7), (7, 11), (3, 7), (11, 7), (5, 5), (9, 9), (5, 9),
                        (4, 4), (10, 10), (4, 10), (10, 4)]  # More positions
            # Always use diagonal directions for maximum difficulty
            directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
            path_count = min(6 + difficulty // 2, len(positions))
            
            for p in range(path_count):
                pos = positions[p]
                if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                    level["one_way_paths"].append({
                        "pos": pos,
                        "direction": directions[p % len(directions)]
                    })
        
        # Color Mechanics - Complex color chains
        if 6 in mechanics:
            colors = ["red", "blue", "green", "yellow", "purple", "orange"][:min(4 + difficulty // 3, 6)]
            
            switch_positions = [(3, 3), (11, 3), (3, 11), (11, 11), (7, 3), (7, 11),
                              (5, 5), (9, 9), (5, 9), (9, 5)]  # More switches
            door_positions = [(7, 5), (7, 7), (7, 9), (5, 7), (9, 7), (7, 11),
                            (6, 6), (8, 8), (6, 8), (8, 6)]  # More doors
            
            for c_idx, color in enumerate(colors):
                # Multiple switches per color
                switch_count = min(2 + difficulty // 4, len(switch_positions))
                for s in range(switch_count):
                    pos_idx = (c_idx + s) % len(switch_positions)
                    pos = switch_positions[pos_idx]
                    if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                        level["color_switches"].append({
                            "pos": pos,
                            "color": color
                        })
                
                # Multiple doors per color
                door_count = min(2 + difficulty // 3, len(door_positions))
                for d in range(door_count):
                    pos_idx = (c_idx + d) % len(door_positions)
                    pos = door_positions[pos_idx]
                    if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                        level["color_doors"].append({
                            "pos": pos,
                            "color": color
                        })
        
        # Buttons and Doors - Complex sequences with multiple dependencies
        if 7 in mechanics:
            button_positions = [(3, 3), (11, 3), (3, 11), (11, 11), (7, 3), (7, 11),
                              (5, 5), (9, 9), (5, 9), (9, 5)]  # More buttons
            door_positions = [(7, 5), (7, 7), (7, 9), (5, 7), (9, 7), (7, 11),
                            (6, 6), (8, 8), (6, 8), (8, 6)]  # More doors
            button_count = min(4 + difficulty // 2, len(button_positions))
            
            for b in range(button_count):
                button_pos = button_positions[b]
                if 0 <= button_pos[0] < GRID_SIZE and 0 <= button_pos[1] < GRID_SIZE:
                    level["buttons"].append(button_pos)
                    # Multiple doors per button
                    door_count = min(2 + difficulty // 3, len(door_positions))
                    for d in range(door_count):
                        pos_idx = (b + d) % len(door_positions)
                        door_pos = door_positions[pos_idx]
                        if 0 <= door_pos[0] < GRID_SIZE and 0 <= door_pos[1] < GRID_SIZE:
                            level["doors"].append(door_pos)
        
        # Wall Patterns - EXTREME maze patterns
        wall_positions = []
        if difficulty >= 2:
            # Dense vertical walls
            gap_size = max(2, 3 - difficulty // 4)  # Smaller gaps
            for y in range(3, 12):
                if y % gap_size != 0 and y < GRID_SIZE:
                    wall_positions.append((7, y))
                    if difficulty > 6:  # Double walls
                        if 5 < GRID_SIZE:
                            wall_positions.append((5, y))
                        if 9 < GRID_SIZE:
                            wall_positions.append((9, y))
        
        if difficulty >= 4:
            # Dense horizontal walls
            for x in range(3, 12):
                if x % gap_size != 0 and x < GRID_SIZE:
                    wall_positions.append((x, 7))
                    if difficulty > 6:  # Double walls
                        if 5 < GRID_SIZE:
                            wall_positions.append((x, 5))
                        if 9 < GRID_SIZE:
                            wall_positions.append((x, 9))
        
        if difficulty >= 6:
            # Complex diagonal barriers
            for x in range(4, 11):
                if x % (gap_size-1) != 0:  # Even smaller gaps for diagonals
                    if x < GRID_SIZE and x < GRID_SIZE:
                        wall_positions.append((x, x))
                        if difficulty > 8:  # Parallel diagonals
                            if x-1 < GRID_SIZE and x-1 < GRID_SIZE:
                                wall_positions.append((x-1, x-1))
                    if x < GRID_SIZE and (14-x) < GRID_SIZE:
                        wall_positions.append((x, 14-x))
                        if difficulty > 8:  # Parallel diagonals
                            if x-1 < GRID_SIZE and (15-x) < GRID_SIZE:
                                wall_positions.append((x-1, 15-x))
        
        level["walls"].extend(list(set(wall_positions)))  # Remove duplicates
        
        # Keys - Many required keys in strategic positions
        if difficulty >= 2 or i % 3 == 0:  # Even more frequent keys
            positions = [(5, 5), (9, 9), (5, 9), (9, 5), (7, 4), (7, 10), (4, 7), (10, 7)]
            key_count = min(3 + difficulty // 2, len(positions))  # More keys required
            
            for k in range(key_count):
                pos = positions[k]
                if 0 <= pos[0] < GRID_SIZE and 0 <= pos[1] < GRID_SIZE:
                    level["keys"].append(pos)
        
        # Ensure player and goal positions are valid
        if not (0 <= level["player"][0] < GRID_SIZE and 0 <= level["player"][1] < GRID_SIZE):
            level["player"] = (1, 1)
        if not (0 <= level["goal"][0] < GRID_SIZE and 0 <= level["goal"][1] < GRID_SIZE):
            level["goal"] = (GRID_SIZE-2, GRID_SIZE-2)
        
        levels.append(level)
    
    return levels

def main():
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Break The Puzzle!")
    clock = pygame.time.Clock()
    
    # Get levels and initialize first level
    levels = get_levels()
    if not levels:
        print("Error: No levels found!")
        pygame.quit()
        sys.exit()
        
    current_level = 0
    level = Level(levels[current_level])
    total_score = 0
    font = pygame.font.Font(None, 36)
    last_move_time = 0
    
    while True:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    level = Level(levels[current_level])
        
        # Handle continuous key presses with delay
        if current_time - last_move_time >= MOVE_DELAY:
            keys = pygame.key.get_pressed()
            moved = False
            
            if keys[pygame.K_LEFT]:
                level.move_player(Vector2(-1, 0))
                moved = True
            elif keys[pygame.K_RIGHT]:
                level.move_player(Vector2(1, 0))
                moved = True
            elif keys[pygame.K_UP]:
                level.move_player(Vector2(0, -1))
                moved = True
            elif keys[pygame.K_DOWN]:
                level.move_player(Vector2(0, 1))
                moved = True
                
            if moved:
                last_move_time = current_time
        
        # Update moving platforms and other elements
        level.update()
        
        # Draw everything
        screen.fill(WHITE)
        level.draw(screen)
        
        # Draw HUD
        score_text = font.render(f'Score: {level.get_score()}', True, BLACK)
        level_text = font.render(f'Level: {current_level + 1}/{len(levels)}', True, BLACK)
        moves_text = font.render(f'Moves: {level.moves}', True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 50))
        screen.blit(moves_text, (10, 90))
        
        # Check win condition
        if level.is_complete():
            total_score += level.get_score()
            current_level += 1
            
            if current_level >= len(levels):
                # Game complete
                complete_text = font.render('Game Complete!', True, BLACK)
                final_score_text = font.render(f'Final Score: {total_score}', True, BLACK)
                screen.blit(complete_text, (WINDOW_SIZE/2 - 100, WINDOW_SIZE/2 - 50))
                screen.blit(final_score_text, (WINDOW_SIZE/2 - 100, WINDOW_SIZE/2 + 50))
            else:
                # Next level
                level = Level(levels[current_level])
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
