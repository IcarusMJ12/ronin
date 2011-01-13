import pygame

class Context(object):
    ctx=None

    def __init__(self):
        self.FONT_SIZE = None
        self.CELL_WIDTH = None
        self.CELL_HEIGHT = None
        self.font = None
        self.screen = None
        self.background = None
        self.group = None
        self.pc = None
        self.enemies = None
        self.world = None
        self.random = None
    
    @classmethod
    def getContext(self):
        if(Context.ctx is None):
            Context.ctx = Context()
        return Context.ctx
