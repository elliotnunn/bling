#!/usr/bin/env python2

import threading
import pygame
import os
import time
import random
import ctypes


class Client(threading.Thread):
    def run(self):
        while True:
            # event will fire to tell us to draw a frame
            self.dirty.wait()
            self.dirty.clear()
            
            # Don't need to acquire self.buffer_lock because this
            # is the only place we ever modify self.which_buffer
            self.draw_frame(self.get_buffer(False))
            
            # But to modify which_buffer, we need the lock
            self.buffer_lock.acquire()
            self.which_buffer = not self.which_buffer
            self.buffer_lock.release()
            
            # Notify our server, if we have one
            if self.parent_server != None:
                self.parent_server.notify_client_dirty()
    
    def __init__(self, width, height, depth, palette):
        threading.Thread.__init__(self)
        self.daemon = True # this is bad!
        
        # set up two buffers
        self.buffer_a = pygame.Surface((width, height), depth=depth)
        self.buffer_b = pygame.Surface((width, height), depth=depth)
        self.buffer_a.set_palette(palette)
        self.buffer_b.set_palette(palette)
        self.which_buffer = True # True means buffer_a is front
        self.buffer_lock = threading.Lock()
        
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
    
    def draw_frame(self, buffer):
        "Nothing"


class Server:
    def notify_client_dirty(self):
        "Nothing"
    def add_client(self, client):
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


class PygameInputServer(InputServer, threading.Thread):
    def run(self):
        print "PygameInputServer thread running"
        
        while True:
            event = pygame.event.wait()
            print "event"
            if event.type == "KEYDOWN":
                print event.key()
    
    def _init_(self):
        "Nothing"
    
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
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)
        
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
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break
    
        if not found:
            raise Exception('No suitable video driver found!')
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
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


class Compositor(Client, Server, threading.Thread):
    def prepare_to_draw_frame(self):
        "Nothing"
    
    def draw_frame(self, buffer):
        
        my_back_buffer = buffer
        
        # one day this will be smarter:
        # - only drawing the topmost fullscreen window and above
        # - drawing a transformed image at the coordinates set by an animation
        # my_back_buffer.fill((255, 255, 255))
        self.client_list_lock.acquire()
        offset = 0
        for client in self.clients:
            # Client may not swap buffers while we are blitting its front buffer!
            client.buffer_lock.acquire()
            client_front_buffer = client.get_buffer(True)
            my_back_buffer.blit(client_front_buffer, (offset, offset))
            client.buffer_lock.release()
            offset += 25
        
        self.client_list_lock.release()
        
    def add_client(self, client):
        self.client_list_lock.acquire()
        self.clients.append(client)
        self.client_list_lock.release()
        client.parent_server = self
    
    def notify_client_dirty(self):
        self.dirty.set()
    
    def __init__(self, width, height, depth, palette):
        # init the super
        
        Client.__init__(self, width, height, depth, palette)
        Server.__init__(self)
        
        self.clients = []
        self.client_list_lock = threading.Lock()
        


class Clock(Client, threading.Thread):
    def draw_frame(self, buffer):
        back_buffer = buffer
        
        bg = (0, 0, 0); fg = (255, 255, 255);
        
        back_buffer.fill(bg)
        sysfont = pygame.font.SysFont("chicagoflf", 12)
        newsurf = sysfont.render("Frame: " + str(self.count), False, fg, bg)
        back_buffer.blit(newsurf, (2, 2))
        
        self.count += 1
    
    def __init__(self, width, height, depth, palette):
        Client.__init__(self, width, height, depth, palette)
        self.count = 0
        self.dirty.set()
        
        print pygame.font.get_fonts()
                

class ProtoMenu(Client, threading.Thread):
    def draw_frame(self, buffer):
        # draw a frame!
        draw_first = self.scroll // self.item_height
        draw_last = (self.scroll + self.view_height) // self.item_height
    
        back_buffer = buffer
    
        for item_index in range(draw_first, draw_last):
            if item_index == self.selected:
                fg = (255, 255, 255); bg = (0, 0, 0);
            else:
                bg = (255, 255, 255); fg = (0, 0, 0);
        
            y = item_index * self.item_height - self.scroll
        
            pygame.draw.rect(back_buffer, bg, (0, y, 128, self.item_height))
            text = self.font.render(self.items[item_index], False, fg, bg)
            back_buffer.blit(text, (4, y))
    
    def __init__(self, width, height, depth, palette):
        self.item_count = 9
        self.items = ["The", "Quick", "Brown", "Fox", "Jumps", "Over", "The", "Lazy", "Dog"]
        self.view_height = 64
        self.item_height = 16
        self.scroll = 0
        self.selected = 0
        
        self.font = pygame.font.SysFont("ChicagoFLF", 12)
        
        Client.__init__(self, width, height, depth, palette)
        self.dirty.set()
        
    
    def event(self, event):
        do_redraw = False
        
        if event == "up":
            if self.selected > 0:
                self.selected -= 1
                do_redraw = True
                max_scroll = self.selected * self.item_height
                if self.scroll > max_scroll: self.scroll = max_scroll
                
        if event == "down":
            if self.selected < self.item_count - 1:
                self.selected += 1
                do_redraw = True
                min_scroll = (self.selected + 1) * self.item_height - self.view_height
                if self.scroll < min_scroll: self.scroll = min_scroll
        
        if do_redraw: self.dirty.set()


if False:
    os.putenv('SDL_VIDEODRIVER', 'fbcon') # What the fuck?
    pygame.display.init()
    screen = pygame.display.set_mode((pygame.display.Info().current_w, pygame.display.Info().current_h), pygame.FULLSCREEN)
    screen.fill((127, 0, 127))        
    pygame.display.update()
    pygame.font.init()

    #x = PixelChucker()
    palette = tuple([(i, i, i) for i in range(0, 255)])

    print 'Initialising driver (ST7565Server)'
    driver = ST7575Server()

    # print 'Initialising input server (PygameInputServer)'
    # input_server = PygameInputServer()

    print 'Initialising Compositor'
    compositor = Compositor(width = 128, height = 64, depth = 8, palette = palette)

    # print 'Attaching compositor to input server'
    # input_server.add_client(compositor)

    print 'Attaching Compositor to driver'
    driver.add_client(compositor)

    print 'Initialising Clock'
    clock = Clock(width = 128, height = 64, depth = 8, palette = palette)

    print 'Attaching Clock to Compositor'
    compositor.add_client(clock)

    demo_wait_time = 15
    print "Running for %ds" % demo_wait_time
    time.sleep(demo_wait_time)

    print 'Deinitialising driver'
    driver.deinit()

# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
