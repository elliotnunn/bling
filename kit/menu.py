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
import pygame.freetype

from core import Client
from ui.widget import TextBox, Scrollbar


class SexyMenu(Client):
    @classmethod
    def mkitem(cls, label, arrowed=False, handler=None, *args, **kwargs):
        return (label, arrowed, handler, args, kwargs)
        # this is the format for the tuples in self.items
    
    def _setup(self, graf_props, title="", menu_items=[], menu_isroot=False, **kwargs):
        # boilerplate
        self.font = pygame.freetype.Font("chicago.bdf")
        self.font.origin = True
        
        # flesh these out a bit
        self.title, self.items, self.isroot = title, menu_items, menu_isroot
        
        self.scrollbar_w = 0 #if len(self.items) <= 4 else 7
        
        # the title is obvious
        if self.isroot:
            title_decor = bling_widgets.TextBox.DECOR_NONE
        else:
            title_decor = bling_widgets.TextBox.DECOR_LARROW
        
        self.title_widget = bling_widgets.TextBox(self.graf_props)
        self.title_widget.set_content(self.title.upper(),
                                      self.font,
                                      title_decor,
                                      (self.width, 13))
        self.title_widget.set_oflow(bling_widgets.TextBox.OFLOW_ELLIPSIS)
        self.title_widget.xy_in_parent = (0, -1)
        
        self.widgets.append(self.title_widget)
        
        # widgets for items, max of 4
        self.item_widgets = []
        for i in range(0, min(4, len(self.items))):
            w = bling_widgets.TextBox(self.graf_props)
            self.item_widgets.append(w)
        self.widgets += self.item_widgets
        
        # do we need a scrollbar?
        if self.scrollbar_w > 0:
            scrollbar = bling_widgets.Scrollbar(self.graf_props)
            scrollbar.set_size((self.scrollbar_w-3, self.height - 12))
            scrollbar.set_position(0, 4, len(self.items))
            scrollbar.xy_in_parent = (self.width - 4, 12)
            
            self.widgets.append(scrollbar)
            self.scrollbar_widget = scrollbar
        
        self._set_scroll(0)
        self._set_selection(0)
    
    def _set_selection(self, to):
        if to < 0 or to >= len(self.items): return
        self.selection = to
        
        if to < self.scroll:
            self._set_scroll(to)
        elif self.scroll + 3 < to:
            self._set_scroll(to - 3)
        
        for i in range(self.scroll, min(len(self.items), self.scroll+4)):
            sel = i == self.selection
            wgt = self.item_widgets[i % 4]
            
            if sel:
                oflow = bling_widgets.TextBox.OFLOW_SCROLL
            else:
                oflow = bling_widgets.TextBox.OFLOW_ELLIPSIS
                
            wgt.set_hilite(sel)
            wgt.set_oflow(oflow, self.t)
    
    def _set_scroll(self, to):
        if not hasattr(self, "scroll"): self.scroll = None
        frm, self.scroll = self.scroll, to
        
        if self.scrollbar_w > 0:
            self.scrollbar_widget.set_position(to, 4, len(self.items))
        
        if frm == None: # first call, scroll to zero
            newly_shown = range(0, 4)
        elif to == frm + 1: # scroll one step down
            newly_shown = [frm + 4]
        elif to == frm - 1: # scroll one step upp
            newly_shown = [to]
        else:
            newly_shown = []
        
        for i in range(to, min(len(self.items), self.scroll+4)):
            wgt = self.item_widgets[i % 4]
            
            y = 12 + 13 * (i - to)
            wgt.xy_in_parent = (0, y)
            
            if i in newly_shown:
                itm = self.items[i]
                wh = (self.width - self.scrollbar_w, 13)
                if itm[1]: # arrowed?
                    decor = bling_widgets.TextBox.DECOR_RARROW
                else:
                    decor = bling_widgets.TextBox.DECOR_NONE 
                
                wgt.set_content(itm[0], self.font, decor, wh)
    
    # This just straightforwardly wraps a few widgets
    def _draw_frame(self, surf, first):
        if first: surf.fill((255,255,255))
        
        self._draw_widgets(surf)
        
        # Horizontal divider under title
        surf.fill((0,0,0), (0, 10, self.width, 1))
        
        # Vertical divider left of the scrollber, if any
        if self.scrollbar_w > 0:
                x = self.width - self.scrollbar_w + 1
                surf.fill((0,0,0), (x, 10, 1, self.height - 10))
    
    def _event(self, event):
        scroll_events = {"up": -1, "down": 1}
        if event in scroll_events:
            delta = scroll_events[event]
            
            with self.big_lock:
                self._set_selection(self.selection + delta)
            
            return True
        
        if event == "ok":
            with self.big_lock:
                label, arrow, handler, args, kwargs = self.items[self.selection]
            
            if hasattr(handler, "get_buffer"): # quacks like a Client
                new_client = handler(self.graf_props, *args, **kwargs)
                self.parent_server.add_client(new_client)
            else: # handler is presumably a function
                handler(*args, **kwargs) # easy as that
            
            return False
        
        if event == "back" and self.isroot:
            return False

