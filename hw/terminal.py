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


from threading import Thread
import sys
import tty
import termios


class TermIn(Thread):
    def add_client(self, client):
        self.client = client
        self.daemon = True
        self.start()
    
    def run(self):
        KEY_TO_EVENT = {
            "w": "up",
            "a": "left",
            "s": "down",
            "d": "right",
            
            "k": "ok",
            "b": "back",
            "q": "quit",
            
            "e": "screenshot",
        }
        
        fd = sys.stdin.fileno()
        
        saved_attrs = termios.tcgetattr(fd)
        tty.setcbreak(sys.stdin.fileno())
        
        while True:
            key = sys.stdin.read(1)
            
            event = KEY_TO_EVENT.get(key)
            
            if event: self.client.event(event)
        
        termios.tcsetattr(fd, termios.TCSADRAIN, saved_attrs)
    
    def remove_client(self, client):
        self.client = None
