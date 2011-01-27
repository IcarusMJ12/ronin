import pygame
from input import InputHandlerManager

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
