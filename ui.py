import pygame

class ScreenManager(object):
    def __init__(self, screen):
        self._screens=[screen]

    def push(self, screen):
        self._screens.insert(0,screen)
    
    def pop(self):
        assert(len(self._screens)>1)
        self._screens.pop(0)
    
    def _current(self):
        return self._screens[0]

    current = property(_current, None)

class Screen(object):
    def __init__(self, input_handler, context):
        self._ctx=context
        self.view=View(self._ctx.screen, self._ctx.background)
        self.handlers=InputHandlerManager(input_handler)

class View(object):
    def __init__(self, pygame_screen, background):
        self._group=pygame.sprite.RenderClear()
        self._screen=pygame_screen
        self._background=background

    def update(self):
        self._group.clear(self._screen, self._background)
        self._group.draw(self._screen)
        pygame.display.update()
    
    def add(self, *sprite):
        self._group.add(*sprite)

class InputHandlerManager(object):
    def __init__(self, handler):
        self._input_handlers=[handler]
    
    def push(self, handler):
        self._input_handlers.insert(0,handler)
    
    def pop(self):
        assert(len(self._input_handlers)>1)
        self._input_handlers.pop(0)
    
    def handle(self,event):
        handler=self._input_handlers[0]
        f=handler.getFunction(event.key, event.mod)
        if f:
            return f()
        return None

class InputHandler(object):
    def __init__(self):
        self.funcs={}

    def addFunction(self, function, key, mods=(0,)):
        if key not in self.funcs.keys():
            self.funcs[key]={}
        self.funcs[key][mods]=function
    
    def getFunction(self, key, mod):
        try:
            mod_map = self.funcs[key]
        except KeyError:
            return None
        print mod_map
        for k,f in mod_map.items():
            match=True
            cum_mod=0
            for m in k:
                cum_mod|=m
                if m and not m & mod:
                    match=False
                    break
            if mod & ~cum_mod:
                match=False
            if match:
                return f
        return None
