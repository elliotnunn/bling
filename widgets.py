import pygame
import pygame.freetype
import numpy

class Widget:
    def __init__(self, graf_props):
        if len(graf_props) == 4:
            self.depth, self.palette = graf_props[2:4]
        else:
            self.depth, self.palette = graf_props[0:2]
    
    def draw(self, buffer, at_xy=(0,0), t=0): raise NotImplementedError


class Scrollbar(Widget):
    def set_size(self, wh=(0,0)):
        self.w, self.h = wh
        self.surf = pygame.Surface(wh, depth=self.depth)
        self.surf.set_palette(self.palette)
    
    def set_position(self, pos, shown, of):
        t, b = pos * self.h // of, (pos+shown) * self.h // of
        
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
        
        self.surf = pygame.Surface((self.surf_w, self.surf_h), depth=self.depth)
        self.surf.set_palette(self.palette)
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
