#!/usr/bin/env python
# coding=utf-8




# class AlarmBackend:
#     def __init__(self):
#         "Load everything from the crontab and elsewhere"
#     
#     def set_alarm(self, days=[1, 2, 3, 4, 5], type="analog", hrs=0, mins=0):
#         # type = "off", "analog" or "digital"
#         if type == "digital":
#             print("Alarm: digital for days %s: %02d:%02d" % (str(days), hrs, mins))
#         else:
#             print("Alarm: %s for days %s" % (type, str(days)))
#     
#     def get_alarm(self, day):
#         # returns a one- or three-item tuple: (type, [ mins, hrs ])
#         "blah"
# 
# class TimeChooser(Client):
#     def __init__(self, graf_props, notifier=None, title="Choose time:"):
#         self.notifier = notifier
#         self.title = title
#         
#         self.hours = 7
#         self.minutes = 0
#         self.mode = 0
#         
#         self.small_font = pygame.freetype.Font("chicago.bdf")
#         self.large_font = pygame.freetype.SysFont("chicagoflf", 36)
#         self.small_font.origin = self.large_font.origin = True
#         self.small_font.antialiased = self.large_font.antialiased = False
#         
#         lg_rect = self.large_font.get_rect("12")
#         self.min_x_pos = 80 # graf_props[0] // 2
#         self.min_hour_gap = 20
#         self.y_gap = (graf_props[1] - lg_rect[1]) // 2 + 7
#         self.lg_origin = self.y_gap + lg_rect[1]
#         
#         ampm_rect = self.small_font.get_rect("am")
#         self.ampm_x = self.min_x_pos - self.min_hour_gap - lg_rect[2] - 0 - ampm_rect[2]
#         self.pm_origin = self.y_gap + 7
#         self.am_origin = self.pm_origin + 10
#         
#         Client.__init__(self, graf_props)
#     
#     def event(self, event):
#         if event == "up" or event == "down":
#             if event == "up":
#                 amt = 1
#             else:
#                 amt = -1
#             
#             if self.mode == 1:
#                 if event == "up" and self.minutes < 55:
#                     self.minutes += 5
#                 if event == "down" and self.minutes > 0:
#                     self.minutes -= 5
#             
#             if self.mode == 0:
#                 if event == "up" and self.hours < 23:
#                     self.hours += 1
#                 if event == "down" and self.hours > 0:
#                     self.hours -= 1
#             
#             self.dirty.set()
#         
#         elif event == "ok":
#             if self.mode == 0:
#                 self.mode = 1
#                 self.dirty.set()
#             elif self.mode == 1:
#                 if self.notifier != None:
#                     self.notifier(self.hours, self.minutes)
#                 Client.event(self, "back")
#         
#         elif event == "back":
#             if self.mode == 1:
#                 self.mode = 0
#                 self.dirty.set()
#             elif self.mode == 0:
#                 Client.event(self, "back")
#         
#         else:
#             Client.event(self, event)
#     
#     def draw_arrow(self, surface, x, y, s=1):
#         sz = 3
#         pygame.draw.line(surface, (0,0,0), (x-sz, y), (x, y+sz*s), 2)
#         pygame.draw.line(surface, (0,0,0), (x+sz, y), (x, y+sz*s), 2)
#     
#     def draw_frame(self, buffer, is_initial):
#         bc = (255, 255, 255)
#         tc = (0, 0, 0)
#         
#         if is_initial:
#             buffer.fill(bc)
#             
#             title = self.title.upper()
#             title_width = self.small_font.get_rect(title)[2]
#             title_pos = ((self.width - title_width) // 2, 9)
#             self.small_font.render_to(buffer, title_pos, title, fgcolor=tc, bgcolor=bc)
#             
#             pygame.draw.line(buffer, tc, (0, 10), (self.width, 10))
#         
#         else:
#             buffer.fill(bc, rect=(0, 11, self.width, self.height - 11))
#         
#         show_ampm = True
#         
#         if self.hours == 0:
#             draw_hours = "12"
#         elif self.hours <= 12:
#             draw_hours = str(self.hours)
#         elif self.hours <= 23:
#             draw_hours = str(self.hours - 12)
#         
#         draw_minutes = str(self.minutes).zfill(2)
#         
#         if show_ampm and self.hours >= 13:
#             self.small_font.render_to(buffer, (self.ampm_x, self.pm_origin), "pm", fgcolor=tc, bgcolor=bc)
#         elif show_ampm and self.hours <= 12:
#             self.small_font.render_to(buffer, (self.ampm_x, self.am_origin), "am", fgcolor=tc, bgcolor=bc)
#         
#         hour_rect = self.large_font.get_rect(draw_hours)
#         hour_pos = (self.min_x_pos - self.min_hour_gap - hour_rect[2], self.lg_origin)
#         self.large_font.render_to(buffer, hour_pos, draw_hours, fgcolor=tc, bgcolor=bc)
#         # buffer.blit(source=no, dest=(64 - no.get_width(), 20))
#         
#         min_pos = (self.min_x_pos, self.lg_origin)
#         self.large_font.render_to(buffer, min_pos, draw_minutes, fgcolor=tc, bgcolor=bc)
#         # buffer.blit(source=no, dest=(64, 20))
#         
#         if self.mode == 0:
#             if self.hours < 23:
#                 self.draw_arrow(buffer, 50, 22, -1)
#             if self.hours > 0:
#                 self.draw_arrow(buffer, 50, 54, 1)
#         elif self.mode == 1:
#             if self.minutes < 55:
#                 self.draw_arrow(buffer, 103, 22, -1)
#             if self.minutes > 0:
#                 self.draw_arrow(buffer, 103, 54, 1)
# 
# 
# class AlarmsMenu(ProtoMenu):
#     def __init__(self, graf_props):
#         spc = ""
#         day_tuples = [
#             ("every day", "Every day>","Daily alarm:"),
#             ("weekdays",  "Weekdays>", "Weekday alarm:"),
#             ("weekends",  "Weekends>", "Weekend alarm:"),
#             ("monday",    spc+"Mon>",  "Monday alarm:"),
#             ("tuesday",   spc+"Tue>",  "Tuesday alarm:"),
#             ("wednesday", spc+"Wed>",  "Wednesday alarm:"),
#             ("thursday",  spc+"Thu>",  "Thursday alarm:"),
#             ("friday",    spc+"Fri>",  "Friday alarm:"),
#             ("saturday",  spc+"Sat>",  "Saturday alarm:"),
#             ("sunday",    spc+"Sun>",  "Sunday alarm:"),
#         ]
#         
#         def create_alarmtypemenu_spawner_for_day(day):
#             def alarmtypemenu_spawner(server):
#                 server.add_client(AlarmTypeMenu(graf_props = graf_props, day = day))
#             return alarmtypemenu_spawner
#         
#         items = []
#         for day_tuple in day_tuples:
#             (day, menu_string, junk) = day_tuple
#             alarmtypemenu_spawner = create_alarmtypemenu_spawner_for_day(day)
#             items.append((menu_string, alarmtypemenu_spawner))
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = "Alarms")
# 
# 
# class AlarmTypeMenu(ProtoMenu):
#     def __init__(self, graf_props, day):
#         day_to_title_and_day_numbers = {
#             "every day": ("Daily alarm:",      range(0, 7)),
#             "weekdays":  ("Weekday alarm:",    range(0, 5)),
#             "weekends":  ("Weekend alarm:",    range(5, 7)),
#             "monday":    ("Monday alarm:",     0),
#             "tuesday":   ("Tuesday alarm:",    1),
#             "wednesday": ("Wednesday alarm:",  2),
#             "thursday":  ("Thursday alarm:",   3),
#             "friday":    ("Friday alarm:",     4),
#             "saturday":  ("Saturday alarm:",   5),
#             "sunday":    ("Sunday alarm:",     6),
#         }
#         title, day_numbers = day_to_title_and_day_numbers[day]
#         
#         items = []
#         
#         def timechooser_action(hrs, mins):
#             global_alarm_backend.set_alarm(days = day_numbers, type = "digital", hrs = hrs, mins = mins)
#         def timechooser_spawner(server):
#             timechooser = TimeChooser(graf_props=graf_props, notifier=timechooser_action, title=title)
#             server.add_client(timechooser)
#         items.append(("Set digital alarm>", timechooser_spawner))
#         
#         def use_analog_alarm(server):
#             global_alarm_backend.set_alarm(days = day_numbers, type = "analog")
#             server.remove_client(self)
#         items.append(("Use analog alarm", use_analog_alarm))
#         
#         def disable_alarm(server):
#             global_alarm_backend.set_alarm(days = day_numbers, type = "off")
#             server.remove_client(self)
#         items.append(("Disable alarm", disable_alarm))
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = title)
#     
#     def event(self, event):
#         if event == "covered":
#             self.parent_server.remove_client(self, anim_duration=0)
#         else:
#             ProtoMenu.event(self, event)




