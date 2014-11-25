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

class MainMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        
        items = []
        
        def spawn_rapidfire(server): server.add_client(bling_misc.RapidFire(graf_props))
        items.append(("RapidFire>", spawn_rapidfire))
        
        def spawn_picture_menu(server): server.add_client(bling_misc.PrettyPicture(graf_props, file="pics/happy_clock.BMP"))
        items.append(("Picture>", spawn_picture_menu))
        
        def spawn_crash_menu(server): server.add_client(bling_misc.CrashMenu(graf_props))
        items.append(("Crash>", spawn_crash_menu))
        
        #def spawn_artists_menu(server): server.add_client(menus_music.ArtistsMenu(graf_props))
        #items.append(("Artists>", spawn_artists_menu))
        
        def spawn_alarms_menu(server): server.add_client(menus_alarms.AlarmsMenu(graf_props))
        items.append(("Alarms>", spawn_alarms_menu))
        
        def spawn_tt(server): server.add_client(bling_uikit.TimeTest(graf_props))
        items.append(("Time test>", spawn_tt))
        
        def spawn_sexy_menu(server): server.add_client(bling_uikit.SexyMenu(graf_props))
        items.append(("SexyMenu>", spawn_sexy_menu))

        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Zeitgeber")
    
    #def _event(self, event):
        #print(event)
        #if event != "back": return bling_uikit.ProtoMenu._event(self, event)


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
