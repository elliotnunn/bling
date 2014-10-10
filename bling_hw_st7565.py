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
        client.buffer_lock.acquire()
        self.libbuff.fling_buffer(client.get_buffer(True)._pixels_address)
        client.buffer_lock.release()
    
    def deinit(self):
        self.libbuff.deinit()
