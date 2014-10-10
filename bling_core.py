#!/usr/bin/env python2

import threading
import pygame
# import os
import time
import random
import ctypes
import traceback
import sys


class Client(threading.Thread):
    def __init__(self, graf_props, **kwargs):
        threading.Thread.__init__(self)
        self.width, self.height, self.depth, self.palette = graf_props
        
        self.quit_flag = False
        self.have_bailed = False
        
        # set up two buffers
        self.buffer_a = pygame.Surface((self.width, self.height), depth=self.depth)
        self.buffer_b = pygame.Surface((self.width, self.height), depth=self.depth)
        self.buffer_a.set_palette(self.palette)
        self.buffer_b.set_palette(self.palette)
        self.which_buffer = True # True means buffer_a is front
        self.buffer_lock = threading.Lock()
        
        # start life as an orphan
        self.parent_server = None
        
        self.dirty = threading.Event()
        
        (self.t, self.nxt) = (pygame.time.get_ticks()/1000, None)
        
        try:
            self._setup(graf_props, **kwargs)
        except:
            self.__bail("while initialising")
        else:
            try:
                self.nxt = self._draw_frame(buffer=self.buffer_a, is_initial=True)
            except:
                self.__bail("while drawing its initial frame")
            else:
                self.buffer_b.blit(self.buffer_a, (0, 0))
                self.start()
    
    def _setup(self, graf_props, **kwargs):
        # gets called right before __init__ returns
        # buffers are ready, etc
        # should defs be overridden
        # The following is ONLY for compatibility with older
        # Clients which override __init__ instead of _setup.
        pass
    
    def run(self): 
        while self.quit_flag==False:
            # Choose how long to wait before drawing a frame
            if self.nxt == None: self.nxt = sys.maxsize
            #if self.nxt == -1: self.nxt = self.t
            if self.nxt < self.t + 50: self.nxt = self.t
            
            if self.nxt == sys.maxsize: # until woken
                if self.__class__.__name__=="FabCompositor": print("waiting forever")
                self.dirty.wait()
                self.dirty.clear()
                
            else:                                           # arbitrary
                if self.__class__.__name__=="FabCompositor":
                    print("waiting from %d to %d" % (pygame.time.get_ticks(), self.nxt))
                pygame.time.wait(self.nxt - pygame.time.get_ticks())
                self.dirty.clear()
            
            # Draw the actual frame
            try:
                self.t = pygame.time.get_ticks() # update frame-time
                self.nxt = self._draw_frame(buffer=self.get_buffer(False),
                                              is_initial=False)
                
            except:
                self.__bail("while drawing a frame")
                self.quit_flag = True # escape from this loop right now
            
            else:
                # Flip the buffers
                self.buffer_lock.acquire()
                self.which_buffer = not self.which_buffer
                self.buffer_lock.release()
                
                # Notify our server, if we have one -- race condition?
                if self.parent_server != None:
                    self.parent_server.notify_client_dirty()
    
    def get_buffer(self, want_front):
        return self.buffer_a if (self.which_buffer == want_front) \
          else self.buffer_b
    
    def event(self, event):
        # called by InputServers
        # Do not override this; override _event instead
        # catches exceptions in our event handling and skelefies this client
        if self.have_bailed: # this code duplicates our _event function
            if event == "quit" or event == "offscreen":
                self.quit_flag = True
                self.dirty.set()
            elif event == "back":
                self.parent_server.remove_client(self) # will eventually result in an "offscreen" event

        else:
            try:
                self._event(event)
            except:
                self.__bail("while handling an event")
    
    def _event(self, event):
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            self.dirty.set()
        elif event == "back":
            self.parent_server.remove_client(self) # will eventually result in an "offscreen" event
    
    def _draw_frame(self, buffer=None, is_first=False):
        "Nothing"
    
    def __bail(self, happened_while):
        # called when a subclass has thrown an exception
        # from _setup, _event or _draw_frame
        self.have_bailed = True
        print("Oh, pickle; a Client spat the dummy %s." % happened_while)
        traceback.print_exc(5)

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
