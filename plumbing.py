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


import pygame as pg

import _thread
import time
import traceback
import sys


class Source:
    
    def _draw_widgets(self, surf=None, which=None):
        if surf == None: surf = self.bbuff # potentially dangerous
        if which == None: which = self.widgets
        if not hasattr(which, "__iter__"): which = [which]
        for w in which:
            nxt = w.draw(surf, w.xy_in_parent, self.t)
            if nxt != None: self.nxt = min(self.nxt, nxt)
    
    def __init__(self, size=None, **k):
        self.size = size
        if self.size == None:
            dispinf = pg.display.Info()
            self.size = (dispinf.current_w, dispinf.current_h)
        
        #HACK
        self.nxt = 0
        
        self.parent = None
        
        self.fbuff = pg.Surface(self.size)
        self.bbuff = pg.Surface(self.size)
        
        self.evtq = []
        
        self.evtq_latch = _thread.allocate_lock()
        self.evtq_latch.acquire()
        self.evtq_lock = _thread.allocate_lock()
        self.buff_lock = _thread.allocate_lock()
        self.throttle = _thread.allocate_lock()
        
        _thread.start_new_thread(self._loop, ())
    
    # Shim layer; treats calls to unimplemented as_* as events
    def __getattr__(self, funcname):
        if funcname.startswith('as_'):
            def callme(*args, **kwargs):
                self.event(funcname[3:], *args, **kwargs)
            return callme
        else:
            raise AttributeError
    
    def event(self, name, *args, **kwargs):
        with self.evtq_lock:
            self.evtq.append((name, args, kwargs))
        
        try: self.evtq_latch.release()
        except RuntimeError: pass
    
    def _wait_next_event(self, timeout=-1):
        if timeout >= 0:
            self.evtq_latch.acquire(timeout=(timeout/1000))
        else:
            self.evtq_latch.acquire()
        
        with self.evtq_lock:
            evt = self.evtq.pop(0)
            if len(self.evtq) > 0: self.evtq_latch.release()
        
        return evt
    
    def unthrottle(self):
        try: self.throttle.release()
        except: pass
    
    def _throttle(self):
        self.throttle.acquire()
    
    def _flip(self):
        with self.buff_lock:
            self.fbuff, self.bbuff = self.bbuff, self.fbuff
        
        if self.parent != None:
                self.parent.as_dirty()
    
    def _handle_event(self, event_tuple):
        event, args, kwargs = event_tuple
        
        try:
            getattr(self, '_as_' + event)(*args, **kwargs)
            print("%s %s %s to %s" % (event, args, kwargs, self.__class__.__name__))
        except AttributeError:
            print("FAILED %s %s %s to %s" % (event, args, kwargs, self.__class__.__name__))
    
    def _as_set_parent(self, parent):
        self.parent = parent


class SexySource(Source):
    
    def __init__(self, **k):
        self.kwargs = k
        self.widgets = []
        self.t = 0
        super(SexySource, self).__init__(**k)
    
    def _loop(self, *k):
        self._setup(**self.kwargs)
        
        while 1:
            self._handle_event(self._wait_next_event())
            
            self._throttle()
            
            self._draw_frame(self.bbuff, True)
            
            self._flip()


class Sink(): pass


class Compositor(Sink, Source):
    
    def _as_add_source(self, source):
        self.viewport = self.viewport + (128,0)
        
        self.sources.append((source, self.viewport))
        
        source.as_set_parent(self)
        source.as_fully_onscreen()
        if len(self.sources) >= 2:
            self.sources[-2].as_offscreen()
    
    def _as_remove_source(self, source):
        for i in range(0, len(self.sources)):
            if self.sources[i][0] == source:
                self.sources.pop(i)
                break
        
        source.as_set_parent(None)
        source.as_offscreen()
        
        self.viewport = self.viewport - (128,0)
    
    def _as_source_dirty(self, source):
        pass
    
    def _as_input(self, *args, **kwargs):
        if len(self.sources) >= 1:
            self.sources[-1].as_input(*args, **kwargs)
    
    def _loop(self):
        self.sources = []
        self.viewport = (-128,0)
        
        while True:
            frame_deadline = False
            
            self._handle_event(self._wait_next_event())
            
            # Calculate and dwar
            source_count = len(self.sources)
            topmost_obscurer = 0
            
            for i in reversed(range(0, source_count)):
                source, topleft, *misc = self.sources[i]
                bottomright = topleft + source.size
                if not(topleft > self.viewport) and not(bottomright < (self.viewport+self.size)):
                    topmost_obscurer = i
                    break
            
            for i in range(0, source_count):
                source, topleft, *misc = self.sources[i]
                
                # Composite this buffer onto the back buffer
                if i >= topmost_obscurer:
                    with source.buff_lock:
                        self.bbuff.blit(source.fbuff, (topleft[0]-self.viewport[0], topleft[1]-self.viewport[1]))
                
                # Do this regardless of whether it is in view
                source.unthrottle()
            
            self._flip()
    
    def __init__(self):
        Source.__init__(self)
        Sink.__init__(self)


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
                time_elapsed_ms = pg.time.get_ticks() - start_time_ms
                
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
                        
                    self.clients[i] = (client, x, 0, animation)
                    
                    animating = True
        
        return animating
    
    def add_client(self, client, anim_duration_ms=200):
        self.big_lock.acquire()
        self.clients.append((client, 0, 0, (pg.time.get_ticks(), anim_duration_ms, 1)))
        self.big_lock.release()
        
        client.parent_server = self
        
        try: self.evt_sem.release()
        except: pass
    
    def remove_client(self, client, anim_duration_ms=200):
        self.big_lock.acquire()
        for i in reversed(range(0, len(self.clients))):
            if self.clients[i][0] == client:
                self.clients[i] = (self.clients[i][0], 0, 0, (pg.time.get_ticks(), anim_duration_ms, -1))
                break
        self.big_lock.release()
        
        try: self.evt_sem.release()
        except: pass
