import pygame
import bling_core
import bling_uikit

class Clock(bling_core.Client):
    def _setup(self, graf_props):
        self.count = 0
        self.font = pygame.font.SysFont("chicagoflf", 12)
        
        self.bg = (0, 0, 0); self.fg = (255, 255, 255);
        
        self.dirty.set()
    
    def _draw_frame(self, buffer, is_initial):
        buffer.fill(self.bg)
        
        newsurf = self.font.render("FrmCt=" + str(self.count), False, self.fg, self.bg)
        buffer.blit(newsurf, (2, 2))
        
        self.count += 1


class PlaceholderMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        items = [
            ("Sorry dude!", None),
            ("  This is an", None),
            ("  unimplemented", None),
            ("  menu.     :-(", None)
        ]
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Dang it!")

class CrashMenu(bling_uikit.ProtoMenu):
    def _setup(self, graf_props):
        def create_spawner(crash_at):
            def menuspawner(server):
                server.add_client(CrashyException(graf_props, crash_at=crash_at))
            return menuspawner

        items = []
        for x in ["_setup", "_event", "_draw_frame"]:
            items.append((x, create_spawner(x)))
        
        bling_uikit.ProtoMenu._setup(self, graf_props, items=items, title="Crash where?")

class CrashyException(bling_core.Client):
    def _setup(self, graf_props, crash_at="_setup"):
        self.crash_at = crash_at
        
        if self.crash_at == "_setup":
            self.__spit_dummy()
    
    def _event(self, event):
        if self.crash_at == "_event":
            self.__spit_dummy()
    
    def _draw_frame(self, buffer, is_initial):
        if self.crash_at == "_draw_frame":
            self.__spit_dummy()
    
    def __spit_dummy(self):
        1 / 0

class PrettyPicture(bling_core.Client):
    def _setup(self, graf_props, **kwargs):
        self.image = pygame.image.load(kwargs["file"])
    
    def _draw_frame(self, buffer, is_initial):
        # buffer.fill((255, 255, 255))
        # buffer.blit(pygame.transform.scale(self.image, (80, 64)), (24, 0))
        buffer.blit(self.image, (0, 0))
