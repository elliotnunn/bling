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


from video.sink import Sink

import os.path
import ctypes


class ST7565(Sink):
    def __init__(self):
        Sink.__init__(self)
        
        my_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(my_dir, "st7565/libbuff.so")
        self.libbuff = ctypes.CDLL(lib_path)
        
        self.libbuff.init()
        self.libbuff.bklt(1)
    
    def add_client(self, client):
        self.libbuff.init()
        self.libbuff.bklt(1)
        
        self.client = client
        client.parent_server = self
        
        self.notify_client_dirty()
    
    def notify_client_dirty(self):
        with self.client.buff_sem:
            self.libbuff.fling_buffer(self.client.fbuff._pixels_address)
        
        self.client.server_allows_draw()
    
    def remove_client(self, client):
        self.libbuff.deinit()
