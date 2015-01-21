# This file is part of bling.

# Bling is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Bling is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Bling.  If not, see <http://www.gnu.org/licenses/>.

import bling_core
import threading

class StdinServer(bling_core.InputServer, threading.Thread):
    def __init__(self):
        import tty, sys, termios
        threading.Thread.__init__(self)

    def run(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        ch = ""
        while ch != "q":
            tty.setcbreak(sys.stdin.fileno())
            
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
            elif ch == "e":
                self.client.event("screenshot")
        
        
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def add_client(self, client):
        self.client = client
        self.start()
