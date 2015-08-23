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


from ui import SexyMenu
from plumbing import Compositor
from inputs import SdlInput
from outputs import SdlWindow


class MainMenu(SexyMenu):
    def _setup(self, **kwargs):
        mni = [
            self.itm("First positional argument of print", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Back1", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
            self.itm("Back 2", True, print, "First positional argument of print!"),
        ]
        
        SexyMenu._setup(self, title="Zeitgeber", menu_isroot=True, menu_items=mni, **kwargs)


out = SdlWindow()
inp = SdlInput()

comp = Compositor()

m = MainMenu()

out.as_add_source(comp)
inp.as_add_source(comp)

comp.as_add_source(m)

print("Main thread exits.")
import time
time.sleep(100)