# class PlaceholderMenu(ProtoMenu):
#     def __init__(self, graf_props):
#         items = [
#             ("Sorry dude!", None),
#             ("  This is an", None),
#             ("  unimplemented", None),
#             ("  menu.     :-(", None)
#         ]
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = "Dang it!")


# class ArtistsMenu(ProtoMenu):
#     def __init__(self, graf_props):
#         artists = [None] + mpd_client.list("ARTIST")
#         items = []
#         
#         # This reminds me of the infamous RequestProcessorFactoryFactory.
#         # Did I mention that Python closures suck?
#         def create_menuspawner_for_artist(artist): # aka artist_albums_menuspawner_factory
#             def menuspawner(server): # aka artist_albums_menu_factory
#                 server.add_client(ArtistAlbumsMenu(artist=artist, graf_props=graf_props))
#             return menuspawner
#         
#         for artist in artists:
#             spawn_artist_albums_menu = create_menuspawner_for_artist(artist)
#             if artist == None: artist = "*See all albums"
#             items.append((artist + ">", spawn_artist_albums_menu))
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = "Artists")
# 
# class ArtistAlbumsMenu(ProtoMenu):
#     def __init__(self, artist, graf_props):
#         if artist == None:
#             albums = mpd_client.list("ALBUM")
#         else:
#             albums = mpd_client.list("ALBUM", artist)
#         items = []
#         
#         # always remember that what we are doing is preparing instructions to be
#         # executed when any item in this menu is selected
#         
#         def create_menuspawner_for_album(artist, album): # aka artist_albums_menuspawner_factory
#             def menuspawner(server): # aka artist_albums_menu_factory
#                 server.add_client(AlbumSongsMenu(artist=artist, album=album, graf_props=graf_props))
#             return menuspawner
#         
#         for album in albums:
#             menuspawner = create_menuspawner_for_album(artist, album)
#             items.append((album + ">", menuspawner))
#         
#         if artist == None:
#             title = "All albums"
#         else:
#             title = artist
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = title)
# 
# class AlbumSongsMenu(ProtoMenu):
#     def __init__(self, artist, album, graf_props):
#         if artist != None:
#             songs = mpd_client.find("ARTIST", artist, "ALBUM", album)
#         else:
#             songs = mpd_client.find("ALBUM", album)
#         items = []
#         
#         def create_action_for_song(file): # aka artist_albums_menuspawner_factory
#             def menuspawner(server): # aka artist_albums_menu_factory
#                 mpd_status = mpd_client.status()
#                 if int(mpd_status["playlistlength"]) > 1:
#                     # menu: now, next, add to queue (Nth)
#                     server.add_client(SongSelectedMenu(graf_props=graf_props, file=file, canqueue=True))
#                 elif mpd_status["state"] != "stop":
#                     # menu: now, next
#                     server.add_client(SongSelectedMenu(graf_props=graf_props, file=file, canqueue=True))
#                 else:
#                     # just play it
#                     id = mpd_client.addid(file)
#                     mpd_client.playid(id)
#                 
#             return menuspawner
#         
#         for song in songs:
#             menuspawner = create_action_for_song(song["file"])
#             title = song["title"]
#             items.append((title, menuspawner))
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = album)
#         
# class SongSelectedMenu(ProtoMenu):
#     def __init__(self, file, canqueue, graf_props):
#         items = []
#                 
#         # def play_next(server):
#         #     id = mpd_client.addid(file)
#         #     print mpd_client.currentsong()
#         #     server.remove_client(self)
#         # items.append(("Play next", play_next))
#         
#         if canqueue:
#             mpd_status = mpd_client.status()
#             
#             queue_pos = int(mpd_status["playlistlength"]) + 1
#             if mpd_status["playlistlength"] != "stop": queue_pos -= 1
#             
#             def queue_song(server):
#                 mpd_client.add(file)
#                 mpd_client.play()
#                 server.remove_client(self)
#             items.append(("Add to queue (#%d)" % queue_pos, queue_song))
#         
#         def play_now(server):
#             mpd_client.clear()
#             mpd_client.add(file)
#             mpd_client.play(0)
#             server.remove_client(self)
#         items.append(("Play now", play_now))
#         
#         ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = "Play song…")

