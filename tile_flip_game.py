# Author
# William Lucca

from launchpad import *
from random import randint
import math


class TileFlipGame:
    # Game variables
    LOOP_DELAY = 10
    
    # Board variables
    INIT_WIDTH = 4
    INIT_HEIGHT = 4
    
    boardWidth = INIT_WIDTH
    boardWidthMin = 0
    boardWidthMax = 0
    
    boardHeight = INIT_HEIGHT
    boardHeightMin = 0
    boardHeightMax = 0
    
    board = [[]]
    
    # Game cover art
    R = (3, 0)
    G = (0, 3)
    K = (0, 0)
    cover = [
        [G, G, G, G, G, G],
        [G, K, K, K, R, G],
        [G, K, K, R, R, G],
        [G, R, K, K, R, G],
        [G, R, R, K, K, G],
        [G, G, G, G, G, G]
    ]
    
    def __init__(self, lp):
        # Store launchpad instance
        self.lp = lp
    
    # The main game loop
    def play(self):
        # Start Launchpad instance with no input
        self.lp.close_input()
        self.lp.reset()
        
        self.boardWidth = self.INIT_WIDTH
        self.boardHeight = self.INIT_HEIGHT
        
        # True if user is attempting to quit the game
        quitting = False
        
        # Get the board ready to play
        if not self.setupBoard():
            return
        time.wait(500)
        self.scramble()
        
        # Start Launchpad instance input
        self.lp.open_input()
        
        # Query buttons via the "xy return strategy" until game is won or quit
        while True:
            self.lp.draw()
            time.wait(self.LOOP_DELAY)
            but = self.lp.button_state_xy()
            
            # Animations
            if quitting:
                self.quitAnimation()
            
            # When a button is pressed down...
            if but != [] and but[2]:
                
                # Call tilePress function on the pressed button
                if self.tilePress(but[0], but[1]):
                    
                    # If a tile was flipped, check for completed board
                    if self.checkWin():
                        self.win()
                        break
                
                # Check if quit button was pressed
                if but == [8, 8, True]:
                    if quitting:
                        # Second time quit button is pressed
                        self.quitGame()
                        break
                    else:
                        # First time quit button is pressed
                        quitting = True
                else:
                    # Pending quit has been canceled
                    quitting = False
                    self.lp.led_ctrl_xy(8, 8, 3, 0)
    
    def setupBoard(self):
        # True if user is attempting to quit the game
        quitting = False
        
        self.lp.led_ctrl_xy(0, 0, 3, 3)  # Larger height button yellow
        self.lp.led_ctrl_xy(1, 0, 3, 3)  # Smaller height button yellow
        self.lp.led_ctrl_xy(2, 0, 3, 3)  # Smaller width button yellow
        self.lp.led_ctrl_xy(3, 0, 3, 3)  # Larger width button yellow
        self.lp.led_ctrl_xy(8, 7, 0, 3)  # Continue button green
        self.lp.led_ctrl_xy(8, 8, 3, 0)  # Quit button red
        
        # Show default board
        self.initializeBoard()
        
        # Allow user to select their board size
        self.lp.open_input()
        # Query buttons until "continue" (Solo) is pressed or game is quit
        while True:
            self.lp.draw()
            time.wait(self.LOOP_DELAY)
            but = self.lp.button_state_xy()
            
            # Animations
            if quitting: self.quitAnimation()
            
            # When a button is pressed down...
            if but != [] and but[2] == True:
                if but[1] == 0 and 0 <= but[0] <= 3:
                    # Change size based on button pressed
                    self.dimensionChange(but[0])
                    
                    self.initializeBoard()
                
                if but == [8, 7, True]:
                    # Continue to game
                    break
                
                # Check if quit button was pressed
                if but == [8, 8, True]:
                    if quitting:
                        # Second time quit button is pressed
                        self.quitGame()
                        return False
                    else:
                        # First time quit button is pressed
                        quitting = True
                else:
                    # Pending quit has been canceled
                    quitting = False
                    self.lp.led_ctrl_xy(8, 8, 3, 0)
        
        # Make outside leds green
        [self.lp.led_ctrl_xy(i, 0, 0, 3) for i in range(0, 8)]
        [self.lp.led_ctrl_xy(8, j, 0, 3) for j in range(1, 9)]
        
        # Make quit button red
        self.lp.led_ctrl_xy(8, 8, 3, 0)
        
        self.lp.close_input()
        
        return True
    
    # Calculate the board's boundaries based on dimensions and draw it
    def initializeBoard(self):
        # Calculate board boundaries from width and height
        self.boardWidthMin = (9 - self.boardWidth) // 2
        self.boardWidthMax = self.boardWidthMin + self.boardWidth
        
        self.boardHeightMin = math.ceil((9 - self.boardHeight) / 2.0)
        self.boardHeightMax = self.boardHeightMin + self.boardHeight
        
        # Make all inside leds green
        for i in range(0, 8):
            for j in range(1, 9):
                self.lp.led_ctrl_xy(i, j, 0, 3)
        
        # Make board leds red
        for i in range(self.boardWidthMin, self.boardWidthMax):
            for j in range(self.boardHeightMin, self.boardHeightMax):
                self.lp.led_ctrl_xy(i, j, 3, 0)
        
        # Initialize logical board (set to True)
        self.board = [[True for j in range(0, self.boardHeight)]
                      for i in range(0, self.boardWidth)]
    
    numClicks = boardWidth * boardHeight * 2
    startDelay = 750
    
    # Does a nice real-time scrambling of the board
    def scramble(self):
        # Create animation speed curve (rational function)
        a = self.startDelay * (1 + (1 / self.numClicks))
        b = self.startDelay - a
        
        def getDelay(t):
            return a * (1 / (t + 1)) + b
        
        # Press random tiles numClicks number of times
        for i in range(0, self.numClicks):
            # Pick a random board tile and flip it
            randX = randint(self.boardWidthMin, self.boardWidthMax - 1)
            randY = randint(self.boardHeightMin, self.boardHeightMax - 1)
            self.tilePress(randX, randY)
            
            # Wait (based on rational function speed curve from above)
            delay = getDelay(i)
            time.wait(int(delay))
        
        # If a winning board comes up, scramble some more with 10 more presses
        while self.checkWin():
            for i in range(0, 10):
                # Pick a random board tile and flip it
                randX = randint(self.boardWidthMin, self.boardWidthMax - 1)
                randY = randint(self.boardHeightMin, self.boardHeightMax - 1)
                self.tilePress(randX, randY)
                
                time.wait(1)
    
    # Try to flip the pressed tile and any surrounding tiles
    # Returns True if at least one tile was flipped
    def tilePress(self, x, y):
        # Don't count presses outside of board
        if x < self.boardWidthMin or x >= self.boardWidthMax:
            return False
        
        if y < self.boardHeightMin or y >= self.boardHeightMax:
            return False
        
        # Define coordinates of tiles to flip relative to pressed tile
        dx = [0, 0, 1, 0, -1]
        dy = [0, -1, 0, 1, 0]
        
        # Attempt to flip all specified tiles
        for i in range(0, len(dx)):
            flipX = x + dx[i]
            flipY = y + dy[i]
            
            # Flip this tile if within boundaries of the board
            if self.boardWidthMin <= flipX < self.boardWidthMax:
                if self.boardHeightMin <= flipY < self.boardHeightMax:
                    self.flipTile(flipX - self.boardWidthMin,
                                  flipY - self.boardHeightMin)
        
        # Tile was flipped
        return True
    
    # Flip the specified tile (in board coordinates)
    def flipTile(self, x, y):
        if self.board[x][y]:
            self.board[x][y] = False
            self.lp.led_ctrl_xy(x + self.boardWidthMin,
                                y + self.boardHeightMin,
                                0, 0)
        else:
            self.board[x][y] = True
            self.lp.led_ctrl_xy(x + self.boardWidthMin,
                                y + self.boardHeightMin,
                                3, 0)
    
    # Change the dimensions of the board based on the ID of the button pressed
    def dimensionChange(self, buttonId):
        switcher = {
            0: [0, 1],  # Width + 0, Height + 1
            1: [0, -1],  # Width + 0, Height - 1
            2: [-1, 0],  # Width - 1, Height + 0
            3: [1, 0]  # Width + 1, Height + 0
        }
        dimensionMods = switcher.get(buttonId, [0, 0])
        
        # Apply the modification selected above
        self.boardWidth += dimensionMods[0]
        self.boardHeight += dimensionMods[1]
        
        # Clamp to range [2, 8]
        self.boardWidth = max(min(self.boardWidth, 8), 2)
        self.boardHeight = max(min(self.boardHeight, 8), 2)
    
    def checkWin(self):
        for i in range(0, self.boardWidth):
            for j in range(0, self.boardHeight):
                if not self.board[i][j]:
                    # Not winning board if any square is False
                    return False
        
        # Every square must be True. Win!
        return True
    
    def win(self):
        # Disable input
        self.lp.close_input()
        
        # Blink animation
        time.wait(500)
        self.lp.led_all_on()
        time.wait(500)
        self.lp.reset()
        time.wait(500)
        self.lp.led_all_on()
        time.wait(500)
        self.lp.reset()
        
        # Winner string
        self.lp.led_ctrl_string("WINNER!", 0, 3, -1, 5)
        
        # Close up shop
        self.lp.reset()
        self.lp.open()
    
    quitBlinkSpd = 750
    
    # Show quit text and quit game
    def quitGame(self):
        # Disable input
        self.lp.close_input()
        
        # Scroll text
        self.lp.reset()
        self.lp.led_ctrl_string("QUIT", 0, 3, -1, 4)
        
        # Close up shop
        self.lp.reset()
        self.lp.open()
    
    def quitAnimation(self):
        periodCoeff = 2 * math.pi / self.quitBlinkSpd
        cosine = math.cos(periodCoeff * time.get_ticks())
        redIntensity = 2 * cosine + 2
        self.lp.led_ctrl_xy(8, 8, redIntensity, 0)
    
    def __str__(self):
        return 'TileFlipGame'


def main():
    lp = Launchpad()
    TileFlipGame(lp).play()
    lp.close()


if __name__ == '__main__':
    main()
