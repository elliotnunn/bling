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
import os.path
import ctypes

class SdlWindow:
    def __init__(self):
        display.init()
        display.set_caption(self.__class__.__name__)
        self.buff = display.set_mode((128, 64))
    
    # This is a bit of a hack, because these clearly aren't asynchronous
    def as_add_source(self, source):
        self.source = source
        source.as_set_parent(self)
    
    def as_dirty(self):
        with self.source.buff_lock:
            self.buff.blit(self.source.fbuff, (0,0))
        
        display.flip()
        
        self.source.unthrottle()


class ST7565:
    def __init__(self):
        my_dir = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(my_dir, "st7565/libbuff.so")
        self.libbuff = ctypes.CDLL(lib_path)
    
    def as_add_source(self, source):
        self.libbuff.init()
        self.libbuff.bklt(1)
        
        self.source = source
        source.as_set_parent(self)
        
        self.notify_source_dirty()
    
    def as_remove_source(self, source):
        self.source.as_set_parent(None)
        self.libbuff.deinit()
        
    def as_dirty(self):
        with self.source.buff_lock:
            self.libbuff.fling_buffer(self.source.fbuff._pixels_address)
        
        self.source.unthrottle()
