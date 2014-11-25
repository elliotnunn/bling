#!/usr/bin/env python2

import threading
import pygame
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
        
        self.evt_sem = threading.Lock()  # These act as semaphores, having
        self.sync_sem = threading.Lock() # no concept of an owning thread.
        self.buff_sem = threading.Lock()
        self.evt_sem.acquire()
        self.sync_sem.acquire()
        
        (self.t, self.nxt) = (pygame.time.get_ticks(), None)
        
        try:
            self._setup(graf_props, **kwargs)
        except:
            self.__bail("while initialising")
            return
        
        # Initial frame gets drawn synchronously (NOT from thread)
        try:
            self.nxt = self._draw_frame(buffer=self.fbuff, is_initial=True)
        except:
            self.__bail("while drawing its initial frame")
            return

        self.bbuff.blit(self.fbuff, (0, 0))
        self.start()
    
    def run(self): 
        while True:
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
            
            if self.quit_flag: break
            
            # at this point we are committed to drawing a frame without delay
            try:
                self.t = pygame.time.get_ticks() # update canonical frame time
                self.nxt = self._draw_frame(buffer=self.bbuff, is_initial=False)
            except:
                self.__bail("while drawing a frame")
                break
            
            if self.quit_flag: break
            
            self.buff_sem.acquire()
            self.fbuff, self.bbuff = self.bbuff, self.fbuff
            self.buff_sem.release()
            
            if self.parent_server != None:
                self.parent_server.notify_client_dirty()
    
    def get_buffer(self, want_front):
        return self.fbuff if want_front else self.bbuff
    
    # called by InputServers
    # Do not override this; override _event instead
    # catches exceptions in our event handling and skelefies this client
    def event(self, event):
        if not self.have_bailed:
            try: # Pass the event through to the subclass's handler
                release_evt_sem = self._event(event)
            except: # But if we get an exception then skelefy this client
                self.__bail("while handling an event")
                return
            
            if release_evt_sem == None: # Handler deferred to default handler
                release_evt_sem = Client._event(self, event)
            
            if release_evt_sem == True: # Handler asks for new frame
                try: self.evt_sem.release()
                except: pass
            
            if self.quit_flag: # Probably from default handler, which would
                try: self.sync_sem.release() # also have returned True.
                except: pass
            
        elif self.have_bailed: # The default handler won't crash
            Client._event(self, event) # and we don't care what it returns
    
    def server_allows_draw(self):
        try: self.sync_sem.release()
        except: pass
    
    # Called when one of the below methods (_setup, _event or _draw_frame),
    # presumably overridden, throws an exception. Makes it possible to
    # close the client using the basic _event handler.
    def __bail(self, happened_while):
        print("Oh, pickle; a Client spat the dummy %s." % happened_while)
        traceback.print_exc(5)
        
        self.quit_flag = self.have_bailed = True
        
        try: self.sync_sem.release() # Duplicates server_allows_draw()
        except: pass                 # for clarity.
        
        try: self.evt_sem.release()
        except: pass
    
    # Subclass to override this to do initialisation before the first frame is
    # drawn. Called from the constructor.
    def _setup(self, graf_props, **kwargs):
        pass
    
    # Subclass should override this to handle events (which are synchronous).
    # Return values:
    #                True   Call _draw_frame immediately.
    #                False  Do nothing.
    #                None   Send this event to the default handler
    def _event(self, event):
        if event == "quit" or event == "offscreen":
            self.quit_flag = True
            return True
        elif event == "back": # We'll get an offscreen event from this.
            self.parent_server.remove_client(self)
            return False
    
    # Subclass should override this to draw a frame and schedule the next frame.
    # Called once from the constructor and subsequently from the thread loop.
    # Return the time [as given by pygame.time.get_ticks()] to draw the next
    # frame. Special values:
    #                        sys.maxsize or None                  indefinitely
    #                        current or past time (e.g. self.t)   immediately
    # 
    def _draw_frame(self, buffer=None, is_initial=False):
        pass

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
        pass
