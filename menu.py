#!/usr/bin/env python3
# coding=utf-8

import pygame
import bling_uikit
#import menus_music
import menus_alarms
import bling_misc
import os
import sys
#import mpd

class MainMenu(bling_uikit.SexyMenu):
    def _setup(self, graf_props, **kwargs):
        menu_items = [
            self.mkitem("Frame Timing Test", True, bling_misc.RapidFire),
            self.mkitem("Timing Precision Test", True, bling_uikit.TimeTest),
            self.mkitem("Picture", True, bling_misc.PrettyPicture, file="pics/happy_clock.BMP"),
            self.mkitem("Exception Handling Test", True, bling_misc.CrashMenu),
            self.mkitem("Alarms", True, menus_alarms.AlarmsMenu),
        ]
        
        kwargs["title"] = "Zeitgeber"
        kwargs["menu_isroot"] = True
        kwargs["menu_items"] = menu_items
        
        bling_uikit.SexyMenu._setup(self, graf_props, **kwargs)
    

menus_alarms.alarm_backend = menus_alarms.AlarmBackend()

if len(sys.argv) == 1:
    envt = "rpi"
else:
    envt = sys.argv[1]

palette = tuple([(i, i, i) for i in range(0, 255)])
graf_props = (128, 64, 8, palette)

if envt == "rpi":
    import bling_hw_st7565
    import bling_hw_terminal
    
    os.putenv("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1,1), pygame.NOFRAME)
    
    hw_server = bling_hw_st7565.ST7575Server()
    input_server = bling_hw_terminal.StdinServer()
elif envt == "desktop":
    import bling_hw_pygame
    import bling_hw_terminal
    
    pygame.init()
    
    hw_server = bling_hw_pygame.DesktopServer(graf_props, scale_to_size=(128*4, 64*5))
    input_server = bling_hw_terminal.StdinServer()

#menus_music.mpd_client = mpd.MPDClient()
#menus_music.mpd_client.timeout = 10
#menus_music.mpd_client.idletimeout = None
#menus_music.mpd_client.connect("127.0.0.1", 6600)

compositor = bling_uikit.FabCompositor(graf_props)
hw_server.add_client(compositor)
input_server.add_client(compositor)

main_menu = MainMenu(graf_props)
compositor.add_client(main_menu, anim_duration_ms=0 )
print("You should now see a UI.")

compositor.join() # block until compositor exits

hw_server.deinit()
print("I have exited cleanly.")

# Ignore the really old comment below.
# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
