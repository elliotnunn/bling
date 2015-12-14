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
pg = pygame

import _thread
import time
import traceback
import sys


class EventQueue:
    class Event:
        def __init__(self, funcname, args, kwargs):
            self.funcname = funcname
            self.retval = (funcname, args, kwargs)
            self.pointer = None
    
    class Timeout(Exception): pass
    
    def prt(self):
        t = self.front
        while t:
            print('%s %s' % (t.funcname, t == self.back))
            t = t.pointer
        
        print('')
        print('%s %s' % (self.latch.locked(), self.back_lock.locked()))
    
    def __init__(self):
        self.back_lock = _thread.allocate_lock()
        self.latch     = _thread.allocate_lock()
        self.latch.acquire()
        
        self.front = self.back = self.Event(None, None, None)
    
    def __release_latch(self):
        try:
            self.latch.release()
        except RuntimeError:
            pass
    
    def push(self, funcname, args, kwargs):
        event = self.Event(funcname, args, kwargs)
        
        with self.back_lock:
            self.back.pointer = event
            self.back = event
            
            self.__release_latch()
    
    def wait(self, deadline=None, only=None):
        prev = self.front # don't need to lock because self.front never changes
        
        while True:
            if deadline == None or deadline == sys.maxsize:
                timeout = -1
            else:
                timeout = max(deadline - time.clock(), 0)
            
            if timeout == 0:
                got = self.latch.acquire(0)
            else:
                got = self.latch.acquire(1, timeout=timeout)
            
            if not got:
                raise self.Timeout
            
            this = prev.pointer
            
            with self.back_lock:
                if only == None or this.funcname in only:
                    prev.pointer = this.pointer # Bridge over this node
                    
                    if this == self.back: # If this was the back node
                        self.back = prev  # then make prev the back node.
                    else:                      # If this was NOT the back node
                        self.__release_latch() # then there are more to handle.
                    
                    return this.retval
                
                else:
                    if this != self.back: # Next iteration, check the next node
                        self.__release_latch()
            
            prev = this


class Actor:
    def __init__(self, **kwargs):
        self.evtq = EventQueue()
        
        super().__init__(**kwargs)
        
        _thread.start_new_thread(self._loop, ())
    
    def __getattr__(self, funcname):
        if funcname.startswith('as_'):
            def callme(*args, **kwargs):
                self.evtq.push(funcname[3:], args, kwargs)
            return callme
        else:
            raise AttributeError
    
    def _wait_next_event(self, deadline=None, only=None):
        # The EventQueue handles the tricky waiting logic
        event = self.evtq.wait(deadline=deadline, only=only)
        
        return self.__handle_event(event)
    
    def __handle_event(self, event_tuple):
        event, args, kwargs = event_tuple
        
        if event != 'dirty':
            print('%s.%s%s%s' % (self.__class__.__name__, event, args, kwargs))
        
        try:
            handler = getattr(self, '_as_' + event)
        except AttributeError:
            pass
        else:
            return handler(*args, **kwargs)

class Source(Actor):
    
    class UpdateDisplay(Exception): pass
    class Quit(Exception): pass
    
    def _get_size(self):
        #dispinf = pg.display.Info()
        #return (dispinf.current_w, dispinf.current_h)
        return(128,64)
    
    def __init__(self, **kwargs):
        self.buff_lock = _thread.allocate_lock()
        self._throttle_lock = _thread.allocate_lock()
        
        super().__init__(**kwargs)
    
    def unthrottle(self):
        try:
            self._throttle_lock.release()
        except RuntimeError:
            pass
    
    def _flip(self):
        self._throttle_lock.acquire()
        
        with self.buff_lock:
            self.fbuff, self.bbuff = self.bbuff, self.fbuff
        
        self.parent.as_dirty(self)
    
    def _as_quit(self):
        raise self.Quit()
    
    def _as_set_parent(self, parent):
        self.fbuff = pg.Surface(self._get_size())
        self.bbuff = pg.Surface(self._get_size())
        
        self.parent = parent


class Animator(): pass


class LinearAnimator(Animator):
    
    def __init__(self, start):
        self.start = self.at = start
        self.finished = True
    
    def aim(self, finish, duration=1):
        self.start = self.at
        self.finish = finish
        self.duration = duration
        self.finished = False
        self.t_start = None
    
    def step_to(self, t):
        if self.finished:
            return self.at
        
        if self.t_start == None:
            self.t_start = t
        
        frac = (t - self.t_start) / self.duration
            
        if frac < 1:
            self.at = tuple(self.start[i]*(1-frac) + self.finish[i]*frac for i in range(len(self.start)))
        else:
            self.at = self.finish
            self.finished = True
        
        return self.at        


class SdlWindow:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(self.__class__.__name__)
        self.buff = pygame.display.set_mode((128, 64))
    
    # This is a bit of a hack, because these clearly aren't asynchronous
    def as_add_source(self, source):
        self.source = source
        source.as_set_parent(self)
    
    def as_source_ready(self, source):
        pass
    
    def as_dirty(self, source):
        with self.source.buff_lock:
            self.buff.blit(self.source.fbuff, (0,0))
        
        pygame.display.flip()
        
        self.source.unthrottle()