# class PrettyPicture(Client):
#     def __init__(self, file, graf_props):
#         self.image = pygame.image.load(file)
#         
#         Client.__init__(self, graf_props=graf_props)
#         
#         self.dirty.set()
#     
#     def draw_frame(self, buffer, is_initial):
#         # buffer.fill((255, 255, 255))
#         # buffer.blit(pygame.transform.scale(self.image, (80, 64)), (24, 0))
#         buffer.blit(self.image, (0, 0))
#     
#     def event(self, event):
#         if event == "back":
#             self.parent_server.remove_client(self)
#             # will eventually result in an "offscreen" event
#         
#         if event == "quit" or event == "offscreen":
#             self.quit_flag = True
#             self.dirty.set()

import pygame
import bling_uikit
import menus_music
import menus_alarms
import bling_misc
import os
import sys
import mpd

class MainMenu(bling_uikit.ProtoMenu):
    def __init__(self, graf_props):
        
        items = []
        
        def spawn_playlists_menu(server): server.add_client(bling_misc.PrettyPicture("pics/glare.bmp", graf_props))
        items.append(("Picture>", spawn_playlists_menu))
        
        def spawn_artists_menu(server): server.add_client(menus_music.ArtistsMenu(graf_props))
        items.append(("Artists>", spawn_artists_menu))
        
        def spawn_alarms_menu(server): server.add_client(menus_alarms.AlarmsMenu(graf_props))
        items.append(("Alarms>", spawn_alarms_menu))
        
        bling_uikit.ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = "Main menu")
    
    def event(self, event):
        if event != "back": bling_uikit.ProtoMenu.event(self, event)



