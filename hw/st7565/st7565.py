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

import pygame
import bling_core
import ctypes
import time

class ST7575Server(bling_core.Server):
    def __init__(self):
        self.libbuff=ctypes.CDLL('buff/libbuff.so')
        self.libbuff.init()
        self.libbuff.bklt(1)
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
        self.notify_client_dirty()
    
    def notify_client_dirty(self):
        self.client.buff_sem.acquire()
        self.libbuff.fling_buffer(self.client.fbuff._pixels_address)
        self.client.buff_sem.release()
        #pygame.time.wait(150)
        self.client.server_allows_draw()
    
    def deinit(self):
        self.libbuff.deinit()
