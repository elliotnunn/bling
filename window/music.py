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

import bling_uikit

global mpd_client

class ArtistsMenu(bling_uikit.SexyMenu):
    def _setup(self, graf_props, **kwargs):
        menu_items = []
        
        for artist in [None] + mpd_client.list("ARTIST"):
            str = artist
            if str == None: str = "(All)"
            
            menu_items.append(self.mkitem(str, True, AlbumsMenu, artist=artist))
        
        kwargs["title"] = "Artists"
        kwargs["menu_items"] = menu_items
        
        bling_uikit.SexyMenu._setup(self, graf_props, **kwargs)

class AlbumsMenu(bling_uikit.SexyMenu):
    def _setup(self, graf_props, artist=None, **kwargs):
        if artist == None:
            albums = mpd_client.list("ALBUM")
        else:
            albums = mpd_client.list("ALBUM", artist)
        
        menu_items = []
        
        for album in albums:
            menu_items.append(self.mkitem(album, True, SongsMenu, artist=artist, album=album))
        
        kwargs["title"] = artist
        kwargs["menu_items"] = menu_items
        
        bling_uikit.SexyMenu._setup(self, graf_props, **kwargs)
        
class SongsMenu(bling_uikit.SexyMenu):
    def _setup(self, graf_props, artist=None, album=None, **kwargs):
        if artist != None:
            songs = mpd_client.find("ARTIST", artist, "ALBUM", album)
        else:
            songs = mpd_client.find("ALBUM", album)
        
        menu_items = []
        
        menu_items = [self.mkitem(song["title"], True, PlayMenuX, path=song["file"]) for song in songs]
        
        kwargs["title"] = album
        kwargs["menu_items"] = menu_items
        
        bling_uikit.SexyMenu._setup(self, graf_props, **kwargs)

class SongsMenuX(bling_uikit.ProtoMenu):
    def _setup(self, graf_props, artist=None, album=None):
        if artist != None:
            songs = mpd_client.find("ARTIST", artist, "ALBUM", album)
        else:
            songs = mpd_client.find("ALBUM", album)
        items = []
        
        def create_action_for_song(file): # aka artist_albums_menuspawner_factory
            def menuspawner(server): # aka artist_albums_menu_factory
                mpd_status = mpd_client.status()
                if int(mpd_status["playlistlength"]) > 1:
                    # menu: now, next, add to queue (Nth)
                    server.add_client(SongSelectedMenu(graf_props=graf_props, file=file, canqueue=True))
                elif mpd_status["state"] != "stop":
                    # menu: now, next
                    server.add_client(SongSelectedMenu(graf_props=graf_props, file=file, canqueue=True))
                else:
                    # just play it
                    id = mpd_client.addid(file)
                    mpd_client.playid(id)
                
            return menuspawner
        
        for song in songs:
            menuspawner = create_action_for_song(song["file"])
            title = song["title"]
            items.append((title, menuspawner))
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title=album)

class PlayMenu(bling_uikit.SexyMenu):
    def _setup(self, graf_props, file=None, **kwargs):
        mpd_status = mpd_client.status()

        queue_pos = int(mpd_status["playlistlength"])
        mpd_state = mpd_status["state"] != "stop"
        
        menu_items = []

        def play_next():
            mpd_client.addid(file, 0)

        #menu_items.append(self.mkitem("Play next", False, play_next))

        if queue_pos > 1 or mpd_state != "stop":
            if mpd_state == "stop": queue_pos += 1
            
            def enqueue():
                mpd_client.add(file)
                mpd_client.play()

            menu_items.append(self.mkitem("Enqueue (#%d)" % queue_pos, False, enqueue))
        
        def play_now():
            mpd_client.clear()
            mpd_client.add(file)
            mpd_client.play(0)

        menu_items.append(self.mkitem("Play now", False, play_now))
                
        kwargs["title"] = "Play song..."
        kwargs["menu_items"] = menu_items
        
        bling_uikit.SexyMenu._setup(self, graf_props, **kwargs)

class PlayMenuX(bling_uikit.ProtoMenu):
    def _setup(self, graf_props, canqueue=True, path=None):
        file = path
        items = []
                
        # def play_next(server):
        #     id = mpd_client.addid(file)
        #     print mpd_client.currentsong()
        #     server.remove_client(self)
        # items.append(("Play next", play_next))
        
        if canqueue:
            mpd_status = mpd_client.status()
            
            queue_pos = int(mpd_status["playlistlength"]) + 1
            if mpd_status["playlistlength"] != "stop": queue_pos -= 1
            
            def queue_song(server):
                mpd_client.add(file)
                mpd_client.play()
                server.remove_client(self)
            items.append(("Add to queue (#%d)" % queue_pos, queue_song))
        
        def play_now(server):
            mpd_client.clear()
            mpd_client.add(file)
            mpd_client.play(0)
            server.remove_client(self)
        items.append(("Play now", play_now))
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Play song…")
