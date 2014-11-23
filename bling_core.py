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
        self.fbuff = pygame.Surface((self.width, self.height), depth=self.depth)
        self.bbuff = pygame.Surface((self.width, self.height), depth=self.depth)
        self.fbuff.set_palette(self.palette)
        self.bbuff.set_palette(self.palette)
        
        # start life as an orphan
        self.parent_server = None
        
        self.evt_sem = threading.Lock()  # acts as a semaphore
        self.sync_sem = threading.Lock() # and has no concept of owning thread
        
        (self.t, self.nxt) = (pygame.time.get_ticks()/1000, None)
        
        try:
            self._setup(graf_props, **kwargs)
        except:
            self.__bail("while initialising")
        else:
            try:
                # draw an initial frame synchronously
                self.nxt = self._draw_frame(buffer=self.fbuff, is_initial=True)
            except:
                self.__bail("while drawing its initial frame")
            else:
                self.bbuff.blit(self.fbuff, (0, 0))
                self.start()
    
    def _setup(self, graf_props, **kwargs):
        # gets called right before the first frame is drawn
        pass
    
    def run(self): 
        while self.quit_flag==False:
            # first must not draw frame before app demands
            if self.nxt == sys.maxsize or self.nxt == None:
                self.evt_sem.acquire() # wait indef until sem released
            else:
                timeout_ms = self.nxt - pygame.time.get_ticks()
                if timeout_ms > 0:
                    self.evt_sem.acquire(timeout=timeout_ms/1000)
                else:
                    self.evt_sem.acquire(blocking=False)
            
            # second must not draw frame before Server allows
            self.sync_sem.acquire()
            
            # at this point we are committed to drawing a frame without delay
            try:
                self.t = pygame.time.get_ticks() # update canonical frame time
                self.nxt = self._draw_frame(buffer=self.bbuff, is_initial=False)
            
            except:
                self.__bail("while drawing a frame")
                self.quit_flag = True # escape from this loop right now
            
            else:
                # this is safe 
                self.fbuff, self.bbuff = self.bbuff, self.fbuff
                
                if self.parent_server != None:
                    self.parent_server.notify_client_dirty()
    
    def get_buffer(self, want_front):
        return self.fbuff if want_front else self.bbuff
    
    def event(self, event):
        # called by InputServers
        # Do not override this; override _event instead
        # catches exceptions in our event handling and skelefies this client
        if self.have_bailed:
            Client._event(self, event)
        
        else:
            try:
                release_evt_sem = self._event(event)
            except:
                self.__bail("while handling an event")
            else:
                if release_evt_sem == True:
                    try: self.evt_sem.release()
                    except: pass
                # perhaps add a better fallback someday, as described below
    
    # Override this. Return True if you want _draw_frame to be called,
    # False for nothing and None for a default handler to be called
    def _event(self, event):
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            return True
        elif event == "back":
            self.parent_server.remove_client(self) # will eventually result in an "offscreen" event
            return False
    
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
        pass
    def add_client(self, client):
        pass
    def remove_client(self, client):
        pass
    def __init__(self):
        pass


class InputServer:
    def add_client(self, client):
        "Nothing"
