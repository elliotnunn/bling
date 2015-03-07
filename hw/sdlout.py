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


from pygame import display, transform
#from video.sink import Sink

import os


class SDLDisplay():
    def __init__(self):
        #Sink.__init__(self)
        display.init()
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
        
        self.dispsurf = display.set_mode((128*4, 64*5)) # Actual window
        self.notify_client_dirty()
    
    def notify_client_dirty(self):
        with self.client.buff_sem:
            surf = self.client.fbuff
            transform.scale(surf, (self.dispsurf.get_width(), self.dispsurf.get_height()), self.dispsurf)
        
        display.flip()
        
        self.client.server_allows_draw()
    
    def remove_client(self, client):
        display.quit()
