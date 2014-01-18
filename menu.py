#!/usr/bin/env python2

import pygame
from bling import *
import os
import time
import mpd

class MainMenu(ProtoMenu):
    def __init__(self, graf_props):
        
        items = []
        
        def spawn_playlists_menu(server): server.add_client(PlaceholderMenu(graf_props))
        items.append(("Playlists>", spawn_playlists_menu))
        
        def spawn_artists_menu(server): server.add_client(ArtistsMenu(graf_props))
        items.append(("Artists>", spawn_artists_menu))
        
        def spawn_streams_menu(server): server.add_client(PlaceholderMenu(graf_props))
        items.append(("Streams>", spawn_streams_menu))
        
        def spawn_alarms_menu(server): server.add_client(PlaceholderMenu(graf_props))
        items.append(("Alarms>", spawn_alarms_menu))
        
        def spawn_settings_menu(server): server.add_client(PlaceholderMenu(graf_props))
        items.append(("Settings>", spawn_settings_menu))
        
        ProtoMenu.__init__(self, graf_props = graf_props, items = items)

class PlaceholderMenu(ProtoMenu):
    def __init__(self, graf_props):
        items = [
            ("Sorry dude!", None),
            ("  This is an", None),
            ("  unimplemented", None),
            ("  menu.     :-(", None)
        ]
        
        ProtoMenu.__init__(self, graf_props = graf_props, items = items)

#closures in Python are an absolute fucking joke!

class ArtistsMenu(ProtoMenu):
    def __init__(self, graf_props):
        artists = [None] + mpd_client.list("ARTIST")
        items = []
        
        # This reminds me of the infamous RequestProcessorFactoryFactory.
        # Did I mention that Python closures suck?
        def create_menuspawner_for_artist(artist): # aka artist_albums_menuspawner_factory
            def menuspawner(server): # aka artist_albums_menu_factory
                server.add_client(ArtistAlbumsMenu(artist=artist, graf_props=graf_props))
            return menuspawner
        
        for artist in artists:
            spawn_artist_albums_menu = create_menuspawner_for_artist(artist)
            if artist == None: artist = "*See all albums"
            items.append((artist + ">", spawn_artist_albums_menu))
        
        ProtoMenu.__init__(self, graf_props = graf_props, items = items)

class ArtistAlbumsMenu(ProtoMenu):
    def __init__(self, artist, graf_props):
        if artist == None:
            albums = mpd_client.list("ALBUM")
        else:
            albums = mpd_client.list("ALBUM", artist)
        items = []
        
        # always remember that what we are doing is preparing instructions to be
        # executed when any item in this menu is selected
        
        def create_menuspawner_for_album(artist, album): # aka artist_albums_menuspawner_factory
            def menuspawner(server): # aka artist_albums_menu_factory
                server.add_client(AlbumSongsMenu(artist=artist, album=album, graf_props=graf_props))
            return menuspawner
        
        for album in albums:
            menuspawner = create_menuspawner_for_album(artist, album)
            items.append((album + ">", menuspawner))
        
        ProtoMenu.__init__(self, graf_props = graf_props, items = items)

class AlbumSongsMenu(ProtoMenu):
    def __init__(self, artist, album, graf_props):
        songs = mpd_client.find("ARTIST", artist, "ALBUM", album)
        items = []
        
        def create_menuspawner_for_song(file): # aka artist_albums_menuspawner_factory
            def menuspawner(server): # aka artist_albums_menu_factory
                server.add_client(PlaceholderMenu(graf_props=graf_props))
            return menuspawner
        
        for song in songs:
            menuspawner = create_menuspawner_for_song(song["file"])
            title = song["title"]
            items.append((title, menuspawner))
        
        ProtoMenu.__init__(self, graf_props = graf_props, items = items)
        


print "Initialising PyGame... video output should be pink"
os.putenv('SDL_VIDEODRIVER', 'fbcon') # What the fuck?
pygame.display.init()
disp_info = pygame.display.Info()
screen = pygame.display.set_mode((disp_info.current_w, disp_info.current_h), pygame.FULLSCREEN)
screen.fill((127, 0, 127))        
pygame.display.update()
pygame.font.init()

print "Chooking up mpd"
global mpd_client
mpd_client = mpd.MPDClient()
mpd_client.timeout = 10
mpd_client.idletimeout = None
mpd_client.connect("localhost", 6600)

print "Putting on Bling!"
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
