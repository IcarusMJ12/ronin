class Context(object):
    ctx=None

    def __init__(self):
        self.FONT_SIZE = None
        self.CELL_WIDTH = None
        self.CELL_HEIGHT = None
        self.MESSAGE_BUFFER_HEIGHT = None
        self.GRID_OFFSET = None
        self.SCREEN_WIDTH = None
        self.font = None
        self.screen = None
        self.background = None
        self.group = None
        self.pc = None
        self.enemies = None
        self.world = None
        self.random = None
        self.quit = None
    
    @classmethod
    def getContext(self):
        if(Context.ctx is None):
            Context.ctx = Context()
        return Context.ctx
