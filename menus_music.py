import bling_uikit

global mpd_client

class ArtistsMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        artists = [None] + mpd_client.list("ARTIST")
        print(str(len(artists)))
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
        
        ProtoMenu._setup(self, graf_props, items=items, title="Artists")

class ArtistAlbumsMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props, artist=None):
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
        
        if artist == None:
            title = "All albums"
        else:
            title = artist
        
        ProtoMenu._setup(self, graf_props, items=items, title=title)

class AlbumSongsMenu(bling_uikit.ProtoMenu):
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
        
        ProtoMenu._setup(self, graf_props, items=items, title=album)
        
class SongSelectedMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props, canqueue=False, file=None):
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
        
        ProtoMenu._setup(self, graf_props, items=items, title="Play song…")
