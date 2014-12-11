import bling_core
import bling_widgets
import pygame
import pygame.freetype
import time
import sys
import threading

class Compositor(bling_core.Client, bling_core.Server):
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
        bling_core.Client.__init__(self, graf_props)
        bling_core.Server.__init__(self)
    
    def _setup(self, graf_props):
        self.clients = []
        self.client_list_lock = threading.Lock()

    
    def _event(self, event): # this is pretty ugly
        if event == "quit":
            self.client_list_lock.acquire()
            for client_tuple in self.clients:
                client_tuple[0].event("quit")
            self.client_list_lock.release()
            
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
                        
                    self.clients[i] = (client, x, x/5, animation)
                    
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


class TimeTest(bling_core.Client):
    def _setup(self, graf_props):
        self.font = pygame.freetype.Font("chicago.bdf")
    
    def _draw_frame(self, buffer=None, is_initial=False):
        buffer.fill((255,255,255), (0,0,self.width,self.height))
        
        self.font.render_to(buffer, (0,0), "t = %dms"%pygame.time.get_ticks())
        
        return self.t + 500


class SexyMenu(bling_core.Client):
    def _setup(self, graf_props, title="SexyMenu", items=["The quick brown fox jumps over the lazy dog"]*3+["aaa","bbb","ggg"]):
        self.font = pygame.freetype.Font("chicago.bdf")
        self.font.origin = True
        
        self.tb = bling_widgets.TextBox
        
        self.title = title
        self.items = items
        self.item_widgets = [None]*4
        for i in range(0,4):
            self.item_widgets[i] = self.tb()
            self.__setup_widget(i)
        
        self.selection = 0
        self.scroll = 0
        
        self.lock = threading.Lock()
    
    def __setup_widget(self, i):
        w = self.item_widgets[i % 4]
        w.set_content(self.items[i], self.font, 0, (self.width, 13))
    
    def __reselect(self, by):
        with self.lock:
            self.selection += by
            self.selection = min(self.selection, len(self.items)-1)
            self.selection = max(self.selection, 0)
            
            if self.selection < self.scroll:
                self.__scroll(-1)
            elif self.selection >= self.scroll + 4:
                self.__scroll(1)
    
    def __scroll(self, by):
        if by == -1 and self.scroll > 0:
            self.scroll += by
            self.__setup_widget(self.scroll)
        elif by == 1 and self.scroll + 4 < len(self.items):
            self.scroll += by
            self.__setup_widget(self.scroll + 3)
    
    
    # This just straightforwardly wraps a few widgets
    def _draw_frame(self, buffer, is_initial):
        if is_initial:
            buffer.fill((255,255,255), (0, 0,  self.width, 12))
            
            w = bling_widgets.TextBox()
            w.set_content(self.title.upper(), self.font, 0, (self.width, 13))
            w.set_oflow(self.tb.OFLOW_ELLIPSIS)
            
            if w.ellipsis_x == 0:
                x = (self.width - w.text_full_w) // 2
            else:
                x = 0
            
            w.draw(buffer, (x, -1), 0)
            
            buffer.fill((0,0,0), (0, 10, self.width, 1))
        
        with self.lock:
            low_end = max(self.scroll + 4, len(self.item_widgets))
            for i in range(self.scroll, low_end):
                widget = self.item_widgets[i % 4]
                
                if i == self.selection:
                    widget.set_hilite(True)
                    widget.set_oflow(self.tb.OFLOW_SCROLL, self.t)
                else:
                    widget.set_hilite(False)
                    widget.set_oflow(self.tb.OFLOW_ELLIPSIS)
                
                widget.draw(buffer, (0, 12+13*(i-self.scroll)), self.t)
        
        return None
    
    def _event(self, event):
        if event == "up":
            self.__reselect(-1)
        elif event == "down":
            self.__reselect(1)
        else:
            return None
        return True

