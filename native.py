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


import pygame as pg
from threading import Thread
from kit import SexyMenu


class MainMenu(SexyMenu):
    def _setup(self, **kwargs):
        mni = [
            self.itm("First positional argument of print", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Back1", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back  3", True, print, "First positional argument of print!"),
            self.itm("Back   4", True, print, "First positional argument of print!"),
            self.itm("Back    5", True, print, "First positional argument of print!"),
            self.itm("First positional argument of print", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Back1", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back  3", True, print, "First positional argument of print!"),
            self.itm("Back   4", True, print, "First positional argument of print!"),
            self.itm("Back    5", True, print, "First positional argument of print!"),
            self.itm("First positional argument of print", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Back1", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back  3", True, print, "First positional argument of print!"),
            self.itm("Back   4", True, print, "First positional argument of print!"),
            self.itm("Back    5", True, print, "First positional argument of print!"),
            self.itm("First positional argument of print", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Back1", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back  3", True, print, "First positional argument of print!"),
            self.itm("Back   4", True, print, "First positional argument of print!"),
            self.itm("Back    5", True, print, "First positional argument of print!"),
            self.itm("First positional argument of print", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Back1", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back  3", True, print, "First positional argument of print!"),
            self.itm("Back   4", True, print, "First positional argument of print!"),
            self.itm("Back    5", True, print, "First positional argument of print!"),
            
        ]
        
        SexyMenu._setup(self, title="Zeitgeber", menu_isroot=True, menu_items=mni, **kwargs)

class FinalSink():
    """\
    This is a class.
    I am still getting used to docstrings...
    """
    
    def __init__(self):
        self.client = None
        
        pg.display.init()
        pg.display.set_caption("bling")
        self.buff = pg.display.set_mode((128, 64))
        
        def event_loop():
            pg.event.set_blocked([
                pg.MOUSEMOTION,
                pg.ACTIVEEVENT,
                ])
            while True:
                evt = pg.event.wait()
                self._pass_down_event(evt)
                if evt.type == pg.QUIT: break
        
        #_thread.start_new_thread(evt_get_loop, ())
        self.event_thread = Thread(target=event_loop, name="SDL event loop")
        self.event_thread.start()
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
        
        self.notify_client_dirty()  # grab something off that client
    
    def notify_client_dirty(self):
        with self.client.buff_sem:
            self.buff.blit(self.client.fbuff, (0,0))
        
        pg.display.flip()
        
        self.client.server_allows_draw()
    
    def _pass_down_event(self, evt):
        if self.client == None: return
        meaning = None
        
        if evt.type == pg.MOUSEBUTTONDOWN:
            btn = evt.button
            
            if btn == 4:
                meaning, content = "directional", "up"
            elif btn == 5:
                meaning, content = "directional", "down"
            elif btn == 3:
                meaning, content = "abstract", "back"
            elif btn == 1:
                meaning, content = "abstract", "ok"
            
        elif evt.type == pg.KEYDOWN:
            key = evt.key
            
            if key == 273:
                meaning, content = "directional", "up"
            elif key == 274:
                meaning, content = "directional", "down"
            elif key == 275:
                meaning, content = "directional", "right"
            elif key == 276:
                meaning, content = "directional", "left"
            elif key == 27:
                meaning, content = "abstract", "back"
            elif key == 13:
                meaning, content = "abstract", "ok"
        
        if meaning:
            evt_new = pg.event.Event(pg.USEREVENT, meaning=meaning, content=content)
        else:
            evt_new = evt
        
        self.client.event(evt_new)

fs = FinalSink()

fs.add_client(MainMenu())

print("main thread has had its run")