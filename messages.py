import pygame
from pygame.locals import *
from context import Context
from widgets import TextBlock
import logging
from ui import InputHandler

class MessageBuffer(object):

    def __init__(self, rect, font, screen):
        self._tb=TextBlock(rect,font,'[more]')
        self._messages=''
        self._screen=screen
        self._screen.view.add(self._tb.sprites)
        self._handler=InputHandler()
        self._handler.addFunction(self.more, K_RETURN)
        self._handler.addFunction(self.more, K_ESCAPE)
    
    def addMessage(self, message):
        self._messages+=message
        self._messages=self._tb.render(self._messages)
        if self._messages:
            self._screen.view.update()
            self._screen.handlers.push(self._handler)

    def flush(self):
        self._messages=''
        self._tb.flush()
    
    def more(self):
        self._messages=self._tb.render(self._messages)
        if not self._messages:
            self._screen.handlers.pop()
        else:
            self._screen.view.update()
