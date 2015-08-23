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


import _thread
import sys
import tty
import termios
import pygame as pg


class TerminalInput:
    def as_add_source(self, source):
        self.source = source
        
        _thread.start_new_thread(self._loop, ())
    
    def as_remove_source(self, client):
        self.source = None
    
    def _loop(self):
        stdin = sys.stdin.fileno()
        saved_attrs = termios.tcgetattr(stdin)
        tty.setcbreak(stdin)
        
        try:
            while True:
                key = sys.stdin.read(1)
                self._dispatch_event(key)
                
                if key == 'q': break
        
        finally:
            termios.tcsetattr(stdin, termios.TCSADRAIN, saved_attrs)
    
    def _dispatch_event(self, key):
        src = self.source
        
        if key == 'k':
            src.as_input('select', kinetic='inst')
        elif key == 'x':
            src.as_input('escape', kinetic='inst')
        elif key == 'w':
            src.as_input('direction', dy=-1, kinetic=kinetic)
        elif key == 's':
            src.as_input('direction', dy=1, kinetic=kinetic)
        elif key == 'd':
            src.as_input('direction', dx=1, kinetic=kinetic)
        elif key == 'a':
            src.as_input('direction', dx=-1, kinetic=kinetic)
        elif key == 'q':
            src.as_quit()
        

class SdlInput:
    def as_add_source(self, source):
        self.source = source
        
        _thread.start_new_thread(self._loop, ())
    
    def as_remove_source(self, client):
        self.source = None
    
    def _loop(self):
        pg.event.set_blocked([pg.MOUSEMOTION, pg.ACTIVEEVENT])
        
        while True:
            sdl_evt = pg.event.wait()
            self._dispatch_event(sdl_evt)
            
            if sdl_evt.type == pg.QUIT: break
    
    def _dispatch_event(self, evt):
        src = self.source
        
        if evt.type == pg.MOUSEBUTTONDOWN:
            
            if evt.button == 4:
                src.as_input('direction', dy=-1, kinetic='inst')
            elif evt.button == 5:
                src.as_input('direction', dy=1, kinetic='inst')
            elif evt.button == 3:
                src.as_input('escape', kinetic='inst')
            elif evt.button == 1:
                src.as_input('select', kinetic='inst')
        
        elif evt.type == pg.KEYDOWN or evt.type == pg.KEYUP:
            
            kinetic = {pg.KEYDOWN: 'in', pg.KEYUP: 'out'}[evt.type]
            key = evt.key
            
            if key == 273:
                src.as_input('direction', dy=-1, kinetic=kinetic)
            elif key == 274:
                src.as_input('direction', dy=1, kinetic=kinetic)
            elif key == 275:
                src.as_input('direction', dx=1, kinetic=kinetic)
            elif key == 276:
                src.as_input('direction', dx=-1, kinetic=kinetic)
            elif key == 27:
                src.as_input('escape', kinetic=kinetic)
            elif key == 13:
                src.as_input('select', kinetic=kinetic)
        
        elif evt.type == pg.QUIT:
            
            src.as_quit()
