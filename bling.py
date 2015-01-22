#!/usr/bin/env python3

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
import pygame.freetype
# Submodules init'ed before gui/*.py is called:
# display, freetype

import os
import sys
from importlib import import_module


#
# Set up imports so that all modules can import from the root
#
bling_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, bling_root)


#
# Parse options (which thankfully are actually optional)
#
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog [--gui=<gui>] [--hw=<hw> ...]",
                      version="bling, not finished yet")
parser.add_option("--gui", action="store",  type="string", dest="gui",
                  help="GUI to show (gui/*.py), e.g. clock")
parser.add_option("--hw",  action="append", type="string", dest="hw",
                  help="import driver (module.class), e.g. st7565.ST7565")

(options, args) = parser.parse_args()

if len(args) > 0:
    parser.error("Error: too many arguments")
    exit(1)


#
# Get a list of Sink classes and initialise them
#
hw = options.hw or ["st7565.ST7565", "terminal.TermIn"]

sinks = []
for hw_name in hw:
    parts = ["hw"] + hw_name.split(".")
    
    hw_modname = ".".join(parts[:-1])
    hw_classname = parts[-1]
    
    mod = import_module(hw_modname)
    cls = getattr(mod, hw_classname)
    
    sink = cls()
    sinks.append(sink)

# We need to initialise a display, so if none of our sinks have done it...
if not pygame.display.get_init():
    os.putenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    pygame.display.set_mode((1, 1))

# And we always need freetype
pygame.freetype.init()


#
# Get our "orchestrator" ready to go
#
gui = options.gui or "debug"
gui_module = import_module("gui." + gui)


#
# Go
#
gui_module.go(sinks)

pygame.quit()
