class TimeTest(bling_core.Client):
    def _setup(self, graf_props):
        self.font = pygame.freetype.Font("chicago.bdf")
    
    def _draw_frame(self, buffer=None, is_initial=False):
        buffer.fill((255,255,255), (0,0,self.width,self.height))
        
        self.font.render_to(buffer, (0,0), "t = %dms"%pygame.time.get_ticks())
        
        return self.t + 500
