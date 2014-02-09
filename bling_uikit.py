from bling_core import *
import pygame.freetype
import time

class Compositor(Client, Server):
    def pre_frame(self): "Nothing"
    
    def draw_frame(self, buffer, is_initial):
        self.client_list_lock.acquire()
        
        self.pre_frame() # this will update the x and y coordinates in self.clients
                
        # one day this will be smarter:
        # - only drawing the topmost fullscreen window and above
        # - drawing a transformed image at the coordinates set by an animation
        # my_back_buffer.fill((255, 255, 255))
        
        first_to_draw = 0
        for i in reversed(range(0, len(self.clients))):
            client_tuple = self.clients[i]
            if client_tuple[1:3] == (0, 0):
                if client_tuple[0].width == self.width and client_tuple[0].height == self.height:
                    first_to_draw = i
                    break
        if first_to_draw < len(self.clients) - 2: print("inefficient!")
        
        for i in range(first_to_draw, len(self.clients)):
            client_tuple = self.clients[i]
            client = client_tuple[0]
            offset = client_tuple[1:3]
            
            # Client may not swap buffers while we are blitting its front buffer!
            client.buffer_lock.acquire()
            buffer.blit(client.get_buffer(True), offset)
            client.buffer_lock.release()

        self.client_list_lock.release()
        
    def add_client(self, client):
        self.client_list_lock.acquire()
        self.clients.append((client, 0, 0))
        self.client_list_lock.release()
        
        client.parent_server = self
        client.event("fully-onscreen")
        if len(clients) >= 2: clients[-2].event("covered")
        self.dirty.set()
    
    def remove_client(self, client):
        self.client_list_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients.pop(i)
                break
        self.client_list_lock.release()
        
        client.parent_server = None
        client.event("offscreen")
        self.dirty.set()
    
    def notify_client_dirty(self):
        self.dirty.set()
    
    def __init__(self, graf_props):
        self.clients = []
        self.client_list_lock = threading.RLock()
        
        Client.__init__(self, graf_props)
        Server.__init__(self)
            
    def event(self, event): # this is pretty ugly
        if event == "quit":
            self.quit_flag = True
            self.dirty.set()
            
            self.client_list_lock.acquire()
            for client_tuple in self.clients:
                client_tuple[0].event("quit")
            self.client_list_lock.release()
        else:
            self.client_list_lock.acquire()
            if len(self.clients) > 0:
                client_tuple = self.clients[-1]
                self.client_list_lock.release()
                client_tuple[0].event(event)
            else:
                self.client_list_lock.release()


class FabCompositor(Compositor):
    def pre_frame(self):
        # we reverse iterate, lest we delete the 2nd client of 3 then try to access the 3rd
        for i in reversed(range(0, len(self.clients))):
            if i > len(self.clients)-1: print("oh crap!")
            # The tuples in self.clients are of the form (client, x_pos, y_pos) by default.
            # This subclass extends them to (client, x_pos, y_pos, animation),
            # where animation = (start_time_in_s, duration_in_s, direction), and
            # direction is -1 for sliding out to the right, and 1 for sliding in from the right
            (client, x, y, animation) = self.clients[i][0:4]
            
            if animation != None:
                (start_time, duration, direction) = animation #unpack the tuple in the tuple in self.clients
                time_elapsed = time.clock() - start_time
                
                if time_elapsed >= duration: #put a stop to this animation
                    animation = None
                    if direction == -1: # this was a fuck-off animation
                        self.clients.pop(i) # DANGEROUS, and bit me on the ass!
                        client.parent_server = None
                        client.event("offscreen")
                    else: # the client remains visible once the animation ends
                        self.clients[i] = (client, 0, 0, None)
                        if len(self.clients) >= 2: self.clients[-2][0].event("covered")
                        client.event("fully-onscreen")
                        
                else:
                    progress = time_elapsed / duration * self.width
                    if direction == -1: # ie sliding out to the right
                        x = progress
                    elif direction == 1: # sliding in from the right
                        x = self.width - progress
                        
                    self.clients[i] = (client, x, 0, animation)
                    
                    self.dirty.set() # go like mad
    
    def add_client(self, client, anim_duration=0.2):
        self.client_list_lock.acquire()
        self.clients.append((client, 0, 0, (time.clock(), anim_duration, 1)))
        self.client_list_lock.release()
        
        client.parent_server = self
        self.dirty.set()
    
    def remove_client(self, client, anim_duration=0.2):
        self.client_list_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients[i] = (self.clients[i][0], 0, 0, (time.clock(), anim_duration, -1))
                break
        self.client_list_lock.release()
        
        self.dirty.set()
