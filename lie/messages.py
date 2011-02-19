import pygame
from pygame.locals import *
from pygame.rect import Rect
from widgets import TextBlock
import logging
from input import InputHandler
import globals

class MessageBuffer(object):
    def __init__(self, screen):
        self._tb=TextBlock(Rect(0,0,globals.screen_width,globals.message_buffer_height),'[more]')
        self._messages=''
        self._screen=screen
        self._screen.view.add(self._tb)
        self._handler=InputHandler()
        self._handler.addFunction(self.more, K_RETURN)
        self._handler.addFunction(self.more, K_SPACE)
        self._is_read=False
    
    def addMessage(self, message):
        self.flush()
        self._messages+=message
        self._messages=self._tb.render(self._messages)
        self._tb.draw()
        self._is_read=False
        if self._messages:
            self._screen.handlers.push(self._handler)
        return None

    def flush(self):
        if self._is_read:
            self._messages=''
            self._tb.render(self._messages)
        self._tb.draw()

    def setIsRead(self,read):
        self._is_read=read
    
    is_read=property(None,setIsRead)
    
    def more(self):
        self._messages=self._tb.render(self._messages)
        if not self._messages:
            self._screen.handlers.pop()
        self._tb.draw()
        return None

    def draw(self):
        self._tb.draw()
