import pygame.sprite
import pygame.rect
import logging

__all__=['TextLine', 'BoundedTextLine', 'StaticTextLine', 'TextBlock']

class TextLine(pygame.sprite.DirtySprite):
    def __init__(self, rect, monofont):
        super(TextLine, self).__init__()
        self._font=monofont
        self.rect=rect
        self._text=''
        self.image=self._font.render('',True,(255,255,255))
        self.dirty=0
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        logging.info(id(self).__repr__()+' rendering '+self._text+' '+text)
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
    def __init__(self, rect, monofont):
        super(BoundedTextLine, self).__init__(rect, monofont)
        self._width=rect.w/monofont.w
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        super(BoundedTextLine, self).render(text[:self._width], color, bgcolor)
        return text[self._width:]

class SmartTextLine(BoundedTextLine):
    def __init__(self, rect, monofont):
        super(SmartTextLine, self).__init__(rect, monofont)
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        message=text.split('\n')
        message[0]=super(SmartTextLine, self).render(message[0], color, bgcolor)
        if message[0]=='':
            message=message[1:]
        return '\n'.join(message)

class StaticTextLine(TextLine):
    def __init__(self, rect, monofont, text, color=(255,255,255), bgcolor=None):
        super(StaticTextLine, self).__init__(rect, monofont)
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

class TextBlock(object):
    def __init__(self, rect, monofont, more_prompt=None):
        self._more=None
        if not more_prompt:
            self._lines=[SmartTextLine(pygame.rect.Rect(rect.x,rect.y+i,rect.w,monofont.h), monofont) for i in xrange(0,rect.h-monofont.h+1,monofont.h)]
        else:
            self._lines=[SmartTextLine(pygame.rect.Rect(rect.x,rect.y+i,rect.w,monofont.h), monofont) for i in xrange(0,rect.h-monofont.h*2+1,monofont.h)]
            self._lines.append(SmartTextLine(pygame.rect.Rect(rect.x,rect.y+(rect.h/monofont.h-1)*monofont.h,rect.w-len(more_prompt)*monofont.w,monofont.h),monofont))
            self._more=StaticTextLine(pygame.rect.Rect(rect.x+rect.w-(len(more_prompt)*monofont.w), rect.y+(rect.h/monofont.h-1)*monofont.h,len(more_prompt)*monofont.w,monofont.h),monofont, more_prompt)
    
    def render(self, text, color=(255,255,255), bgcolor=None):
        overflow=text
        for line in self._lines:
            overflow=line.render(overflow, color, bgcolor)
        if overflow and self._more:
            self._more.render()
        return overflow

    def flush(self):
        map(lambda x: x.flush(), self._lines)
        if self._more:
            self._more.flush()
    
    def getSprites(self):
        if self._more:
            return self._lines+[self._more]
        return self._lines

    sprites=property(getSprites,None)
