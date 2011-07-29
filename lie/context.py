class Context(object):
    ctx=None

    def __init__(self):
        self.pc = None
        self.enemies = None
        self.world = None
        self.worldview = None
        self.random = None
        self.screen_manager = None
    
    @classmethod
    def getContext(self):
        if(Context.ctx is None):
            Context.ctx = Context()
        return Context.ctx
