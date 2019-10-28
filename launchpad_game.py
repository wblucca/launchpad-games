# Author
# William Lucca

from time import perf_counter
from launchpad import *


class LaunchpadGame:
    """Defines a game with a main loop and event system to handle input.
    
    Also features a fixed time loop for real-time game logic. All timekeeping
    functions and properties use seconds.
    """
    
    # Launchpad
    lp = None
    
    # Game loop
    fixed_update_delay = 0.0333333333  # Default to 30Hz
    fixed_update_timer = 0
    playing = True
    
    # Timekeeping
    game_start_time = 0
    prev_time = 0
    delta_time = 0
    
    # Timers created by start_timer
    timers = {}
    
    # Cover art for the game (default to all yellow)
    # Must be a 6x6 grid of colors (R, G)
    cover = [[(3, 3) for i in range(6)] for j in range(6)]
    
    def __init__(self, launchpad_):
        # Store launchpad instance
        self.lp = launchpad_
    
    def setup(self):
        """Called when the game begins play"""
        
        self.playing = True
        self.stop_all_timers()
    
    def cleanup(self):
        """Called when the game is quitting"""
        
        self.lp.clear_input()
        self.stop_all_timers()
        self.lp.reset()
    
    def input(self, button_event):
        """Called whenever a button event is received
        
        button_event is a table: [x, y, down]
        x and y are the coordinates of the button on the launchpad and down is
        True if the button is being pressed down, false if it is released.
        """
        pass
    
    def update(self):
        """Called as fast as the game loop can execute
        
        Use self.delta_time to get the duration of the last loop if you need
        things to happen in real-world time.
        """
        pass
    
    def fixed_update(self):
        """Called at a precise interval specified by fixed_update_rate
        
        Useful for drawing to launchpad because doing so too frequently will
        slow the game loop
        """
        pass
    
    def play(self):
        """The body of the game's execution
        
        ***Do not override or call this method in a derived class.***
        
        Begins with setup(), then enters the main game loop, where the
        following occurs on a loop until playing is set to False:
         - Measure time of last loop
         - Hand input
         - Update game
         - Run fixed update if enough time has elapsed
         - Draw any buffered led updates to launchpad (SLOW!)
        Finally, once playing is false, run cleanup() and exit.
        """
        
        self.setup()
        
        # Begin timing
        self.game_start_time = perf_counter()
        self.delta()
        
        while self.playing:
            # Clock duration of last loop
            self.delta()
            
            # Handle input
            button_event = self.lp.button_state_xy()
            if button_event:
                self.input(button_event)
            
            # Update game
            self.update()
            
            # If enough time elapsed, reset timer and run fixed_update()
            self.fixed_update_timer += self.delta_time
            if self.fixed_update_timer > self.fixed_update_delay:
                self.fixed_update_timer -= self.fixed_update_delay
                self.fixed_update()
            
            # Update timers elapsed time
            for key in list(self.timers):
                self.timers[key].update(self.delta_time)
            
            # Delete if completed
            to_del = [key for key in self.timers if self.timers[key].completed]
            for key in to_del:
                del self.timers[key]
            
            # Draw to launchpad
            self.lp.draw()
        
        self.cleanup()
    
    def start_timer(self, *args, function, timeout, repeat=False):
        """Start timer that runs a function after the elapsed time (seconds)
        
        ***Do not override.***
        :param function: Function to run after time expires
        :param timeout: Time (in seconds) before running code
        :param repeat: Whether or not to restart the timer after expiring and
        executing (running the timer on a loop)
        :return: An integer ID that acts as a reference for the timer
        """
        
        timer = Timer(*args, expire=timeout, function=function, repeat=repeat)
        self.timers[hash(timer)] = timer
        return hash(timer)
    
    def stop_timer(self, *timer_ids):
        """Stop and delete the currently running timers
        
        ***Do not override.***
        :param timer_ids: The IDs of the timers to stop
        :return: True if a timer was found and deleted, False otherwise
        """
        
        for timer_id in timer_ids:
            if timer_id in self.timers:
                del self.timers[timer_id]
                return True
        
        return False
    
    def stop_all_timers(self):
        """Stop and delete all running timers
        
        ***Do not override***
        :return: True if at least one timer was deleted, False otherwise
        """
        
        # If there are timers, clear them
        if len(self.timers) > 0:
            self.timers.clear()
            return True
        
        return False
    
    def start_anim(self, *tuples, repeat=False):
        """Start a multitude of timers with the given properties
        
        ***Do not override.***
        :param tuples: Multiple tuples, each structured like a call to
        start_timer, without the repeat argument. The timeout representing the
        delay between that keyframe timer and the previous.
        :param repeat: Whether or not to restart the animation after expiring
        and executing all functions (whether or not to loop)
        :return: A list of all of the timer IDs of the animation frames
        """
        
        # For storing all of the IDs of the timers in the animation
        timer_ids = []
        
        # Store total animation time
        total_time = 0
        for tuple_ in tuples:
            total_time += tuple_[-1]
        
        # The time of the last frame in the animation so far
        running_time = 0
        
        # Create the timers with the same expiration time so they loop properly
        for tuple_ in tuples:
            # Update accumulated time from timers
            running_time += tuple_[-1]
            
            # Create the timer
            timer_id = self.start_timer(*tuple_[:-2],
                                        function=tuple_[-2],
                                        timeout=total_time,
                                        repeat=repeat)
            
            # Timers start with some time already elapsed so that they finish
            # when specified in the arguments, despite having the same
            # expiration time when created
            self.timers[timer_id].passed = total_time - running_time
            
            # Store ID to return at the end
            timer_ids.append(timer_id)
        
        return timer_ids
    
    def delta(self):
        """Set delta_time equal to time since last call to delta()
        
        ***Do not override or call this method in a derived class.***
        It is used for timing the fixed update loop.
        """
        
        cur_time = perf_counter()
        self.delta_time = cur_time - self.prev_time
        self.prev_time = cur_time
    
    def get_time(self):
        """Return the time since the game loop started
        
        ***Do not override.***
        """
        
        return perf_counter() - self.game_start_time
    
    def __str__(self):
        """Please override this with the name of the game"""
        
        return 'LaunchpadGame'


