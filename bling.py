#!/usr/bin/env python2

import threading
import pygame
import pygame.freetype
import os
import time
import random
import ctypes


class Client(threading.Thread):
    def run(self):
        self.dirty.wait()
        self.dirty.clear()
        
        while self.quit_flag == False:
            # Don't need to acquire self.buffer_lock because this
            # is the only place we ever modify self.which_buffer
            self.draw_frame(buffer=self.get_buffer(False), is_initial=False)
            
            # But to modify which_buffer, we need the lock
            self.buffer_lock.acquire()
            self.which_buffer = not self.which_buffer
            self.buffer_lock.release()
            
            # Notify our server, if we have one
            if self.parent_server != None:
                self.parent_server.notify_client_dirty()
            
            # event will fire to tell us to draw a frame
            self.dirty.wait()
            self.dirty.clear()
        
    def __init__(self, graf_props):
        threading.Thread.__init__(self)
        self.width, self.height, self.depth, self.palette = graf_props
        
        self.quit_flag = False
        
        # set up two buffers
        self.buffer_a = pygame.Surface((self.width, self.height), depth=self.depth)
        self.buffer_b = pygame.Surface((self.width, self.height), depth=self.depth)
        self.buffer_a.set_palette(self.palette)
        self.buffer_b.set_palette(self.palette)
        self.which_buffer = True # True means buffer_a is front
        self.buffer_lock = threading.Lock()
        
        # draw an initial frame to both buffers
        self.draw_frame(buffer=self.buffer_a, is_initial=True)
        self.buffer_b.blit(self.buffer_a, (0, 0))
        
        # start life as an orphan
        self.parent_server = None
        
        # the thread's main loop will iterate when this event fires
        # and self.draw_frame(buffer) will get called
        self.dirty = threading.Event()
        
        self.start()
        
    def get_buffer(self, front):
        if self.which_buffer == front:
            return self.buffer_a
        else:
            return self.buffer_b
    
    def draw_frame(self, buffer, is_first=False):
        "Nothing"
    
    def event(self, event):
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            self.dirty.set()
        
        if event == "back":
            self.parent_server.remove_client(self) # will eventually result in an "offscreen" event


class Server:
    def notify_client_dirty(self):
        "Nothing" # Clients will do self.dirty.set()
    def add_client(self, client):
        "Nothing"
    def remove_client(self, client):
        "Nothing"
    def __init__(self):
        "Nothing"


class InputServer:
    def add_client(self, client):
        "Nothing"


class ST7575Server(Server):
    def __init__(self):
        self.libbuff=ctypes.CDLL('buff/libbuff.so')
        self.libbuff.init()
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
    
    def notify_client_dirty(self):
        client = self.client
        client.buffer_lock.acquire()
        self.libbuff.fling_buffer(client.get_buffer(True).get_buffer().raw) # sloooow??
        client.buffer_lock.release()
    
    def deinit(self):
        self.libbuff.deinit()


class StdinServer(InputServer, threading.Thread):
    def __init__(self):
        import tty, sys, termios
        threading.Thread.__init__(self)

    def run(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        ch = ""
        while ch != "q":
            tty.setraw(sys.stdin.fileno())
            
            # this blocks, and thank goodness
            ch = sys.stdin.read(1)
            if ch == "w":
                self.client.event("up")
            elif ch == "s":
                self.client.event("down")
            elif ch == "a":
                self.client.event("left")
            elif ch == "d":
                self.client.event("right")
            elif ch == "k":
                self.client.event("ok")
            elif ch == "b":
                self.client.event("back")
            elif ch == "q":
                self.client.event("quit")
        
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def add_client(self, client):
        self.client = client
        self.start()


class PixelChucker(Server):
    screen = None;
    
    def __init__(self):
        Server.__init__(self)
        
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        # if disp_no:
        #     print "I'm running under X display = {0}".format(disp_no)
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                #print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break
    
        if not found:
            raise Exception('No suitable video driver found!')
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        #print "Framebuffer size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((127, 0, 127))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
 
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
    
    def notify_client_dirty(self):
        client = self.client
        client.buffer_lock.acquire()
        self.screen.blit(client.get_buffer(True), (0, 0))
        client.buffer_lock.release()
        pygame.display.flip()


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
        self.dirty.set()
    
    def remove_client(self, client):
        self.client_list_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients.pop(i)
                break
        self.client_list_lock.release()
        
        client.parent_server = None
        self.dirty.set()
        client.event("offscreen")
    
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
        for i in range(0, len(self.clients)):
            # The tuples in self.clients are of the form (client, x_pos, y_pos) by default.
            # This subclass extends them to (client, x_pos, y_pos, animation),
            # where animation = (start_time_in_s, duration_in_s, direction), and
            # direction is -1 for sliding out to the right, and 1 for sliding in from the right
            (client, x, y, animation) = self.clients[i][0:4]
            
            if animation != None:
                (start_time, duration, direction) = animation #unpack the tuple in the tuple in self.clients
                progress = (time.clock() - start_time) / duration * self.width
                
                if progress >= self.width: #put a stop to this animation
                    animation = None
                    if direction == -1: # this was a fuck-off animation
                        self.clients.pop(i) # DANGEROUS
                        client.parent_server = None
                        client.event("offscreen")
                    else: # the client remains visible once the animation ends
                        self.clients[i] = (client, 0, 0, None)
                        
                else: 
                    if direction == -1: # ie sliding out to the right
                        x = progress
                    elif direction == 1: # sliding in from the right
                        x = self.width - progress
                        
                    self.clients[i] = (client, x, 0, animation)
            
                self.dirty.set() # go like mad
    
    def add_client(self, client):
        self.client_list_lock.acquire()
        self.clients.append((client, 0, 0, (time.clock(), 0.2, 1)))
        self.client_list_lock.release()
        
        client.parent_server = self
        self.dirty.set()
    
    def remove_client(self, client):
        self.client_list_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients[i] = (self.clients[i][0], 0, 0, (time.clock(), 0.2, -1))
                break
        self.client_list_lock.release()
        
        self.dirty.set()
        

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
                

class ProtoMenu(Client): # a bit of a mess, and poorly optimised
    def draw_frame(self, buffer, is_initial):
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
    
    def __init__(self, graf_props, items, title="untitled"):
        # will NOT change
        self.title = title.upper()
        
        self.items = items # list of tuples: ("Artists>>>", a function)
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
        
        Client.__init__(self, graf_props)
        
    def event(self, event):
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



# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
