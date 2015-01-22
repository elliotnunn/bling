from video.compositor import FabCompositor
from kit.menu import SexyMenu

#class DiagnosticsMenu(SexyMenu):
    #def _setup(self, graf_props, **kwargs):
        #menu_items = [
            #self.mkitem("Frame timing", True, bling_misc.RapidFire),
            #self.mkitem("Exception handling", True, bling_misc.CrashMenu),
            #self.mkitem("Pygame time", True, bling_uikit.TimeTest),
        #]
        
        #kwargs["title"] = "Diagnostics"
        #kwargs["menu_items"] = menu_items
        
        #bling_uikit.SexyMenu._setup(self, graf_props, **kwargs)

class MainMenu(SexyMenu):
    def _setup(self, graf_props, **kwargs):
        menu_items = [
            self.itm("Music", True, MainMenu),
            self.itm("Alarm settings", True, print, "First positional argument of print!"),
            self.itm("About", True, print, "First positional argument of print!"),
            self.itm("Backlight", True, print, "First positional argument of print!"),
            self.itm("Backlight", True, print, "First positional argument of print!"),
        ]
        
        kwargs["title"] = "Zeitgeber"
        kwargs["menu_isroot"] = True
        kwargs["menu_items"] = menu_items
        
        SexyMenu._setup(self, graf_props, **kwargs)


def go(sinks):
    # Get rid of this c-r-a-p as soon as possible
    palette = tuple([(i, i, i) for i in range(0, 255)])
    graf_props = (128, 64, 8, palette)
    
    compositor = FabCompositor(graf_props)
    for sink in sinks:
        sink.add_client(compositor)
    
    main_menu = MainMenu(graf_props)
    compositor.add_client(main_menu, anim_duration_ms=0)
    
    compositor.join()
