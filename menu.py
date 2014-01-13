#!/usr/bin/env python2

import pygame
from bling import *
import os
import time


print "Initialising PyGame... video output should be pink"
os.putenv('SDL_VIDEODRIVER', 'fbcon') # What the fuck?
pygame.display.init()
screen = pygame.display.set_mode((pygame.display.Info().current_w, pygame.display.Info().current_h), pygame.FULLSCREEN)
screen.fill((127, 0, 127))        
pygame.display.update()
pygame.font.init()

print "Initialising Bling!"
palette = tuple([(i, i, i) for i in range(0, 255)])
driver = ST7575Server()
compositor = Compositor(width = 132, height = 64, depth = 8, palette = palette)
driver.add_client(compositor)
clock = ProtoMenu(width = 132, height = 64, depth = 8, palette = palette)
compositor.add_client(clock)
time.sleep(0.5)
# threads should not be daemonised, but that means that I need a working event-passing system!
while True:
    for i in range(1, 9):
        clock.event("down")
        time.sleep(0.5)

    for i in range(1, 9):
        clock.event("up")
        time.sleep(0.5)

print 'Deinitialising driver'
driver.deinit()

# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
