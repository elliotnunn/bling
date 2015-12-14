#!/usr/bin/python3

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
from plumbing import StackCompositor, StripCompositor, SdlWindow
from inputs import SdlInput
from switches import ClockSwitches
from ui import SexyMenu

import os
try:
    if os.environ['SDL_VIDEODRIVER'] != 'st7565shim':
        raise KeyError
except KeyError:
    pass
else:
    import st7565


class MainMenu(SexyMenu):
    def __init__(self, **kwargs):
        mni = [
            self.itm("The quick1", True, MainMenu),
            self.itm("The quick2", True, MainMenu),
            self.itm("The quick3", True, MainMenu),
            self.itm("The quick4", True, MainMenu),
            self.itm("The quick5", True, MainMenu),
            self.itm("The quick6", True, MainMenu),
            self.itm("The quick7", True, MainMenu),
            self.itm("The quick8", True, MainMenu),
        ]
        
        SexyMenu.__init__(self, title="Zeitgeber", menu_isroot=True, menu_items=mni, **kwargs)


out = SdlWindow()
#inp = SdlInput()
inp = ClockSwitches()

comp = StackCompositor()

m = MainMenu()

out.as_add_source(comp)
inp.as_set_source(comp)

comp.as_push(m)

print("Main thread exits.")
import time
while 1: time.sleep(3600)