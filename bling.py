#!/usr/bin/env python2

import threading
import pygame
import os
import time
import random
import ctypes


class Client:
    def __init__(self, width, height, depth, palette):
        # BUFFERS
        self.buffer_a = pygame.Surface((width, height), depth=depth)
        self.buffer_b = pygame.Surface((width, height), depth=depth)
        self.buffer_a.set_palette(palette)
        self.buffer_b.set_palette(palette)
        self.which_buffer = True # True means buffer_a is front
        self.buffer_lock = threading.Lock()
        
        self.parent_server = None
    
    def get_buffer(self, front):
        if self.which_buffer == front:
            return self.buffer_a
        else:
            return self.buffer_b
    
    def swap_buffers(self):
        self.buffer_lock.acquire()
        self.which_buffer = not self.which_buffer
        self.buffer_lock.release()
    
    def am_dirty(self):
        if self.parent_server != None:
            self.parent_server.notify_client_dirty()


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
    
    def deinit():
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
    
    def run(self):
        print "Compositor thread waiting"
        while True:
            self.client_dirty.wait() # only if no animation in progress
            self.client_dirty.clear()
            
            # Subclassess will implement this to do animations, etc
            self.prepare_to_draw_frame()
            
            # Don't need to acquire self.buffer_lock because this
            # is the only place we ever modify self.which_buffer
            my_back_buffer = self.get_buffer(False)
            
            # one day this will be smarter:
            # - only drawing the topmost fullscreen window and above
            # - drawing a transformed image at the coordinates set by an animation
            # my_back_buffer.fill((255, 255, 255))
            self.client_list_lock.acquire()
            for client in self.clients:
                # Client may not swap buffers while we are blitting its front buffer!
                client.buffer_lock.acquire()
                client_front_buffer = client.get_buffer(True)
                my_back_buffer.blit(client_front_buffer, (0, 0))
                client.buffer_lock.release()
            
            self.client_list_lock.release()
            
            # Now we acquire the lock so that we don't swap our buffers
            # while our parent server is accessing them
            self.buffer_lock.acquire()
            self.which_buffer = not self.which_buffer
            self.buffer_lock.release()
            
            self.am_dirty()
        
    def add_client(self, client):
        self.client_list_lock.acquire()
        self.clients.append(client)
        self.client_list_lock.release()
        client.parent_server = self
    
    def notify_client_dirty(self):
        self.client_dirty.set()
        print "comp notified"
    
    def __init__(self, width, height, depth, palette):
        # init the super
        
        Client.__init__(self, width, height, depth, palette)
        Server.__init__(self)
        threading.Thread.__init__(self)
        
        self.clients = []
        self.client_list_lock = threading.Lock()
        
        self.client_dirty = threading.Event()
        
        self.daemon = True
        self.start()


class Clock(Client, threading.Thread):
    def run(self):
        count = 0
        while True:
            count += 1
            
            back_buffer = self.get_buffer(False)
            
            back_buffer.fill((255, 255, 255))
            sysfont = pygame.font.SysFont("ChicagoFLF", 12)
            newsurf = sysfont.render("AWW " + str(count), True, (0, 0, 0), (255, 255, 255))
            back_buffer.blit(newsurf, (10, 0))

            self.swap_buffers()
            self.am_dirty()
            
            #time.sleep(0.5)
    
    def __init__(self, width, height, depth, palette):
        threading.Thread.__init__(self)
        Client.__init__(self, width, height, depth, palette)
        
        self.daemon = True
        self.start()
        

class ProtoMenu(Client, threading.Thread):
    def run(self):
        while True:
            self.dirty.wait()
            self.dirty.clear()
            
            # draw a frame!
            draw_first = self.scroll // self.item_height
            draw_last = (self.scroll + self.view_height) // self.item_height
            
            back_buffer = self.get_buffer(False)
            
            for item_index in range(draw_first, draw_last):
                if item_index == self.selected:
                    fg = (255, 255, 255); bg = (0, 0, 0);
                else:
                    bg = (255, 255, 255); fg = (0, 0, 0);
                
                y = item_index * self.item_height - self.scroll
                
                pygame.draw.rect(back_buffer, bg, (0, y, 132, self.item_height))
                text = self.font.render(self.items[item_index], False, fg, bg)
                back_buffer.blit(text, (4, y))
            
            self.swap_buffers()
            self.am_dirty()
    
    def __init__(self, width, height, depth, palette):
        self.item_count = 9
        self.items = ["The", "Quick", "Brown", "Fox", "Jumps", "Over", "The", "Lazy", "Dog"]
        self.view_height = 64
        self.item_height = 16
        self.scroll = 0
        self.selected = 0
        
        self.font = pygame.font.SysFont("ChicagoFLF", 12)
        
        threading.Thread.__init__(self)
        Client.__init__(self, width, height, depth, palette)
        
        self.dirty = threading.Event()
        
        self.daemon = True
        self.start()
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
    compositor = Compositor(width = 132, height = 64, depth = 8, palette = palette)

    # print 'Attaching compositor to input server'
    # input_server.add_client(compositor)

    print 'Attaching Compositor to driver'
    driver.add_client(compositor)

    print 'Initialising Clock'
    clock = Clock(width = 132, height = 64, depth = 8, palette = palette)

    print 'Attaching Clock to Compositor'
    compositor.add_client(clock)

    demo_wait_time = 15
    print "Running for %ds" % demo_wait_time
    time.sleep(demo_wait_time)

    print 'Deinitialising driver'
    driver.deinit()

# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
