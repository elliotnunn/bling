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
import numpy

from plumbing import Source, SexySource


class SexyMenu(SexySource):
    @classmethod
    def itm(cls, label, arrowed=False, handler=None, *args, **kwargs):
        return (label, arrowed, handler, args, kwargs)
        # this is the format for the tuples in self.items
    
    def _setup(self, title="", menu_items=[], menu_isroot=False, **kwargs):
        # boilerplate
        pygame.freetype.init()
        self.font = pygame.freetype.Font("Chicago-12.bdf")
        self.font.origin = True
        
        
        self.scroll = None
        
        
        
        # flesh these out a bit
        self.title, self.items, self.isroot = title, menu_items, menu_isroot
        
        # the title is obvious
        if self.isroot:
            title_decor = TextBox.DECOR_NONE
        else:
            title_decor = TextBox.DECOR_LARROW
        
        self.title_widget = TextBox()
        self.title_widget.set_content(self.title.upper(),
                                      self.font,
                                      title_decor,
                                      (self.size[0], 13))
        self.title_widget.set_oflow(TextBox.OFLOW_ELLIPSIS)
        self.title_widget.xy_in_parent = (0, -1)
        
        self.widgets.append(self.title_widget)
        
        # widgets for items, max of max_disp_items
        self.max_disp = (self.size[1] - 12)//13
        self.scrollbar_w = 0 if len(self.items) <= self.max_disp else 7
        
        self.item_widgets = []
        for i in range(0, min(self.max_disp, len(self.items))):
            w = TextBox()
            self.item_widgets.append(w)
        self.widgets += self.item_widgets
        
        # do we need a scrollbar?
        if self.scrollbar_w > 0:
            scrollbar = Scrollbar()
            scrollbar.set_size((self.scrollbar_w-3, self.size[1] - 12))
            scrollbar.set_position(pos=0, wind=self.max_disp, total=len(self.items))
            scrollbar.xy_in_parent = (self.size[0] - 4, 12)
            
            self.widgets.append(scrollbar)
            self.scrollbar_widget = scrollbar
        
        self._set_scroll(0)
        self._set_selection(0)
    
    def _set_selection(self, to):
        if to < 0 or to >= len(self.items): return
        self.selection = to
        
        if to < self.scroll:
            self._set_scroll(to)
        elif self.scroll + self.max_disp <= to:
            self._set_scroll(to - self.max_disp + 1)
        
        for i in range(self.scroll, min(len(self.items), self.scroll+self.max_disp)):
            sel = i == self.selection
            wgt = self.item_widgets[i % self.max_disp]
            
            if sel:
                oflow = TextBox.OFLOW_SCROLL
            else:
                oflow = TextBox.OFLOW_ELLIPSIS
            
            wgt.set_hilite(sel)
            wgt.set_oflow(oflow, self.t)
    
    def _set_scroll(self, to):
        frm, self.scroll = self.scroll, to
        
        if self.scrollbar_w > 0:
            self.scrollbar_widget.set_position(pos=to, wind=4, total=len(self.items))
        
        if frm == None: # first call, scroll to zero
            newly_shown = range(0, min(self.max_disp, len(self.items)))
        elif to == frm + 1: # scroll one step down
            newly_shown = [frm + self.max_disp]
        elif to == frm - 1: # scroll one step upp
            newly_shown = [to]
        else:
            newly_shown = []
        
        for i in range(to, min(len(self.items), self.scroll+self.max_disp)):
            wgt = self.item_widgets[i % self.max_disp]
            
            y = 12 + 13 * (i - to)
            wgt.xy_in_parent = (0, y)
            
            if i in newly_shown:
                itm = self.items[i]
                wh = (self.size[0] - self.scrollbar_w, 13)
                if itm[1]: # arrowed?
                    decor = TextBox.DECOR_RARROW
                else:
                    decor = TextBox.DECOR_NONE 
                
                wgt.set_content(itm[0], self.font, decor, wh)
    
    # This just straightforwardly wraps a few widgets
    def _draw_frame(self, surf, first):
        if first: surf.fill((255,255,255))
        
        self._draw_widgets(surf)
        
        # Horizontal divider under title
        surf.fill((0,0,0), (0, 10, self.size[0], 1))
        
        # Vertical divider left of the scrollber, if any
        if self.scrollbar_w > 0:
                x = self.size[0] - self.scrollbar_w + 1
                surf.fill((0,0,0), (x, 10, 1, self.size[1] - 10))
    
    def _as_input(self, kind, kinetic='', dx=0, dy=0, **k):
        if kind == 'direction' and dy != 0 and kinetic != 'in':
            self._set_selection(self.selection - dy)
        
        elif kind == 'select':
            label, arrow, handler, handler_args, handler_kwargs = self.items[self.selection]
            
            handler(*handler_args, **handler_kwargs)


