from bling_core import *
import pygame.freetype
import time
import sys

class Compositor(Client, Server):
    def pre_frame(self): pass
    
    def _draw_frame(self, buffer, is_initial):
        self.client_list_lock.acquire()
        nxt = self.pre_frame() # this will update the x and y coordinates in self.clients
                
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
        
        return nxt
        
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
        Client.__init__(self, graf_props)
        Server.__init__(self)
    
    def _setup(self, graf_props):
        print("running setup")
        self.clients = []
        self.client_list_lock = threading.RLock()

    
    def _event(self, event): # this is pretty ugly
        if event == "quit":
            self.quit_flag = True
            self.dirty.set()
            
            self.client_list_lock.acquire()
            for client_tuple in self.clients:
                client_tuple[0].event("quit")
            self.client_list_lock.release()
            
        elif event == "screenshot":
            filename = "screenshot/bling @ %s.png" % time.ctime()
            self.buffer_lock.acquire()
            pygame.image.save(self.get_buffer(True), filename)
            self.buffer_lock.release()
            
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
                    
                    return self.t
    
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


class TimeTest(Client):
    def _setup(self, graf_props):
        self.font = pygame.freetype.Font("chicago.bdf")
    
    def _draw_frame(self, buffer=None, is_initial=False):
        buffer.fill((255,255,255), (0,0,self.width,self.height))
        
        self.font.render_to(buffer, (0,0), "t = %dms"%pygame.time.get_ticks())
        
        return self.t + 500
        

class SexyMenu(Client):
    class MenuItemWidget:
        def setup(self, text, font, width, height):
            self.gap, self.speed = 1, 20 # sec, px/sex
            
            self.text, self.width, self.height = text, width, height
            self.selected = False
            
            self.buff, rect = font.render(text, fgcolor=(0,0,0), bgcolor=(255,255,255))
            self.txt_y = 10 - rect[1] # the origin!
            self.txt_x = 2 + rect[0]
            
            max_string_width = width # - self.draw_x - 2
            self.overflow = (self.buff.get_width() > max_string_width)
            if self.overflow:
                # Figure out the goddamn cutoff width using numpy or something
                self.overflow_cutoff = max_string_width - 11 # (ellipsis width + 1px)
                self.cycle = self.gap + self.buff.get_width()/self.speed
        
        def set_selected(self, selected, at_time):
            self.selected = selected
            if selected: self.selected_when = at_time
        
        def draw(self, surf, pos, frame_time):
            fg = (255,255,255) if self.selected else (0,0,0)
            bg = (0,0,0) if self.selected else (255,255,255)
            
            # right here: choose whether to invert
            
            rect = pos + (self.width, self.height)
            surf.fill(bg, rect)
            buff_w, buff_h = self.buff.get_width(), self.buff.get_height()
            widg_x, widg_y = pos
            
            txt_y = widg_y + self.txt_y
            txt_x = widg_x + self.txt_x
            
            if self.overflow:
                if self.selected:
                    progress = (frame_time - self.selected_when) % self.cycle
                    if progress > self.gap:
                        src_x = (progress-self.gap)*self.speed
                        nxt = frame_time
                        print("anim")
                    else:
                        src_x = 0
                        nxt = frame_time + self.gap - progress
                        print("gap till %f" % nxt)
                        
                    src_w = buff_w - src_x
                    dest_x = 0
                    
                    if src_w < self.width:
                        draw_2 = True
                        src2_x = 0
                        src2_w = src_w - self.width
                        dest2_x = src_w
                    else:
                        draw_2 = False
                        src_w = self.width
                    
                    src_xywh = (src_x, 0, src_w, buff_h)
                    dest_xy = (dest_x, txt_y)
                    surf.blit(self.buff, dest_xy, area=src_xywh)
                    
                    if draw_2:
                        src2_xywh = (src2_x, 0, src2_w, buff_h)
                        dest2_xy = (dest2_x, txt_y)
                        surf.blit(self.buff, dest2_xy, area=src2_xywh)
                    
                else:
                    dest_xy = (0, txt_y)
                    src_w = self.width - 11
                    src_xywh = (0, 0, src_w, buff_h)
                    surf.blit(self.buff, dest_xy, area=src_xywh)
                    
                    # ellipses
                    dot_y = txt_y + buff_h - 2 - 3
                    for i in [1, 5, 9]:
                        dot_x = src_w + i
                        surf.fill(fg, (dot_x, dot_y, 2, 2))
                    
                    nxt = None
                        
            else:
                surf.blit(self.buff, (txt_x, txt_y))
                
                nxt = None
                # no animation
            
            return nxt
    
    def _setup(self, graf_props, items=["My name is Elliot Nunn.","Two","eight","acquire","stuff"]):
        self.font = pygame.freetype.Font("chicago.bdf")
        
        self.item_widgets = []
        for i in range(0,4):
            w = self.MenuItemWidget()
            w.setup(items[i], self.font, self.width, 13)
            self.item_widgets.append(w)
        
        self.selection = 0
        self.item_widgets[self.selection].set_selected(True, time.clock())
        self.scroll = 0
        
    def _draw_frame(self, buffer, is_initial):
        nxt = sys.maxsize
        
        for i in range(self.scroll, 4):
            widget = self.item_widgets[i % 4]
            widget_nxt = widget.draw(buffer, (0, 13*(i-self.scroll)), self.t)
            if widget_nxt==None:
                widget_nxt = sys.maxsize
                print("   widget wants no frame")
            elif widget_nxt == self.t:
                print("   widget wants to draw right now")
            else:
                print("   widget wants to draw at %f" % widget_nxt)
            nxt = min(nxt, widget_nxt)
        
        if nxt==sys.maxsize: nxt = None
        
        return nxt