# Museum piece predating widget classes. Use SexyMenu instead.
class ProtoMenu(Client): # a bit of a mess, and poorly optimised
    def _draw_frame(self, buffer, is_initial):
        blk = (0, 0, 0)
        wht = (255, 255, 255)
        blk = (127, 127, 127)
        #blk, wht = wht, blk # cheeky
        
        # draw the title
        pygame.draw.rect(buffer, wht, (0, 0, self.width, self.titlearea_height))
        title_width = self.font.get_rect(self.title)[2]
        self.font.render_to(buffer, ((self.width - title_width) // 2, 9), self.title, fgcolor=blk, bgcolor=wht)
        
        # draw a separating line after 10 pixels
        pygame.draw.line(buffer, blk, (0, self.titlearea_height - 2), (self.width, self.titlearea_height - 2))
        # equals 12 pixels, leaving room for 4 13-px lines of chicago
        
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
                x = self.view_width - 6
                pygame.draw.line(buffer, tc, (x, y+4), (x+2, y+6), 2)
                pygame.draw.line(buffer, tc, (x, y+8), (x+2, y+6), 2)
        
        if self.scrollbar_visible:
            pygame.draw.rect(buffer, wht,(self.view_width, self.titlearea_height, self.scrollbararea_width, self.view_height))
            pygame.draw.line(buffer, blk, (self.view_width + 1, self.titlearea_height - 1), (self.view_width + 1, self.height))
            pygame.draw.rect(buffer, blk, (self.view_width + 3, self.scrollbar_pos + self.titlearea_height, self.scrollbararea_width - 3, self.scrollbar_height))
        
        #return -1
    
    #def __init__(self, graf_props, items, title="untitled"):
    def _setup(self, graf_props, **kwargs):
        # will NOT change
        title = kwargs["title"]
        if title == "": title = "untitled"
        self.title = title.upper()
        
        self.items = kwargs["items"]
        # list of tuples: ("Artists>>>", a function)
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
            self.scrollbararea_width = 7
            self.scrollbar_height = max(10, self.view_height * self.view_height / self.content_height)
        
        self.view_width = self.view_width - self.scrollbararea_width
                
        # will change:
        self.scroll = 0
        self.selected = 0
        self.scrollbar_pos = 0
        
        #Client.__init__(self, graf_props)
        
    def _event(self, event):
        if event == "back":
            self.parent_server.remove_client(self)
            return False
        
        elif event == "ok":
            func = self.items[self.selected][1]
            if func != None: func(self.parent_server)
            return False
        
        elif event == "up":
            if self.selected > 0:
                self.selected -= 1
                if self.scrollbar_visible:
                    max_scroll = self.selected * self.item_height
                    if self.scroll > max_scroll: self.scroll = max_scroll
                
        elif event == "down":
            if self.selected < self.item_count - 1:
                self.selected += 1
                if self.scrollbar_visible:
                    min_scroll = (self.selected + 1) * self.item_height - self.view_height
                    if self.scroll < min_scroll: self.scroll = min_scroll
        
        else:
            return None
        
        if self.scrollbar_visible:
            scrollbar_max = self.view_height - self.scrollbar_height + 1
            scroll_max = self.content_height - self.view_height
            self.scrollbar_pos = scrollbar_max * self.scroll / scroll_max
        
        return True
