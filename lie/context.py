class Context(object):
    ctx=None

    def __init__(self):
        self.pc = None
        self.enemies = None
        self.world = None
        self.worldview = None
        self.random = None
        self.screen_manager = None
        self.turn_manager = None
        self.message_buffer = None
    
    @classmethod
    def getContext(self):
        if(Context.ctx is None):
            Context.ctx = Context()
        return Context.ctx
    
    def __getstate__(self):
        state=dict([(key,self.__dict__[key]) for key in self.__dict__.keys() if key not in ('worldview','screen_manager','message_buffer')])
        for key in ('worldview','screen_manager','message_buffer'):
            state[key]=None
        return state