class Timer:
    """Defines a timer that runs a function with the given args after expiring
    
    Can also be run on a loop. Must be updated with elapsed time to process
    timing, run code, etc.
    """
    
    passed = 0
    expire = 0
    repeat = False
    function = None
    func_args = []
    completed = False
    
    def __init__(self, *args, expire, function, repeat=False):
        """Creates a Timer
        
        :param args: Optional arguments to the given function
        :param expire: When to have the timer expire (seconds)
        :param function: What to run on expiring
        :param repeat: Whether or not to repeat after expiring
        """
        
        self.expire = expire
        self.function = function
        self.func_args = args
        self.repeat = repeat
    
    def update(self, t):
        """Simulates an amount of time, updating and running code appropriately
        
        :param t: How much time to simulate
        :return: True if timer is expired, false otherwise
        """
        # Increment time
        self.passed += t
        
        # Check if timer expired
        if not self.completed and self.passed > self.expire:
            # Execute timer code
            if self.function:
                self.function(*self.func_args)
            
            # Reset time if set to repeat, mark complete otherwise
            if self.repeat:
                self.passed -= self.expire
            else:
                self.completed = True
        
        return self.completed


def test():
    """For testing the LaunchpadGame class"""
    
    # Setup the Launchpad instance
    lp = Launchpad()
    lp.open()
    lp.reset()
    
    class TestGame(LaunchpadGame):
        """Test game that prints info and stops on any released button"""
        
        num_updates = 0
        num_fixed_updates = 0
        
        loop_tmr = None
        timers100 = []
        
        def setup(self):
            """Print that the game is setting up and make some timers"""
            
            print('Setting up', self.__str__())
            
            # Looping timer deleted on input
            self.loop_tmr = self.start_timer('Every', '1', 'second',
                                             timeout=1,
                                             function=lambda a, b, c: print(a,
                                                                            b,
                                                                            c),
                                             repeat=True)
            
            # 100 looping timers that don't delete and 100 non-looping timers
            for i in range(100):
                string_ = 'Looper: ' + str(3 + i / 100000) + ' seconds'
                self.start_timer(string_,
                                 timeout=3 + i / 100000,
                                 function=lambda x: print(x),
                                 repeat=True)
                id_ = self.start_timer('7 second timer: ' + str(i),
                                       timeout=7,
                                       function=lambda y: print(y))
                self.timers100.append(id_)
            
            # Decimate the 100 non-looping timers
            for i in range(100):
                if random.random() < 0.1:
                    print('Destroy 7 second timer', i)
                    self.stop_timer(self.timers100[i])
            
            print('Loop timer ID:', self.loop_tmr)
        
        def cleanup(self):
            """Print that the game is cleaning up"""
            print('Cleaning up', self.__str__())
        
        def input(self, button_event):
            """Set the game to stop on any released button"""
            
            self.stop_timer(self.loop_tmr)
            if not button_event[2]:
                print(button_event)
                game.playing = False
        
        def update(self):
            """Print delta time every 1000 updates for 1 second"""
            
            self.num_updates += 1
            if self.num_updates % 1000 == 0 and self.get_time() < 1:
                # print('Loop duration:', self.delta_time)
                pass
        
        def fixed_update(self):
            """Print number of fixed updates and draw 1 random led"""
            
            self.num_fixed_updates += 1
            # print('Num fixed updates:', self.num_fixed_updates)
            # print('Real time:', self.get_time())
            
            self.lp.led_ctrl_xy(random.randint(0, 8),
                                random.randint(0, 8),
                                random.randint(0, 3),
                                random.randint(0, 3))
        
        def __str__(self):
            return 'TestGame'
    
    game = TestGame(lp)
    game.play()
    print(game)
    
    lp.close()


if __name__ == '__main__':
    test()