class Widget:
    def draw(self, buffer, at_xy=(0,0), t=0): raise NotImplementedError


class Scrollbar(Widget):
    def set_size(self, wh=(0,0)):
        self.w, self.h = wh
        self.surf = pygame.Surface(wh)
    
    def set_position(self, pos=0, wind=1, total=2):
        t, b = pos * self.h // total, (pos+wind) * self.h // total
        
        self.surf.fill((255,255,255))
        self.surf.fill((0,0,0), rect=(0, t, self.w, b-t))
    
    def draw(self, surf, at_xy=(0,0), t=0):
        surf.blit(self.surf, at_xy)


class TextBox(Widget):
    OFLOW_TRUNCATE = 0
    OFLOW_ELLIPSIS = 1
    OFLOW_SCROLL   = 2
    HILITE_OFF     = False
    HILITE_ON      = True
    DECOR_NONE     = 0
    DECOR_RARROW   = 1
    DECOR_LARROW   = 2
    
    SCROLL_DELAY_MS = 1500
    SCROLL_STEP_PX = 1
    SCROLL_STEP_MS = 80
    SCROLL_GOES_AROUND = 3
    
    ELLIPSIS_W = 11
    
    def set_content(self, text, font, decor, widget_wh):
        self.widget_w, self.widget_h = widget_wh
        self.fgc, self.bgc = (0, 0, 0), (255, 255, 255)
        self.hilite, self.oflow = self.HILITE_OFF, self.OFLOW_TRUNCATE
        self.decor = decor
        
        # how wide will the text be when drawn? (being generous)
        text_rect = font.get_rect(text)
        self.text_full_w = text_rect[0] + text_rect[2] + 1
        
        # how wide can be accommodate, accounting for decoration?
        if decor == self.DECOR_NONE:     text_margins = 0, 0
        elif decor == self.DECOR_LARROW: text_margins = 12, 0
        elif decor == self.DECOR_RARROW: text_margins = 0, 8
        self.text_margin_l, self.text_margin_r = text_margins
        
        self.max_text_disp_w = self.widget_w - sum(text_margins)
        
        if self.text_full_w <= self.max_text_disp_w:
            self.surf_w = self.text_full_w
        else: # this is the gap that will appear if the text scrolls
            self.surf_w = self.text_full_w + 30 # aesthetic crap
            self.surf_w -= self.surf_w % self.SCROLL_STEP_PX # even multiple
        
        self.surf_h = self.widget_h
        
        self.surf = pygame.Surface((self.surf_w, self.surf_h))
        self.surf.fill(self.bgc)
        
        font.render_to(self.surf,
                       (text_rect[0], 10),
                       None, # string from get_rect
                       fgcolor=self.fgc, bgcolor=self.bgc)
        
        # figure out how many whole letters we can display before an ellipsis
        #print("%d > %d ?" % (self.text_full_w, self.max_text_disp_w))
        if self.text_full_w > self.max_text_disp_w:
            arr = pygame.surfarray.pixels2d(self.surf)
            
            self.ellipsis_x = self.max_text_disp_w - self.ELLIPSIS_W
            have_had_success = False
            
            while True:
                col1 = arr[self.ellipsis_x - 1] & 1
                col2 = arr[self.ellipsis_x - 2, 7:10] & 1
                
                success = numpy.all(col1 == 1) and numpy.all(col2 == 1)
                if success:
                    have_had_success = True
                elif not success and have_had_success:
                    self.ellipsis_x += 1
                    break
                
                self.ellipsis_x -= 1
        
        else:
            self.ellipsis_x = 0 # indicates that the text fits
    
    def set_hilite(self, to):
        if to != self.hilite:
            arr = pygame.surfarray.pixels2d(self.surf)
            arr ^= 0x00ffffff
            
            self.fgc, self.bgc = self.bgc, self.fgc
            
            self.hilite = to
    
    def set_oflow(self, to, t=0):
        if self.ellipsis_x == 0:
            to = self.OFLOW_TRUNCATE
        
        if to == self.OFLOW_SCROLL and self.oflow != self.OFLOW_SCROLL:
            self.oflow_scroll_start_t = t + self.SCROLL_DELAY_MS
            self.oflow_scroll_x = 0
        
        self.oflow = to
    
    def __draw_text(self, dest, dest_rect, src, src_x1, bgc=None):
        dbg = False #self.oflow == self.OFLOW_TRUNCATE
        
        dest_x1, dest_y, dest_w, dest_h = dest_rect
        src_w1 = min(src.get_width() - src_x1, dest_w)
        
        if dbg:
            print("(dest_x1=%d, dest_y=%d) (src_x1=%d, 0, src_w1=%d, dest_h=%d)" %
                (dest_x1, dest_y, src_x1, src_w1, dest_h))
        dest.blit(src, (dest_x1, dest_y), area=(src_x1, 0, src_w1, dest_h))
        
        # Did we reach the right edge of the drawing area?
        # Either draw the text from the beginning or fill with bg colour
        if src_w1 < dest_w:
            src_x2 = 0
            src_w2 = dest_w - src_w1
            dest_x2 = src_w1
            
            if bgc == None:
                if dbg:
                    print("(dest_x2=%d dest_y=%d) (src_x2=%d, 0, src_w2=%d, dest_h=%d)" %
                    (dest_x2, dest_y, src_x2, src_w2, dest_h))
                dest.blit(src, (dest_x2, dest_y), area=(src_x2, 0, src_w2, dest_h))
            else:
                pass
                #dest.fill(bgc, (dest_x2, dest_y, src_w2, dest_h))
        if dbg:
            print("--")
    
    def draw(self, surf, dest_xy, t):
        dest_x, dest_y = dest_xy
        dest_w, dest_h = self.widget_w, self.widget_h
        
        surf.fill(self.bgc, (dest_x, dest_y, dest_w, dest_h))
        
        # draw the decoration!
        
        if self.decor != self.DECOR_NONE:
            y = dest_y + 5 # tip y
            
            if self.decor == self.DECOR_LARROW:
                x = dest_x + 4 # tip x
                l = 1# tail direction
                y = dest_y + 6 # tip y
                
            elif self.decor == self.DECOR_RARROW:
                x = dest_x + dest_w - 4
                l = -1
                y = dest_y + 6
            
            pygame.draw.line(surf, self.fgc, (x + 2*l, y-2), (x, y), 2)
            pygame.draw.line(surf, self.fgc, (x + 2*l, y+2), (x, y), 2)
        
        display_as = self.oflow
        
        # Scroll stepping
        if self.oflow == self.OFLOW_SCROLL:
            if self.oflow_scroll_x == 0 and t < self.oflow_scroll_start_t:
                # waiting for scroll to begin
                display_as = self.OFLOW_ELLIPSIS
                nxt = self.oflow_scroll_start_t
            else:
                # Step forwards
                self.oflow_scroll_x += self.SCROLL_STEP_PX
                self.oflow_scroll_x %= self.surf_w
                nxt = t + self.SCROLL_STEP_MS
            
            #if self.oflow_scroll_x >= self.text_full_w: # Hit the end
            #    display_as = self.oflow = self.OFLOW_ELLIPSIS
        
        # Now actually handle the three cases
        
        if display_as == self.OFLOW_TRUNCATE:
            dest_rect = (dest_x + self.text_margin_l, dest_y,
                         self.max_text_disp_w,        dest_h)
            
            self.__draw_text(surf, dest_rect, self.surf, 0, bgc=self.bgc)
        
        elif display_as == self.OFLOW_ELLIPSIS:
            dest_rect = (dest_x + self.text_margin_l, dest_y,
                         self.ellipsis_x,             dest_h)
            
            self.__draw_text(surf, dest_rect, self.surf, 0, bgc=self.bgc)
            
            clear_w = self.max_text_disp_w - self.ellipsis_x
            clear_x = dest_x + dest_w - self.text_margin_r - clear_w
            
            #surf.fill(self.bgc, rect=(clear_x, dest_y, clear_w, dest_h))
            
            x = dest_x + self.text_margin_l + self.ellipsis_x
            for i in range(3):
                surf.fill(self.fgc, rect=(x + 4*i, dest_y+8, 2, 2))
        
        elif display_as == self.OFLOW_SCROLL:
            dest_rect = (dest_x + self.text_margin_l, dest_y,
                         self.max_text_disp_w,        dest_h)
            
            self.__draw_text(surf, dest_rect, self.surf,
                             self.oflow_scroll_x, bgc=None)
        
        if self.oflow == self.OFLOW_SCROLL:
            return nxt
