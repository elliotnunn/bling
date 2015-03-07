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

from threading import Thread, Lock
import time
import traceback
import sys


class Source(Thread):
    def __init__(self, graf_props, **kwargs):
        Thread.__init__(self)
        self.graf_props = graf_props
        self.width, self.height, self.depth, self.palette = graf_props
        
        self.quit_flag = False
        self.have_bailed = False
        
        # set up two buffers
        self.fbuff = pygame.Surface((self.width, self.height))#, depth=self.depth)
        self.bbuff = pygame.Surface((self.width, self.height))#, depth=self.depth)
        #self.fbuff.set_palette(self.palette)
        #self.bbuff.set_palette(self.palette)
        # NOCOPY hack
        #self.skip_offering_buffer = False
        
        # start life as an orphan
        self.parent_server = None
        
        self.evt_sem = Lock()  # These act as semaphores, having
        self.sync_sem = Lock() # no concept of an owning thread.
        self.buff_sem = Lock()
        self.evt_sem.acquire()
        self.sync_sem.acquire()
        
        self.big_lock = Lock()
        
        self.widgets = []
        
        (self.t, self.nxt) = (pygame.time.get_ticks(), None)
        
        try:
            self._setup(graf_props, **kwargs)
        except:
            self.__bail("while initialising")
            return
        
        # Initial frame gets drawn synchronously (NOT from thread)
        self.nxt = sys.maxsize
        
        try:
            nxt = self._draw_frame(self.fbuff, True)
            if nxt != None: self.nxt = min(self.nxt, nxt)
        except:
            self.__bail("while drawing its initial frame")
            return

        self.bbuff.blit(self.fbuff, (0, 0))
        self.start()
    
    def run(self): 
        while True:
            # first must not draw frame before app demands
            if self.nxt == sys.maxsize:
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
            self.nxt = sys.maxsize
            
            try:
                self.t = pygame.time.get_ticks() # update canonical frame time
                with self.big_lock:
                    nxt = self._draw_frame(self.bbuff, False)
                if nxt != None: self.nxt = min(self.nxt, nxt)
            except:
                self.__bail("while drawing a frame")
                break
            
            if self.quit_flag: break
            
            # NOCOPY hack
            #if self.skip_offering_buffer:
                #continue
            
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
                release_evt_sem = Source._event(self, event)
            
            if release_evt_sem == True: # Handler asks for new frame
                try: self.evt_sem.release()
                except: pass
            
            if self.quit_flag: # Probably from default handler, which would
                try: self.sync_sem.release() # also have returned True.
                except: pass
            
        elif self.have_bailed: # The default handler won't crash
            Source._event(self, event) # and we don't care what it returns
    
    def server_allows_draw(self):
        try: self.sync_sem.release()
        except: pass
    
    # Called when one of the below methods (_setup, _event or _draw_frame),
    # presumably overridden, throws an exception. Makes it possible to
    # close the client using the basic _event handler.
    def __bail(self, happened_while):
        print("Oh, pickle; a Source spat the dummy %s." % happened_while)
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
    def _draw_frame(self, surf, first):
        surf.fill((255,255,255))
        self._draw_widgets(surf)
    
    def _draw_widgets(self, surf=None, which=None):
        if surf == None: surf = self.bbuff # potentially dangerous
        if which == None: which = self.widgets
        if not hasattr(which, "__iter__"): which = [which]
        for w in which:
            nxt = w.draw(surf, w.xy_in_parent, self.t)
            if nxt != None: self.nxt = min(self.nxt, nxt)
