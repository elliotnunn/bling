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
import ctypes
import numpy as np
import os
import time

SCR_W = 128
SCR_H = 64
SKIPCOL = 4
PAGES = SCR_H / 8

SPI_FLAGS = [0b11000000, 0b11000100] # flip the SS line
SPI_BAUD = 10000000

cmd = lambda page: [(7-page) | 0xb0, (SKIPCOL >> 4) | 0x10, SKIPCOL & 0x0f]
PAGE_CMDS = np.array([cmd(page) for page in range(8)], dtype=np.uint8)

GPIO_RST = 25


class FakeSurface:
    def blit(self, surf, *args, **kwargs):
        array = pygame.surfarray.pixels2d(surf)
        
        for page in range(8):
            packed = np.packbits(array[:, page*8:page*8+8])
            
            pigpio.spiWrite(spi_if[0], PAGE_CMDS[page].ctypes.data, 3)
            pigpio.spiWrite(spi_if[1], packed.ctypes.data, packed.size)

def patched_set_mode(res, *args, **kwargs):
    if res != (128, 64):
        raise RuntimeError('Cannot set this resolution using the shim.')
    
    old_set_mode((1,1), *args, **kwargs)
    return fake_surface

def patched_flip(): pass


# For when pygame gets init'ed
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# This needs to be called from out patched function
old_set_mode = pygame.display.set_mode

fake_surface = FakeSurface()
pygame.display.set_mode = patched_set_mode
pygame.display.flip     = patched_flip


pigpio = ctypes.cdll.LoadLibrary("libpigpio.so")
pigpio.gpioInitialise()

pigpio.gpioSetMode(GPIO_RST, 1)

spi_if = [pigpio.spiOpen(0, SPI_BAUD, f) for f in SPI_FLAGS]

def cmd_byte(byte):
    pigpio.spiWrite(spi_if[0], ctypes.byref(ctypes.c_uint8(byte)), 1)

for l in [0, 1]:
    pigpio.gpioWrite(GPIO_RST, l)
    time.sleep(0.1)

cmd_byte(0xe2) # 14. reset, not inc memory or LCD power              */
cmd_byte(0xaf) #  1. display on (0xaf) or off (0xae)                 */
cmd_byte(0x40) #  2. first display line (0x40 | 6 bits)              */
cmd_byte(0xa1) #  8. LCD scan normal (0xa0) or reverse (0xa1)        */
cmd_byte(0xa7) #  9. normal 1=white (0xa7) or reverse 1=black (0xa6) */
cmd_byte(0xa4) # 10. every pixel black (0xa5) or not (0xa4)          */
cmd_byte(0xa3) # 11. LCD voltage bias 1/9 (0xa2) or 1/7 (0xa3)       */

cmd_byte(0xc8) # 15. LCD scan downwards (0xc0) or upwards (0xc8)     */
cmd_byte(0x2f) # 16. internal power supply mode:
#                       0x28 | 0x04 (internal voltage converter circuit)
#                            | 0x02 (internal voltage regulator circuit)
#                            | 0x01 (internal voltage follower circuit)     */
cmd_byte(0x22) # 17. resistor ratio:
#                           0x20 | (3 bits) such that (1 + Rb/Ra) =
#                           3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.4          */
cmd_byte(0x81) # 18. reference voltage (2 byte command)              */
cmd_byte(45)   #     low contrast (0) to high contrast (63)          */
