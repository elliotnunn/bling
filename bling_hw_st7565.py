import pygame
import bling_core
import ctypes
import time

class ST7575Server(bling_core.Server):
    def __init__(self):
        self.libbuff=ctypes.CDLL('buff/libbuff.so')
        self.libbuff.init()
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
        self.notify_client_dirty()
    
    def notify_client_dirty(self):
        self.client.buff_sem.acquire()
        self.libbuff.fling_buffer(self.client.fbuff._pixels_address)
        self.client.buff_sem.release()
        #pygame.time.wait(150)
        self.client.server_allows_draw()
    
    def deinit(self):
        self.libbuff.deinit()
