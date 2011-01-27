import pygame
from pygame.locals import *
from widgets import TextBlock
import logging
import globals
from input import InputHandler

class MessageBuffer(object):
    def __init__(self, rect, screen):
        self._tb=TextBlock(rect,'[more]')
        self._messages=''
        self._screen=screen
        self._screen.view.add(self._tb.sprites)
        self._handler=InputHandler()
        self._handler.addFunction(self.more, K_RETURN)
        self._handler.addFunction(self.more, K_SPACE)
        self._flushing=True
    
    def addMessage(self, message):
        self._messages+=message
        self._messages=self._tb.render(self._messages)
        self._screen.view.update()
        if self._messages:
            self._screen.handlers.push(self._handler)
            self._flushing=False
        return None

    def flush(self):
        if self._flushing:
            self._messages=''
            self._tb.flush()
    
    def more(self):
        self._messages=self._tb.render(self._messages)
        if not self._messages:
            self._screen.handlers.pop()
            self._flushing=True
        self._screen.view.update()
        return None
