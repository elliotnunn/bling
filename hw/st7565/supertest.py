#!/usr/bin/env python3

# this is supertest

import pygame
import bling_hw_st7565
import time
import os
import ctypes

# ugly pygame stuff
os.putenv("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.display.set_mode((1,1), pygame.NOFRAME)

libbuff = ctypes.CDLL('buff/libbuff.so')

# painful contortions to get an 8-bit surface
surf = pygame.image.load ("supertest-image.png").convert (8)
palette = tuple([(i, i, i) for i in range(0, 255)])
surf2 = pygame.Surface ((128, 64), depth=8)
surf2.set_palette (palette)
surf2.blit (surf, (0, 0))

print("Waiting before init'ing")
time.sleep(1.5)

print("NOW")
libbuff.init()

time.sleep(1.0)
print("Waiting before showing frame")
time.sleep(1.5)

print("NOW")
libbuff.fling_buffer(surf2._pixels_address)

time.sleep(1.0)
print("Waiting before deinit")
time.sleep(1.5)

print("NOW")
libbuff.deinit()
