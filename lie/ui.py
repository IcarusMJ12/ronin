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
    def __init__(self, input_handler):
        self.view=View()
        self.handlers=InputHandlerManager(input_handler)

class View(object):
    def __init__(self):
        self._groups=[]

    def draw(self):
        map(lambda x: x.draw(), self._groups)
    
    def add(self, group):
        self._groups.append(group)
