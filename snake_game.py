# Author
# William Lucca

from launchpad import *
from launchpad_game import LaunchpadGame
from collections import deque
from math import floor
import enum


class GameState(enum.Enum):
    """Enum for representing the game's possible states from start to finish"""
    
    tutorial = 0
    starting = 1
    snaking = 2
    dying = 3
    show_score = 4


class TileType(enum.Enum):
    """Enum for representing the possible occupants of a tile on the board"""
    
    empty = 0
    snake = 1
    food = 2


def is_opposite_dir(dir1, dir2):
    """Returns whether or not the two directions are opposite each other
    
    :return: True if opposite directions, False otherwise
    """
    
    if dir1 is Direction.up and dir2 is Direction.down:
        return True
    if dir1 is Direction.down and dir2 is Direction.up:
        return True
    if dir1 is Direction.left and dir2 is Direction.right:
        return True
    if dir1 is Direction.right and dir2 is Direction.left:
        return True
    
    return False


class Direction(enum.Enum):
    """Enum for representing the possible directions for the snake to move"""
    
    up = 0
    down = 1
    left = 2
    right = 3


# Some color constants
R = (3, 0)
G = (0, 3)
Y = (3, 3)
K = (0, 0)


class SnakeGame(LaunchpadGame):
    """A game of Snake using the LaunchpadGame base class
    
    How to play:
     - Move the snake to eat the food squares
     - Eating food makes the snake longer
     - Moving off the edge wraps around to the other side
     - You lose if you run into yourself
    
    Controls:
     - Move the snake using arrow buttons at the top, or
     - Tap a button on the top, right, bottom, or left of the main grid
     - Tap the red "Record Arm" button to quit
    """
    
    # Game cover art
    cover = [
        [K, R, R, R, R, K],
        [K, R, K, K, R, K],
        [K, R, K, K, R, K],
        [K, K, K, R, R, K],
        [K, G, K, R, K, K],
        [K, K, K, R, R, R]
    ]
    
    state = GameState.tutorial
    
    # Input buttons
    UP_BUTTONS = [
        (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
        (2, 2), (3, 2), (4, 2), (5, 2),
        (3, 3), (4, 3)
    ]
    DOWN_BUTTONS = [
        (3, 6), (4, 6),
        (2, 7), (3, 7), (4, 7), (5, 7),
        (1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (6, 8)
    ]
    LEFT_BUTTONS = [
        (0, 2),
        (0, 3), (1, 3),
        (0, 4), (1, 4), (2, 4),
        (0, 5), (1, 5), (2, 5),
        (0, 6), (1, 6),
        (0, 7)
    ]
    RIGHT_BUTTONS = [
        (7, 2),
        (6, 3), (7, 3),
        (5, 4), (6, 4), (7, 4),
        (5, 5), (6, 5), (7, 5),
        (6, 6), (7, 6),
        (7, 7)
    ]
    GRID_BUTTONS = {
        Direction.up: UP_BUTTONS,
        Direction.down: DOWN_BUTTONS,
        Direction.left: LEFT_BUTTONS,
        Direction.right: RIGHT_BUTTONS
    }
    ARROW_BUTTONS = {
        Direction.up: (0, 0),
        Direction.down: (1, 0),
        Direction.left: (2, 0),
        Direction.right: (3, 0)
    }
    BUT_RESTART = (8, 7)
    BUT_QUIT = (8, 8)
    
    # Colors
    COL_ARROW = R
    COL_GRID = Y
    COL_QUIT = R
    COL_RESTART = G
    COL_SNAKE = [
        (3, 0),
        (2, 0),
        (1, 0)
    ]
    COL_DEAD_SNAKE = (3, 1)
    COL_FOOD = G
    
    # Timing
    TIM_GRID_BUTTONS = 0.06
    TIM_STARTUP = 0.5
    TIM_TUTORIAL_FLASH = 1.2
    TIM_TUTORIAL_SNAKE = 0.11
    TIM_SNAKE_FLASH = 0.075
    TIM_SHOW_SCORE = 0.04
    tmr_snake = 0
    
    # Game board
    BOARD_WIDTH = 8
    BOARD_HEIGHT = 8
    board = [[]]
    
    # Snake variables
    SNAKE_SPD = 3.2  # Squares per second
    SNAKE_UPDATE_DELAY = 1.0 / SNAKE_SPD
    INIT_SNAKE_LOC = (1, 8)
    INIT_SNAKE_DIR = Direction.up
    INIT_SNAKE_LEN = 5
    snake_loc = INIT_SNAKE_LOC
    snake_dir = INIT_SNAKE_DIR
    snake_len = INIT_SNAKE_LEN
    snake_body = deque()
    dir_buffer = deque()
    
    # Food variables
    FOOD_VALUE = 1
    INIT_FOOD_LOC = (5, 5)
    food_loc = INIT_FOOD_LOC
    
    def setup(self, restart=False):
        """Reset game variables to start a new game from the beginning"""
        
        super().setup()
        
        self.lp.reset()
        
        # Snake setup
        self.snake_loc = self.INIT_SNAKE_LOC
        self.snake_len = self.INIT_SNAKE_LEN
        self.snake_dir = self.INIT_SNAKE_DIR
        self.snake_body = deque()
        self.dir_buffer = deque()
        
        # Food setup
        self.food_loc = self.INIT_FOOD_LOC
        
        # Board setup
        self.board = [[TileType.empty for i in range(self.BOARD_WIDTH)]
                      for j in range(self.BOARD_HEIGHT)]
        self.board[self.food_loc[0]][self.food_loc[1]] = TileType.food
        
        # Initial state
        self.change_state(GameState.tutorial)
        
        if restart:
            # If game was restart from the show_score state, don't show the
            # directional input tutorial
            self.start_timer(False,
                             function=self.tutorial,
                             timeout=self.TIM_STARTUP)
        else:
            # If game was just started, show directional input part of tutorial
            self.start_timer(True,
                             function=self.tutorial,
                             timeout=self.TIM_STARTUP)
    
    def input(self, button_event):
        """Accept input to control snake if in snaking state"""
        
        super().input(button_event)
        
        if self.state in [GameState.starting, GameState.snaking]:
            x = button_event[0]
            y = button_event[1]
            
            # If button pressed down
            if button_event[2]:
                # Directional input
                for direction in Direction:
                    # Grid buttons
                    if (x, y) in self.GRID_BUTTONS[direction]:
                        # Buffer direction change
                        self.try_dir_change(direction)
                        
                        # Color whole button field for a short interval of time
                        self.draw_grid_buttons(direction, True)
                        self.start_timer(direction, False,
                                         function=self.draw_grid_buttons,
                                         timeout=self.TIM_GRID_BUTTONS)
                        
                        # If waiting to begin play and a valid direction was
                        # pressed, begin the game
                        if self.state is GameState.starting:
                            if not is_opposite_dir(direction, self.snake_dir):
                                self.change_state(GameState.snaking)
            
            # If button released
            if not button_event[2]:
                # Quit button
                if (x, y) == self.BUT_QUIT:
                    self.playing = False
        
        if self.state is GameState.show_score:
            x = button_event[0]
            y = button_event[1]
            
            # If button released
            if not button_event[2]:
                # Quit button
                if (x, y) == self.BUT_QUIT:
                    self.playing = False
                
                # Restart button
                if (x, y) == self.BUT_RESTART:
                    self.setup(restart=True)
    
    def update_snake(self):
        """Performs one move for the snake, checking for food and collision"""
        
        # Get next direction from buffer
        if len(self.dir_buffer) > 0:
            self.snake_dir = self.dir_buffer.pop()
        
        if not self.move_snake():
            # Move didn't go so well, time to die
            self.change_state(GameState.dying)
            return
        
        # Update snake head
        self.snake_body.appendleft(self.snake_loc)
        x = self.snake_loc[0]
        y = self.snake_loc[1]
        self.board[x][y] = TileType.snake
        
        # Update snake tail and erase it
        if len(self.snake_body) > self.snake_len:
            tail = self.snake_body.pop()
            self.board[tail[0]][tail[1]] = TileType.empty
            self.lp.led_ctrl_xy(tail[0], tail[1] + 1, *K)
        
        self.draw_snake()
    
    def move_snake(self):
        """Move the snake's head and check for obstacles
        
        Doesn't check for obstacles (death)
        :return: True if no obstacle is hit and movement is successful, False
        if obstacle is hit and death is imminent
        """
        
        # Find where snake is trying to move
        target_loc = [self.snake_loc[0], self.snake_loc[1]]
        if self.snake_dir is Direction.up:
            target_loc[1] -= 1
        elif self.snake_dir is Direction.down:
            target_loc[1] += 1
        elif self.snake_dir is Direction.left:
            target_loc[0] -= 1
        elif self.snake_dir is Direction.right:
            target_loc[0] += 1
        
        # Wrap around
        if target_loc[0] < 0:
            target_loc[0] = self.BOARD_WIDTH - 1
        if target_loc[0] >= self.BOARD_WIDTH:
            target_loc[0] = 0
        if target_loc[1] < 0:
            target_loc[1] = self.BOARD_HEIGHT - 1
        if target_loc[1] >= self.BOARD_HEIGHT:
            target_loc[1] = 0
        
        # Check for snake
        if self.board[target_loc[0]][target_loc[1]] is TileType.snake:
            # No movement, just death
            return False
        
        # Check for delicious food
        if self.board[target_loc[0]][target_loc[1]] is TileType.food:
            self.eat_food()
        
        # Make the move
        self.snake_loc = (target_loc[0], target_loc[1])
        return True
    
    def eat_food(self):
        """Increases snake length and moves the food"""
        
        self.snake_len += self.FOOD_VALUE
        
        # Find a spot for the delicious food
        new_x = -1
        new_y = -1
        is_bad_loc = True
        while is_bad_loc:
            # Pick a random tile
            new_x = random.randint(0, self.BOARD_WIDTH - 1)
            new_y = random.randint(0, self.BOARD_HEIGHT - 1)
            
            # Make sure its empty
            is_bad_loc = self.board[new_x][new_y] is not TileType.empty
        
        # Move the delicious food
        old_x = self.food_loc[0]
        old_y = self.food_loc[1]
        self.board[old_x][old_y] = TileType.empty
        self.lp.led_ctrl_xy(old_x, old_y + 1, *K)
        self.board[new_x][new_y] = TileType.food
        self.lp.led_ctrl_xy(new_x, new_y + 1, *self.COL_FOOD)
        self.food_loc = (new_x, new_y)
    
    def try_dir_change(self, direction):
        """Buffer the given direction for turning on the next available frame
        
        :param direction: Direction to turn in
        """
        
        # Store the current direction or last direction buffered
        if len(self.dir_buffer) > 0:
            prev_dir = self.dir_buffer[0]
        else:
            prev_dir = self.snake_dir
        
        # Do not buffer if same direction or opposite direction as previous
        if direction is not prev_dir:
            if not is_opposite_dir(direction, prev_dir):
                self.dir_buffer.appendleft(direction)
    
    def draw_snake(self):
        """Draws everything in snake body to the board"""
        
        for i in range(len(self.snake_body)):
            # Launchpad led coords
            x = self.snake_body[i][0]
            y = self.snake_body[i][1] + 1
            
            # Draw color from COL_SNAKE gradient
            color_id = floor(i / len(self.snake_body) * len(self.COL_SNAKE))
            self.lp.led_ctrl_xy(x, y, *self.COL_SNAKE[color_id])
    
    def change_state(self, new_state):
        """Transitions the game's state to the given state
        
        Always change game state with this function to ensure that any entry
        functionality for the state is run.
        :param new_state: The state to transition into
        :return: True if there was a state transition, False otherwise
        """
        
        state_transition = self.state is new_state
        self.state = new_state
        
        if self.state is GameState.starting:
            # Show the quit button
            self.lp.led_ctrl_xy(*self.BUT_QUIT, *self.COL_QUIT)
        
        elif self.state is GameState.snaking:
            # Start the real game with a snake update timer
            self.tmr_snake = self.start_timer(function=self.update_snake,
                                              timeout=self.SNAKE_UPDATE_DELAY,
                                              repeat=True)
        
        elif self.state is GameState.dying:
            self.stop_timer(self.tmr_snake)
            
            # Flashy snake death animation
            anim = [(None, self.TIM_SNAKE_FLASH)]
            for i in range(len(self.snake_body)):
                coords = self.snake_body[i]
                anim.append((coords[0], coords[1] + 1, *K,
                             self.lp.led_ctrl_xy, 0))
                anim.append((coords[0], coords[1] + 1, *self.COL_DEAD_SNAKE,
                             self.lp.led_ctrl_xy, self.TIM_SNAKE_FLASH))
            
            # Change state to score display
            anim.append((GameState.show_score,
                         self.change_state, 5 * self.TIM_SNAKE_FLASH))
            
            self.start_anim(*anim)
        
        elif self.state is GameState.show_score:
            self.show_score()
        
        return state_transition
    
    def tutorial(self, input_tutorial=True):
        """Displays the tutorial and advances to starting state
        
        Plays an animation showing the directional input buttons and the snake
        slithering in, then switches to the starting state to await input.
        :param input_tutorial: If True, show the portion of the tutorial that
        illuminates the directional input buttons
        """
        
        # Tutorial animation
        anim = []
        
        # Show the tutorial for the buttons if input_tutorial is True
        if input_tutorial:
            
            # Turn all directions on and off one at a time
            for direction in Direction:
                anim.append((direction, True,
                             self.draw_grid_buttons, 0))
                anim.append((direction, True,
                             self.draw_arrow_buttons, 0))
                anim.append((direction, False,
                             self.draw_grid_buttons, self.TIM_TUTORIAL_FLASH))
                anim.append((direction, False,
                             self.draw_arrow_buttons, 0))
            
            # Off for a moment
            anim.append((None, 0.5 * self.TIM_TUTORIAL_FLASH))
            
            # All directions on
            for direction in Direction:
                anim.append((direction, True,
                             self.draw_grid_buttons, 0))
                anim.append((direction, True,
                             self.draw_arrow_buttons, 0))
            
            # On for a moment
            anim.append((None, 0.4 * self.TIM_TUTORIAL_FLASH))
            
            # All directions off
            for direction in Direction:
                anim.append((direction, False,
                             self.draw_grid_buttons, 0))
                anim.append((direction, False,
                             self.draw_arrow_buttons, 0))
        # End input tutorial
        
        # Make snake move forward 7 times
        for i in range(7):
            anim.append((self.update_snake, self.TIM_TUTORIAL_SNAKE))
        
        # Show food and turn snake
        anim.append((self.food_loc[0], self.food_loc[1] + 1, *self.COL_FOOD,
                     self.lp.led_ctrl_xy, 0))
        anim.append((Direction.right,
                     self.try_dir_change, 0))
        
        # Make snake move forward 2 more times
        for i in range(2):
            anim.append((self.update_snake, self.TIM_TUTORIAL_SNAKE))
        
        # Switch to starting state
        anim.append((GameState.starting,
                     self.change_state, self.SNAKE_UPDATE_DELAY))
        
        self.start_anim(*anim)
    
    def show_score(self):
        """Display an animation of the snake filling the screen
        
        Also lights the quit and restart buttons in the bottom right corner.
        """
        
        # Clean up a bit
        self.lp.reset()
        self.stop_all_timers()
        
        # Show restart and quit buttons
        self.lp.led_ctrl_xy(*self.BUT_RESTART, *self.COL_RESTART)
        self.lp.led_ctrl_xy(*self.BUT_QUIT, *self.COL_QUIT)
        
        # The maximum score is the board's total number of tiles
        score = min(self.snake_len, self.BOARD_WIDTH * self.BOARD_HEIGHT)
        
        # Final snake length display animation
        anim = [(None, 8 * self.TIM_SHOW_SCORE)]
        for i in range(score):
            x = i % self.BOARD_WIDTH
            y = i // self.BOARD_WIDTH + 1
            
            # Light up in food color, then blink to snake color
            anim.append((x, y, *self.COL_FOOD,
                         self.lp.led_ctrl_xy, 0))
            anim.append((x, y, *self.COL_SNAKE[0],
                         self.lp.led_ctrl_xy, self.TIM_SHOW_SCORE))
        
        # Play score animation on loop
        self.start_anim(*anim, repeat=True)
    
    def draw_grid_buttons(self, direction, is_on):
        """Draws the grid buttons for the selected direction on or off
        
        :param direction: Which direction's grid buttons to draw
        :param is_on: If True draw them on, if False draw the board underneath
        """
        
        if is_on:
            for coord in self.GRID_BUTTONS[direction]:
                self.lp.led_ctrl_xy(*coord, *self.COL_GRID)
        else:
            # Draw snake
            self.draw_snake()
            
            # Draw everything else
            for coord in self.GRID_BUTTONS[direction]:
                x = coord[0]
                y = coord[1]
                
                # Draw food
                if self.board[x][y - 1] is TileType.food:
                    self.lp.led_ctrl_xy(*coord, *self.COL_FOOD)
                
                # Draw empty
                if self.board[x][y - 1] is TileType.empty:
                    self.lp.led_ctrl_xy(*coord, *K)
    
    def draw_arrow_buttons(self, direction, is_on):
        """Draws the arrow button for the selected direction on or off
        
        :param direction: Which direction's grid buttons to draw
        :param is_on: If True draw them on, if False draw them off
        """
        
        if is_on:
            self.lp.led_ctrl_xy(*self.ARROW_BUTTONS[direction],
                                *self.COL_ARROW)
        else:
            self.lp.led_ctrl_xy(*self.ARROW_BUTTONS[direction],
                                *K)
    
    def __str__(self):
        return 'SnakeGame'


def main():
    lp = Launchpad()
    SnakeGame(lp).play()


if __name__ == '__main__':
    main()
