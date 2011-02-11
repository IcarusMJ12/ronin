class Context(object):
    ctx=None

    def __init__(self):
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