class ProtoMenu(Client): # a bit of a mess, and poorly optimised
    def _draw_frame(self, buffer, is_initial):
        blk = (0, 0, 0)
        wht = (255, 255, 255)
        # blk, wht = wht, blk # cheeky
        
        # draw the title
        pygame.draw.rect(buffer, wht, (0, 0, self.width, self.titlearea_height))
        title_width = self.font.get_rect(self.title)[2]
        self.font.render_to(buffer, ((self.width - title_width) // 2, 9), self.title, fgcolor=blk, bgcolor=wht)
        
        # draw a separating line after 10 pixels
        pygame.draw.line(buffer, blk, (0, self.titlearea_height - 2), (self.width, self.titlearea_height - 2))
        # equals 12 pixels, leaving room for 4 lines of chicago
        
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
                x = self.view_width - 8
                pygame.draw.line(buffer, tc, (x, y+4), (x+2, y+6), 2)
                pygame.draw.line(buffer, tc, (x, y+8), (x+2, y+6), 2)
        
        if self.scrollbar_visible:
            pygame.draw.rect(buffer, wht,(self.view_width, self.titlearea_height, self.scrollbararea_width, self.view_height))
            pygame.draw.line(buffer, blk, (self.view_width + 1, self.titlearea_height - 1), (self.view_width + 1, self.height))
            pygame.draw.rect(buffer, blk, (self.view_width + 3, self.scrollbar_pos + self.titlearea_height, self.scrollbararea_width - 3, self.scrollbar_height))
    
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
            self.scrollbararea_width = 8
            self.scrollbar_height = max(10, self.view_height * self.view_height / self.content_height)
        
        self.view_width = self.view_width - self.scrollbararea_width
                
        # will change:
        self.scroll = 0
        self.selected = 0
        self.scrollbar_pos = 0
        
        #Client.__init__(self, graf_props)
        
    def _event(self, event):
        do_redraw = False
        do_change_scrollbar = False
        
        if event == "back":
            self.parent_server.remove_client(self)
            # will eventually result in an "offscreen" event
        
        if event == "up":
            if self.selected > 0:
                self.selected -= 1
                do_redraw = True
                max_scroll = self.selected * self.item_height
                if self.scroll > max_scroll:
                    self.scroll = max_scroll
                    do_change_scrollbar = True
                
        if event == "down":
            if self.selected < self.item_count - 1:
                self.selected += 1
                do_redraw = True
                min_scroll = (self.selected + 1) * self.item_height - self.view_height
                if self.scroll < min_scroll:
                    self.scroll = min_scroll
                    do_change_scrollbar = True
        
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            do_redraw = True
        
        if event == "ok":
            func = self.items[self.selected][1]
            if func != None: func(self.parent_server)
        
        if do_change_scrollbar:
            scrollbar_max = self.view_height - self.scrollbar_height + 1
            scroll_max = self.content_height - self.view_height
            self.scrollbar_pos = scrollbar_max * self.scroll / scroll_max
        
        if do_redraw: self.dirty.set()