class ProtoMenu(bling_core.Client): # a bit of a mess, and poorly optimised
    def _draw_frame(self, buffer, is_initial):
        blk = (0, 0, 0)
        wht = (255, 255, 255)
        blk = (127, 127, 127)
        #blk, wht = wht, blk # cheeky
        
        # draw the title
        pygame.draw.rect(buffer, wht, (0, 0, self.width, self.titlearea_height))
        title_width = self.font.get_rect(self.title)[2]
        self.font.render_to(buffer, ((self.width - title_width) // 2, 9), self.title, fgcolor=blk, bgcolor=wht)
        
        # draw a separating line after 10 pixels
        pygame.draw.line(buffer, blk, (0, self.titlearea_height - 2), (self.width, self.titlearea_height - 2))
        # equals 12 pixels, leaving room for 4 13-px lines of chicago
        
        # draw the "contents"
        draw_first = self.scroll // self.item_height
        draw_last = (self.scroll + self.view_height - 1) // self.item_height + 1
        
        for item_index in range(draw_first, draw_last):
            if item_index == self.selected:
                tc, bc = wht, blk
            else:
                tc, bc = blk, wht
        
            y = self.titlearea_height + item_index * self.item_height - self.scroll
        
            pygame.draw.rect(buffer, bc, (0, y, self.view_width, self.item_height))
            
            if item_index >= self.item_count: continue
            
            text = self.items[item_index][0]
            if text.endswith(">"): # This shouldn't be in-band but whatevs
                text = text.rstrip(">")
                draw_arrow = True
            else:
                draw_arrow = False
            
            self.font.render_to(buffer, (1, y+10), text, fgcolor=tc, bgcolor=bc)
            
            if draw_arrow:
                x = self.view_width - 6
                pygame.draw.line(buffer, tc, (x, y+4), (x+2, y+6), 2)
                pygame.draw.line(buffer, tc, (x, y+8), (x+2, y+6), 2)
        
        if self.scrollbar_visible:
            pygame.draw.rect(buffer, wht,(self.view_width, self.titlearea_height, self.scrollbararea_width, self.view_height))
            pygame.draw.line(buffer, blk, (self.view_width + 1, self.titlearea_height - 1), (self.view_width + 1, self.height))
            pygame.draw.rect(buffer, blk, (self.view_width + 3, self.scrollbar_pos + self.titlearea_height, self.scrollbararea_width - 3, self.scrollbar_height))
        
        #return -1
    
    #def __init__(self, graf_props, items, title="untitled"):
    def _setup(self, graf_props, **kwargs):
        # will NOT change
        title = kwargs["title"]
        if title == "": title = "untitled"
        self.title = title.upper()
        
        self.items = kwargs["items"]
        # list of tuples: ("Artists>>>", a function)
        self.item_count = len(self.items)
        
        self.titlearea_height = 12
        self.view_width, self.view_height = graf_props[0], graf_props[1] - self.titlearea_height
        
        self.font = pygame.freetype.Font("chicago.bdf")
        self.font.origin = True
        self.font.antialiased = False
        self.item_height = 13 # self.font.get_sized_glyph_height()
        
        self.content_height = self.item_height * self.item_count
        if self.content_height <= self.view_height:
            self.scrollbar_visible = False
            self.scrollbararea_width = 0
        else:
            self.scrollbar_visible = True
            self.scrollbararea_width = 7
            self.scrollbar_height = max(10, self.view_height * self.view_height / self.content_height)
        
        self.view_width = self.view_width - self.scrollbararea_width
                
        # will change:
        self.scroll = 0
        self.selected = 0
        self.scrollbar_pos = 0
        
        #Client.__init__(self, graf_props)
        
    def _event(self, event):
        if event == "back":
            self.parent_server.remove_client(self)
            return False
        
        elif event == "ok":
            func = self.items[self.selected][1]
            if func != None: func(self.parent_server)
            return False
        
        elif event == "up":
            if self.selected > 0:
                self.selected -= 1
                if self.scrollbar_visible:
                    max_scroll = self.selected * self.item_height
                    if self.scroll > max_scroll: self.scroll = max_scroll
                
        elif event == "down":
            if self.selected < self.item_count - 1:
                self.selected += 1
                if self.scrollbar_visible:
                    min_scroll = (self.selected + 1) * self.item_height - self.view_height
                    if self.scroll < min_scroll: self.scroll = min_scroll
        
        else:
            return None
        
        if self.scrollbar_visible:
            scrollbar_max = self.view_height - self.scrollbar_height + 1
            scroll_max = self.content_height - self.view_height
            self.scrollbar_pos = scrollbar_max * self.scroll / scroll_max
        
        return True
