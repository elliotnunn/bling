from bling_core import *
import threading

class StdinServer(InputServer, threading.Thread):
    def __init__(self):
        import tty, sys, termios
        threading.Thread.__init__(self)

    def run(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        ch = ""
        while ch != "q":
            tty.setraw(sys.stdin.fileno())
            
            # this blocks, and thank goodness
            ch = sys.stdin.read(1)
            if ch == "w":
                self.client.event("up")
            elif ch == "s":
                self.client.event("down")
            elif ch == "a":
                self.client.event("left")
            elif ch == "d":
                self.client.event("right")
            elif ch == "k":
                self.client.event("ok")
            elif ch == "b":
                self.client.event("back")
            elif ch == "q":
                self.client.event("quit")
        
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def add_client(self, client):
        self.client = client
        self.start()