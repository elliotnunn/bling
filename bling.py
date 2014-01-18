#!/usr/bin/env python2

import threading
import pygame
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
            self.draw_frame(self.get_buffer(False))
            
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
    
    def event(self, event):
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


class Compositor(Client, Server):
    def prepare_to_draw_frame(self):
        "Nothing"
    
    def draw_frame(self, buffer):
        
        my_back_buffer = buffer
        
        buffer.fill((0, 0, 0))
        
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
            offset += 0
        
        self.client_list_lock.release()
        
    def add_client(self, client):
        self.client_list_lock.acquire()
        self.clients.append(client)
        self.client_list_lock.release()
        client.parent_server = self
        self.dirty.set()
    
    def remove_client(self, client): # this is spaghetti
        self.client_list_lock.acquire()
        if client in self.clients: self.clients.remove(client)
        self.client_list_lock.release()
        #client.parent_server = None
        client.event("offscreen")
        self.dirty.set()
    
    def notify_client_dirty(self):
        self.dirty.set()
    
    def __init__(self, graf_props):
        # init the super
        
        Client.__init__(self, graf_props)
        Server.__init__(self)
        
        self.clients = []
        self.client_list_lock = threading.RLock()
    
    def event(self, event): # this is pretty ugly
        if event == "quit":
            self.quit_flag = True
            self.dirty.set()
            
            self.client_list_lock.acquire()
            for client in self.clients:
                client.event("quit")
            self.client_list_lock.release()
        else:
            self.client_list_lock.acquire()
            if len(self.clients) > 0:
                client = self.clients[-1]
                self.client_list_lock.release()
                client.event(event)
            else:
                self.client_list_lock.release()
        

class Clock(Client):
    def draw_frame(self, buffer):
        buffer.fill(self.bg)
        
        newsurf = self.font.render("FrmCt=" + str(self.count), False, self.fg, self.bg)
        buffer.blit(newsurf, (2, 2))
        
        self.count += 1
    
    def __init__(self, graf_props):
        Client.__init__(self, graf_props)
        
        self.count = 0
        self.font = pygame.font.SysFont("chicagoflf", 12)
        print str(self.font.get_linesize())
        
        self.bg = (0, 0, 0); self.fg = (255, 255, 255);
        
        self.dirty.set()
    
    def event(self, event):
        if event == "quit":
            self.quit_flag = True
            self.dirty.set()
                

class ProtoMenu(Client):
    def draw_frame(self, buffer):
        # draw a frame!
        draw_first = self.scroll // self.item_height
        draw_last = (self.scroll + self.view_height - 1) // self.item_height + 1
    
        for item_index in range(draw_first, draw_last):
            if item_index == self.selected:
                fg = (255, 255, 255); bg = (0, 0, 0);
            else:
                bg = (255, 255, 255); fg = (0, 0, 0);
        
            y = item_index * self.item_height - self.scroll
        
            pygame.draw.rect(buffer, bg, (0, y, self.view_width, self.item_height))
            
            if item_index < self.item_count:
                text = self.font.render(self.items[item_index][0], False, fg, bg)
                buffer.blit(text, (4, y))
        
        bg = (255, 255, 255); fg = (0, 0, 0);
        pygame.draw.line(buffer, fg, (self.view_width, 0), (self.view_width, self.view_height))
        pygame.draw.rect(buffer, bg, (self.view_width+1, 0, 9, self.view_height))
        sb_y = self.scroll * self.view_height / self.content_height
        sb_h = self.view_height * self.view_height / self.content_height
        pygame.draw.rect(buffer, fg, (self.view_width+1, sb_y, 9, sb_h))
    
    def __init__(self, graf_props, items):
        Client.__init__(self, graf_props)
        
        self.items = items # list of tuples: ("Artists>>>", a function)
        self.item_count = len(self.items)
        
        self.view_width, self.view_height = self.width, self.height
        self.font = pygame.font.SysFont("ChicagoFLF", 12)
        self.item_height = self.font.get_linesize()
        self.content_height = self.item_height * self.item_count
        self.show_scrollbar = self.content_height > self.view_height
        
        if self.show_scrollbar:
            self.view_width -= 10
        
        # will change:
        self.scroll = 0
        self.selected = 0
        
        self.dirty.set()
        
    def event(self, event):
        do_redraw = False
        
        if event == "back":
            self.parent_server.remove_client(self)
            # will eventually result in an "offscreen" event
        
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
        
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            do_redraw = True
        
        if event == "ok":
            func = self.items[self.selected][1]
            if func != None: func(self.parent_server)
        
        if do_redraw: self.dirty.set()



# cutting out the compositor decreases frame-time by 1.6ms, from 15.1ms to 13.5ms
# text drawing seems to be really slow, but blitting is fast!
