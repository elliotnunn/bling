#!/usr/bin/env python2

import pygame
from bling import *
import os
import time

class MainMenu(ProtoMenu):
    def __init__(self, graf_props):
        def myfunc(server):
            print "spawning spawn"
            server.add_client(MainMenu(graf_props))
            
        items = [
            ("First option", myfunc),
            ("Second option", None),
            ("Third option", None),
            ("Fourth option", None),
            ("Fifth option", None)
        ]
        
        ProtoMenu.__init__(self, items, graf_props)



print "Initialising PyGame... video output should be pink"
os.putenv('SDL_VIDEODRIVER', 'fbcon') # What the fuck?
pygame.display.init()
disp_info = pygame.display.Info()
screen = pygame.display.set_mode((disp_info.current_w, disp_info.current_h), pygame.FULLSCREEN)
screen.fill((127, 0, 127))        
pygame.display.update()
pygame.font.init()

print "Initialising Bling!"
palette = tuple([(i, i, i) for i in range(0, 255)])

graf_props = (128, 64, 8, palette)

driver = ST7575Server()
input_server = StdinServer()
compositor = Compositor(graf_props)
input_server.add_client(compositor)
driver.add_client(compositor)

compositor.add_client(MainMenu(graf_props))

# while True:
#     for i in range(1, 9):
#         time.sleep(0.5)
#         menu.event("down")
#         #clock.dirty.set()
# 
#     for i in range(1, 9):
#         time.sleep(0.5)
#         menu.event("up")
#         #clock.dirty.set()


# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