class Compositor(Source):
    
    # Possible values for source.comp_stage
    UNREADY  = 1
    READY    = 2
    UNPERSON = 3
    
    def __init__(self, **kwargs):
        self.sources = []
        self.delta = (0,0)
        
        super().__init__(**kwargs)
    
    def _as_quit():
        try:
            for s in self.sources:
                s.as_quit()
        except RuntimeError:
            pass
        
        super()._as_quit()
    
    def _draw_frame(self):
        self.bbuff.fill((0,0,0))
        
        for s in self.sources:
            if s.comp_stage == self.UNREADY: continue
            
            with s.buff_lock:
                self.bbuff.blit(s.fbuff, (s.comp_x - self.view_x,
                                          s.comp_y - self.view_y))
            
            s.unthrottle()
        
        self._flip()
    
    def _as_dirty(self, source):
        if source.comp_stage == self.UNREADY:
            source.comp_stage = self.READY
            self._source_became_ready(source)
        
        raise Source.UpdateDisplay
    
    def _source_became_ready(self, source):
        pass


def StripCompositor(Compositor):
    
    def _as_set_sources(self, sources):
        for i in range(sources):
            s = sources[i]
            
            s.comp_x = 0
            s.comp_y = i * self._get_size[1]
            s.comp_stage = self.UNREADY
            
            s.as_set_parent(self)
        
        self.sources = sources
        self.view_animator = LinearAnimator((0, 0))
        self.mode = 0
        self.sources_reported_ready = 0
    
    def _as_select(self, mode):
        self.mode = mode
        self.foremost = self.sources[mode]
        
        new_xy = (self.foremost.comp_x, self.foremost.comp_y)
        self.view_animator.aim(new_xy)
        
        raise Source.UpdateDisplay
    
    def _as_input(self, kind, **kwargs):
        if kind == 'direction':
            newmode = self.mode + kwargs['dx']
            if 0 <= newmode < len(self.sources):
                self._as_select(newmode)
            
        else:
            self.foremost.as_input(kind, **kwargs)
    
    def _draw_frame(self):
        self.view_x, self.view_y = self.view_animator.step_to(time.clock())
        
        super()._draw_frame()
        
        if self.view_animator.finished:
            return None
        else:
            return 0
    
    def _loop(self):
        self._wait_next_event(only=['set_parent'])
        
        self._wait_next_event(only=['set_sources'])
        
        while len(s for s in self.sources if s.comp_stage == self.UNREADY) > 0:
            try:
                self._wait_next_event(only=['dirty'])
            except Source.UpdateDisplay:
                pass
        
        deadline = self._draw_frame()
        
        while True:
            try:
                self._wait_next_event(deadline)
            except (EventQueue.Timeout, Source.UpdateDisplay):
                deadline = self._draw_frame()


class StackCompositor(Compositor):
    
    def _remove_unpersons(self):
        kill = [s for s in self.sources if s.comp_stage == self.UNPERSON]
        self.sources = [s for s in self.sources if not s in kill]
        
        for k in kill:
            k.as_fully_offscreen()
    
    def _aim_animator(self):
        for s in reversed(self.sources):
            if s.comp_stage == self.READY:
                self.view_animator.aim((s.comp_x, s.comp_y))
                break
    
    def _as_set_parent(self, parent):
        super()._as_set_parent(parent)
        self.view_animator = LinearAnimator((0, 0))
    
    def _as_push(self, s):
        self._remove_unpersons()
        
        s.comp_x = sum([s._get_size()[0]+2 for s in self.sources])
        s.comp_y = 0
        s.comp_stage = self.UNREADY
        
        s.as_set_parent(self)
        self.sources.append(s)
    
    def _source_became_ready(self, source):
        if source != self.sources[0]:
            self._aim_animator()
    
    def _as_input(self, *args, **kwargs):
        for source in reversed(self.sources):
            if source.comp_stage != self.UNPERSON:
                source.as_input(*args, **kwargs)
                break
    
    def _as_pop(self, s):
        s.comp_stage = self.UNPERSON
        self._aim_animator()
        raise Source.UpdateDisplay
    
    def _draw_frame(self):
        self.view_x, self.view_y = self.view_animator.step_to(time.time())
        
        if self.view_animator.finished:
            self._remove_unpersons()
        
        super()._draw_frame()
        
        if self.view_animator.finished:
            return None # no deadline
        else:
            return 0
    
    def _loop(self):
        self._wait_next_event(only=['set_parent'])
        
        self._wait_next_event(only=['push'])
        
        try:
            self._wait_next_event(only=['dirty'])
        except Source.UpdateDisplay:
            pass
        
        deadline = self._draw_frame()
        
        while True:
            try:
                self._wait_next_event(deadline)
            except EventQueue.Timeout:
                deadline = self._draw_frame()
            except Source.UpdateDisplay: # just update the display, but first
                # flush all other pending 'dirty' events
                while True:
                    try:
                        self._wait_next_event(only=['dirty'], deadline=0)
                    except EventQueue.Timeout: break
                    except Source.UpdateDisplay: pass
                deadline = self._draw_frame()
                       
class CallStackCompositor(Compositor):
    
    def _as_push(self, new_source):
        self.sources.append(new_source)
        +
    
    def _loop(self):
        self._wait_next_event(only=['set_parent'])
        
        self._wait_next_event(only=[''])