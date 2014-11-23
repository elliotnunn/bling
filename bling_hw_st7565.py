import pygame
import bling_core
import ctypes
import time

class ST7575Server(bling_core.Server):
    def __init__(self):
        self.libbuff=ctypes.CDLL('buff/libbuff.so')
        self.libbuff.init()
        pygame.time.wait(500)
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
    
    def notify_client_dirty(self):
        client = self.client
        self.libbuff.fling_buffer(client.fbuff._pixels_address)
        pygame.time.wait(50)
        try: client.sync_sem.release()
        except: pass
    
    def deinit(self):
        self.libbuff.deinit()
