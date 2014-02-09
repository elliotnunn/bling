from bling_core import *
import ctypes

class ST7575Server(Server):
    def __init__(self):
        self.libbuff=ctypes.CDLL('buff/libbuff.so')
        self.libbuff.init()
    
    def add_client(self, client):
        self.client = client
        client.parent_server = self
    
    def notify_client_dirty(self):
        client = self.client
        client.buffer_lock.acquire()
        self.libbuff.fling_buffer(client.get_buffer(True).get_buffer().raw) # sloooow??
        client.buffer_lock.release()
    
    def deinit(self):
        self.libbuff.deinit()