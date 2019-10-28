# Author
# William Lucca

from time import perf_counter
from launchpad import *
from snake_game import SnakeGame
import math

# Buttons
BUT_LEFT = (2, 0)
BUT_RIGHT = (3, 0)
BUT_START = (8, 7)
BUT_QUIT = (8, 8)

# Cover art border
BORDER_ANIM_DELAY = 0.08
BORDER_COORDS = [(0, 0) for i in range(28)]  # 28 border squares around cover
for i in range(7):
    BORDER_COORDS[i] = (i, 1)  # Top row
    BORDER_COORDS[i + 7] = (7, i + 1)  # Right column
    BORDER_COORDS[i + 14] = (7 - i, 8)  # Bottom row
    BORDER_COORDS[i + 21] = (0, (7 - i) + 1)  # Left column
    
# Menu leds
menu_leds = [(0, 0) for i in range(16)]

# Game dictionary
games = {}
selected_game = 0

lp = None


# Main function
def main():
    """Shows the player a menu to select and play games"""
    global lp
    global games, selected_game
    
    # Create a Launchpad instance and start it up
    lp = Launchpad()
    lp.open()
    lp.reset()
    
    populate_games()
    draw_main_menu()
    
    playing = True

    # Timekeeping
    last_time = 0
    anim_timer = 0

    while playing:
        # Get delta_time this loop
        cur_time = perf_counter()
        delta_time = cur_time - last_time
        last_time = cur_time

        # Get next input
        button = lp.button_state_xy()
        
        # Animate border
        anim_timer += delta_time
        if anim_timer > BORDER_ANIM_DELAY:
            anim_timer = 0
            draw_border()
        
        # Handle input (if any)
        if button:
            x = button[0]
            y = button[1]
            
            # If button pressed
            if button[2]:
                # Write red to pressed button if circle button
                if x == 8 or y == 0:
                    lp.led_ctrl_xy(x, y, 3, 0)
                
                if (x, y) == BUT_LEFT:
                    selected_game = (selected_game + 1) % len(games)
                    draw_cover()
                
                if (x, y) == BUT_RIGHT:
                    selected_game = (selected_game - 1) % len(games)
                    draw_cover()
            
            # If button released
            if not button[2]:
                # Write menu color to released button if circle button
                if y == 0:
                    lp.led_ctrl_xy(x, y, *menu_leds[x])  # Top row
                if x == 8:
                    lp.led_ctrl_xy(x, y, *menu_leds[7 + y])  # Right column
                
                if (x, y) == BUT_START:
                    lp.clear_input()
                    lp.reset()
                    games[selected_game].play()
                    draw_main_menu()
                
                if (x, y) == BUT_QUIT:
                    playing = False
        
        lp.draw()
    
    lp.reset()
    lp.close()


def draw_cover():
    """Draws the selected game's cover art"""
    
    game_cover = games[selected_game].cover
    
    # Draw game cover art
    for i in range(len(game_cover)):
        for j in range(len(game_cover[0])):
            led_x = i + 1
            led_y = j + 2
            lp.led_ctrl_xy(led_x, led_y, *game_cover[i][j])


def draw_border():
    """Draws one frame of the colored border animation"""
    
    length = len(BORDER_COORDS)
    
    # Constants for sine wave
    b = 2 * math.pi / length
    speed = 2
    
    # Draw sinusoid red/green design
    for i in range(length):
        # Sine function
        t = perf_counter()
        sine = math.sin(b*i + speed*t)  # Wave with period 28
        
        # Map sine value from [-1, 1] to [0, 4)
        red = min(math.floor(2 * sine + 2), 3)
        
        # Fade red and green colors
        lp.led_ctrl_xy(*BORDER_COORDS[i], red, 3 - red)


def draw_menu_buttons():
    """Draws all the circular buttons and interactive menu buttons"""
    global menu_leds
    
    def draw_menu_led(x, y, color):
        """Draws menu lights to launchpad and stores them in menu_leds
        
        :param x: x-coord of led
        :param y: y-coord of led
        :param color: color of led
        :return: None
        """
        lp.led_ctrl_xy(x, y, *color)
        if y != 0:
            menu_leds[7 + y] = color
        else:
            menu_leds[x] = color
    
    # Clear all circular buttons
    for i in range(8):
        draw_menu_led(i, 0, (0, 0))
        draw_menu_led(8, i + 1, (0, 0))
    
    # Color all menu buttons
    draw_menu_led(*BUT_LEFT, (3, 3))  # Select buttons yellow
    draw_menu_led(*BUT_RIGHT, (3, 3))
    draw_menu_led(*BUT_START, (0, 3))  # Start button green
    draw_menu_led(*BUT_QUIT, (3, 0))  # Quit button red


def draw_main_menu():
    """Draws the cover art, menu buttons, and cover art border"""
    draw_cover()
    draw_menu_buttons()
    draw_border()


def populate_games():
    """Initializes all of the game objects in the games dictionary"""
    global games
    games[0] = SnakeGame(lp)


if __name__ == '__main__':
    main()
