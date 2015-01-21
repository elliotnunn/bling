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

import sys
sys.path.insert(0, "../")

import pygame
import core
import ui

class RapidFire(core.Client):
    def _setup(self, graf_props):
        self.ifdel = 0
        self.lastfire = self.t
        
        self.font = pygame.freetype.Font("chicago.bdf")
        self.font.origin = True
        self.font.antialiased = False
        
        self.fg = (0, 0, 0); self.bg = (255, 255, 255);
    
    def _draw_frame(self, buffer, is_initial):
        delta = self.t - self.lastfire
        self.lastfire = self.t
        
        if delta==0:
            fps = 0
        else:
            fps = 1000 / delta
        
        buffer.fill(self.bg)
        
        self.font.render_to(buffer, (1, 12), "frame time", fgcolor=self.fg, bgcolor=self.bg)
        self.font.render_to(buffer, (1, 24), "   set = %dms" % self.ifdel, fgcolor=self.fg, bgcolor=self.bg)
        self.font.render_to(buffer, (1, 36), "   actual = %dms" % delta, fgcolor=self.fg, bgcolor=self.bg)
        self.font.render_to(buffer, (1, 60), "rate = %dfps" % fps, fgcolor=self.fg, bgcolor=self.bg)
        
        return self.t + self.ifdel
    
    def _event(self, event):
        if event == "up":
            self.ifdel+=10
            return True
        elif event == "down":
            self.ifdel-=10
            return True
        else:
            return None

class PlaceholderMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        items = [
            ("Sorry dude!", None),
            ("  This is an", None),
            ("  unimplemented", None),
            ("  menu.     :-(", None)
        ]
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Dang it!")

class CrashMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        def create_spawner(crash_at):
            def menuspawner(server):
                server.add_client(CrashyException(graf_props, crash_at=crash_at))
            return menuspawner

        crashes = ["_setup", "_event", "_draw_frame 1st", "_draw_frame other"]
        items = [(x, create_spawner(x)) for x in crashes]
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Crash where?")

class CrashyException(bling_core.Client):
    def _setup(self, graf_props, crash_at=""):
        self.crash_at = crash_at
        if self.crash_at == "_setup":
            1/0
    
    def _event(self, event):
        if self.crash_at == "_event":
            1/0
        elif event == "ok":
            return True
    
    def _draw_frame(self, buffer, is_initial):
        if is_initial and self.crash_at == "_draw_frame 1st":
            1/0
        elif not is_initial and self.crash_at == "_draw_frame later":
            1/0

class PrettyPicture(bling_core.Client):
    def _setup(self, graf_props, **kwargs):
        self.image = pygame.image.load(kwargs["file"])
    
    def _draw_frame(self, buffer, is_initial):
        # buffer.fill((255, 255, 255))
        # buffer.blit(pygame.transform.scale(self.image, (80, 64)), (24, 0))
        buffer.blit(self.image, (0, 0))
