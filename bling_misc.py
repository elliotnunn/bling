from bling_core import *
from bling_uikit import *

class Clock(Client):
    def draw_frame(self, buffer, is_initial):
        buffer.fill(self.bg)
        
        newsurf = self.font.render("FrmCt=" + str(self.count), False, self.fg, self.bg)
        buffer.blit(newsurf, (2, 2))
        
        self.count += 1
    
    def __init__(self, graf_props):
        Client.__init__(self, graf_props)
        
        self.count = 0
        self.font = pygame.font.SysFont("chicagoflf", 12)
        
        self.bg = (0, 0, 0); self.fg = (255, 255, 255);
        
        self.dirty.set()
    
    def event(self, event):
        if event == "quit":
            self.quit_flag = True
            self.dirty.set()


class PlaceholderMenu(ProtoMenu):
    def __init__(self, graf_props):
        items = [
            ("Sorry dude!", None),
            ("  This is an", None),
            ("  unimplemented", None),
            ("  menu.     :-(", None)
        ]
        
        ProtoMenu.__init__(self, graf_props = graf_props, items = items, title = "Dang it!")


class PrettyPicture(Client):
    def __init__(self, file, graf_props):
        self.image = pygame.image.load(file)
        
        Client.__init__(self, graf_props=graf_props)
        
        self.dirty.set()
    
    def draw_frame(self, buffer, is_initial):
        # buffer.fill((255, 255, 255))
        # buffer.blit(pygame.transform.scale(self.image, (80, 64)), (24, 0))
        buffer.blit(self.image, (0, 0))
    
    def event(self, event):
        if event == "back":
            self.parent_server.remove_client(self)
            # will eventually result in an "offscreen" event
        
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            self.dirty.set()