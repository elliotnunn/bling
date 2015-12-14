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

from plumbing import SexySource
from ui import typeset
import pygame

class WhatsThisThenSlut(SexySource):
    def __init__(self, **kwargs):
        self.placard = None
        self.pw = self._get_size()[0]
        
        super(WhatsThisThenSlut, self).__init__(**kwargs)
    
    def _draw_frame(self, buff):
        if True: #not self.placard:
            text = "Ever wondered what it’s like to have sex with Justin Bieber after a long night of hookers and weed? Me neither. https://youtu.be/DK_0jXPuIr0 ff"
            
            pygame.freetype.init()
            font = pygame.freetype.Font("Chicago-12.bdf")
            font.origin = True
            
            self.placard = typeset(text, font, self.pw)
        
        buff.fill((0,)*3)
        
        buff.blit(self.placard, (0,0))
        
        print(self.pw)
        self.pw -= 1
        return self.t + 50

# typeset(self, text, font, width=128, bg=(255,)*3, fg=(0,)*3, spacing=1)