# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import pygame.sprite
import pygame.rect
import logging
import globals

__all__=['TextLine', 'BoundedTextLine', 'StaticTextLine', 'TextBlock']

class TextLine(pygame.sprite.DirtySprite):
    def __init__(self, rect):
        super(TextLine, self).__init__()
        self._font=globals.font
        self.rect=rect
        self._text=''
        self.image=self._font.render('',True,(255,255,255))
        self.dirty=0
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        if self._text!=text:
            if bgcolor:
                self.image=self._font.render(text, True, color, bgcolor)
            else:
                self.image=self._font.render(text, True, color)
            self._text=text
            self.dirty=1

    def flush(self):
        self.render('')
    
class BoundedTextLine(TextLine):
    def __init__(self, rect):
        super(BoundedTextLine, self).__init__(rect)
        self._width=rect.w/globals.font.w
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        super(BoundedTextLine, self).render(text[:self._width], color, bgcolor)
        return text[self._width:]

class SmartTextLine(BoundedTextLine):
    def __init__(self, rect):
        super(SmartTextLine, self).__init__(rect)
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        message=text.split('\n')
        message[0]=super(SmartTextLine, self).render(message[0], color, bgcolor)
        if message[0]=='':
            message=message[1:]
        return '\n'.join(message)

class StaticTextLine(TextLine):
    def __init__(self, rect, text, color=(255,255,255), bgcolor=None):
        super(StaticTextLine, self).__init__(rect)
        super(StaticTextLine, self).render(text, color, bgcolor)
        self._image_vis=self.image
        super(StaticTextLine, self).render('',color,bgcolor)
        self._image_invis=self.image
        self.dirty=0
    
    def flush(self):
        if self.image==self._image_vis:
            self.image=self._image_invis
            self.dirty=1
    
    def render(self):
        if self.image==self._image_invis:
            self.image=self._image_vis
            self.dirty=1

class TextBlock(pygame.sprite.RenderUpdates):
    def __init__(self, rect, more_prompt=None):
        super(TextBlock, self).__init__()
        self._more=None
        if not more_prompt:
            self._lines=[SmartTextLine(pygame.rect.Rect(rect.x,rect.y+i,rect.w,globals.font.h)) for i in xrange(0,rect.h-globals.font.h+1,globals.font.h)]
        else:
            self._lines=[SmartTextLine(pygame.rect.Rect(rect.x,rect.y+i,rect.w,globals.font.h)) for i in xrange(0,rect.h-globals.font.h*2+1,globals.font.h)]
            self._lines.append(SmartTextLine(pygame.rect.Rect(rect.x,rect.y+(rect.h/globals.font.h-1)*globals.font.h,rect.w-len(more_prompt)*globals.font.w,globals.font.h)))
            self._more=StaticTextLine(pygame.rect.Rect(rect.x+rect.w-(len(more_prompt)*globals.font.w), rect.y+(rect.h/globals.font.h-1)*globals.font.h,len(more_prompt)*globals.font.w,globals.font.h), more_prompt)
            self.add(self._more)
        self.add(self._lines)
        self.viewport=globals.screen.subsurface(rect)
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        overflow=text
        for line in self._lines:
            overflow=line.render(overflow, color, bgcolor)
        if self._more:
            if overflow:
                self._more.render()
            else:
                self._more.flush()
        return overflow

    def flush(self):
        map(lambda x: x.flush(), self._lines)
        if self._more:
            self._more.flush()
    
    def draw(self):
        self.clear(self.viewport, globals.background)
        pygame.display.update(super(TextBlock, self).draw(self.viewport))
