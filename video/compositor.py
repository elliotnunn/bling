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


import pygame
from video.sink import Sink
from video.source import Source

import time
import threading


class Compositor(Sink, Source):
    def pre_frame(self): pass
    
    def _draw_frame(self, buffer, is_initial):
        self.client_list_lock.acquire()
        nxt = self.pre_frame() # this will update the x and y coordinates in self.clients
                
        # one day this will be smarter:
        # - only drawing the topmost fullscreen window and above
        # - drawing a transformed image at the coordinates set by an animation
        # my_back_buffer.fill((255, 255, 255))
        
        # Ignore the above. It is now smarter.
        
        client_count = len(self.clients)
        topmost_obscurer = 0
        # NOCOPY HACK [also check bling_core.Client.run()]
        #self.skip_offering_buffer = False
        
        for i in reversed(range(0, client_count)):
            client_tuple = self.clients[i]
            xy_min = client_tuple[1:3]
            if xy_min <= (0,0):
                xy_max = (client_tuple[0].width, client_tuple[0].height) + xy_min
                if xy_max >= (self.width, self.height):
                    topmost_obscurer = i
                    break
        
        for i in range(0, client_count):
            client_tuple = self.clients[i]
            client = client_tuple[0]
            
            # NOCOPY HACK: ugly, and doesn't actually make anything faster
            # Requires that parent_server only ever ask for a frame async.
            # If reenabling then change the below if to elif.
            #if topmost_obscurer == client_count-1 == i:
                ##print("Decided")
                #self.buff_sem.acquire()
                #client.buff_sem.acquire()
                #(save_fbuff, self.fbuff) = (self.fbuff, client.fbuff)
                #self.buff_sem.release()
                ##print("Got buffers")
                
                ##print("Notifying server")
                #self.parent_server.notify_client_dirty()
                #self.sync_sem.acquire() # wait for server to consent but
                #self.sync_sem.release() # don't snag again before next frame
                ##print("Server acknowledged")
                
                #self.buff_sem.acquire()
                #self.fbuff = save_fbuff
                #client.buff_sem.release()
                #self.buff_sem.release()
                ##print("Put buffers back")
                
                #self.skip_offering_buffer = True
            
            # Composite this buffer onto the back buffer
            if i >= topmost_obscurer:
                client.buff_sem.acquire()
                buffer.blit(client.fbuff, client_tuple[1:3])
                client.buff_sem.release()
            
            # Regardless of whether it is in view
            client.server_allows_draw()
        
        self.client_list_lock.release()
        
        if nxt: return self.t
        else: return None
    
    # Should actually remove the following two methods; ugly duplication of FabCompositor
    def add_client(self, client, **kwargs):
        self.client_list_lock.acquire()
        self.clients.append((client, 0, 0))
        self.client_list_lock.release()
        
        client.parent_server = self
        client.event("fully-onscreen")
        if len(clients) >= 2: clients[-2].event("covered")
        
        try: self.evt_sem.release()
        except: pass
    
    def remove_client(self, client, **kwargs):
        self.client_list_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients.pop(i)
                break
        self.client_list_lock.release()
        
        client.parent_server = None
        client.event("offscreen")
        
        try: self.evt_sem.release()
        except: pass
    
    def notify_client_dirty(self):
        try: self.evt_sem.release()
        except: pass
    
    def __init__(self, graf_props):
        Source.__init__(self, graf_props)
        Sink.__init__(self)
    
    def _setup(self, graf_props):
        self.clients = []
        self.client_list_lock = threading.Lock()

    
    def _event(self, event): # this is pretty ugly
        if event == "quit":
            self.client_list_lock.acquire()
            for client_tuple in self.clients:
                client_tuple[0].event("quit")
            self.client_list_lock.release()
            
            self.parent_server and self.parent_server.remove_client(self)
            
            self.quit_flag = True
            return True
            
        elif event == "screenshot":
            filename = "screenshot/bling @ %s.png" % time.ctime()
            self.buffer_lock.acquire()
            pygame.image.save(self.get_buffer(True), filename)
            self.buffer_lock.release()
            
            return False
            
        else:
            self.client_list_lock.acquire()
            if len(self.clients) > 0:
                client_tuple = self.clients[-1]
                self.client_list_lock.release()
                client_tuple[0].event(event)
            else:
                self.client_list_lock.release()
            
            return False


class FabCompositor(Compositor):
    def pre_frame(self):
        # we reverse iterate, lest we delete the 2nd client of 3 then try to access the 3rd
        animating = False
        for i in reversed(range(0, len(self.clients))):
            if i > len(self.clients)-1: print("oh crap!")
            # The tuples in self.clients are of the form (client, x_pos, y_pos) by default.
            # This subclass extends them to (client, x_pos, y_pos, animation),
            # where animation = (start_time_in_ms, duration_in_ms, direction), and
            # direction is -1 for sliding out to the right, and 1 for sliding in from the right
            (client, x, y, animation) = self.clients[i][0:4]
            
            if animation != None:
                (start_time_ms, duration_ms, direction) = animation #unpack the tuple in the tuple in self.clients
                time_elapsed_ms = pygame.time.get_ticks() - start_time_ms
                
                if time_elapsed_ms >= duration_ms: #put a stop to this animation
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
                    progress = time_elapsed_ms / duration_ms * self.width
                    if direction == -1: # ie sliding out to the right
                        x = progress
                    elif direction == 1: # sliding in from the right
                        x = self.width - progress
                        
                    self.clients[i] = (client, x, 0, animation)
                    
                    animating = True
        
        return animating
    
    def add_client(self, client, anim_duration_ms=200):
        self.client_list_lock.acquire()
        self.clients.append((client, 0, 0, (pygame.time.get_ticks(), anim_duration_ms, 1)))
        self.client_list_lock.release()
        
        client.parent_server = self
        
        try: self.evt_sem.release()
        except: pass
    
    def remove_client(self, client, anim_duration_ms=200):
        self.client_list_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients[i] = (self.clients[i][0], 0, 0, (pygame.time.get_ticks(), anim_duration_ms, -1))
                break
        self.client_list_lock.release()
        
        try: self.evt_sem.release()
        except: pass
