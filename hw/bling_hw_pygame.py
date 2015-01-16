import pygame
import bling_core
import os

class DesktopServer(bling_core.Server):
    screen = None;
    
    def __init__(self, graf_props, to_framebuffer=False, scale_to_size=None):
        bling_core.Server.__init__(self)
        
        self.scale_to_size = scale_to_size
        
        if to_framebuffer:
            os.putenv("SDL_VIDEODRIVER", "fbcon")
            screen_info = pygame.display.Info()
            screen_size = (disp_info.current_w, disp_info.current_h)
            screen_flags = pygame.FULLSCREEN
        
        else:
            os.putenv("SDL_VIDEODRIVER", "dummy")
            if scale_to_size == None:
                screen_size = graf_props[0:2]
            else:
                screen_size = scale_to_size
            screen_flags = 0 # doublebuf?
        
        self.screen = pygame.display.set_mode(screen_size, screen_flags)
        self.screen.fill((127, 0, 127))        
        pygame.display.update()
 
    def deinit(self):
        pygame.display.quit()
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
        self.notify_client_dirty()
    
    def notify_client_dirty(self):
        with self.client.buff_sem:
            surf = self.client.fbuff
            if self.scale_to_size:
                surf = pygame.transform.scale(surf, self.scale_to_size)
            self.screen.blit(surf, (0, 0))
        
        pygame.display.flip()
        self.client.server_allows_draw()