global global_alarm_backend
global_alarm_backend = menus_alarms.AlarmBackend()

if len(sys.argv) == 0:
    envt = "desktop"
else:
    envt = sys.argv[1]

    palette = tuple([(i, i, i) for i in range(0, 255)])
    graf_props = (128, 64, 8, palette)

if envt == "rpi":
    import bling_hw_pygame
    import bling_hw_st7565
    import bling_hw_terminal
    
    # Initialise pygame ourselves because ST7565 server won't (but should) do it
    # print("Initialising PyGame... video output should be pink")
    # os.putenv('SDL_VIDEODRIVER', 'fbcon') # What the fuck?
    # pygame.display.init()
    # print("PyGame version " + pygame.version.ver)
    # disp_info = pygame.display.Info()
    # screen = pygame.display.set_mode((disp_info.current_w, disp_info.current_h), pygame.FULLSCREEN)
    # screen.fill((127, 0, 127))        
    # pygame.display.update()
    
    ds = bling_hw_pygame.DesktopServer(graf_props) # to init pygame
    
    hw_server = bling_hw_st7565.ST7575Server()
    input_server = bling_hw_terminal.StdinServer()

elif envt == "desktop":
    import bling_hw_pygame
    import bling_hw_terminal
    
    hw_server = bling_hw_pygame.DesktopServer(graf_props, scale_to_size=(128*4, 64*5))
    input_server = bling_hw_terminal.StdinServer()
    

# Should defs be elsewhere
pygame.font.init()
pygame.freetype.init()

# Should probs be elsewhere
menus_music.mpd_client = mpd.MPDClient()
menus_music.mpd_client.timeout = 10
menus_music.mpd_client.idletimeout = None
menus_music.mpd_client.connect("192.168.2.120", 6600)

compositor = bling_uikit.FabCompositor(graf_props)
hw_server.add_client(compositor)
input_server.add_client(compositor)

main_menu = MainMenu(graf_props)
compositor.add_client(main_menu)
    

# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
