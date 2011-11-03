#!/usr/bin/env python
#Copyright (c) 2011 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

__all__=['lookMode']

from pygame.locals import *

from context import Context
import input_handling
import globals
import logging
import abc

logger=logging.getLogger(__name__)

def _key(*args):
    def bindToKey(f):
        f.keys=list(args)
        return f
    return bindToKey

class AbstractLook(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, cursor):
        self.cursor=cursor
        self._backup=[None]
        ctx=Context.getContext()

        look_handler=input_handling.InputHandler()
        for method in [getattr(self,m) for m in dir(self) if callable(getattr(self,m))]:
            try:
                for key in method.keys:
                    if isinstance(key, tuple):
                        look_handler.addFunction(method, key[0], key[1])
                    else:
                        look_handler.addFunction(method, key)
                    logger.debug("Bound "+str(method)+" to "+str(key))
            except AttributeError:
                pass
        ctx.screen_manager.current.handlers.push(look_handler)

        self.message_buffer=ctx.message_buffer
        self.perception=ctx.pc.perception
        self.loc=ctx.pc.parent.loc
        self.original_loc=ctx.pc.parent.loc
        self.previous_loc=ctx.pc.parent.loc
        self.worldview=ctx.worldview
        (self.width,self.height)=(self.worldview.width-1,self.worldview.height-1)
        self.screen_manager=ctx.screen_manager
        self.ctx=ctx
        self.monster_index=-1
        self.len_monsters_keys=len(self.perception.monsters_keys)
    
    def _position(self):
        tile=self.worldview[self.loc]
        self.backup=tile.image
        tile.image=self.cursor
        if abs(self.loc[0]-self.previous_loc[0])>5 or abs(self.loc[1]-self.previous_loc[1])>5:
            self.worldview.center(self.worldview[self.loc].rect)
            self.previous_loc=self.loc
        self.screen_manager.current.view.draw()
    
    @abc.abstractmethod
    def _addMessage(self):
        pass

    def go(self):
        self._position()
        self._addMessage()

    @_key(K_y)
    def N(self):
        self.worldview[self.loc].image=self.backup
        self.loc=(self.loc[0],max(0,self.loc[1]-1))
        self.go()
    
    @_key(K_k)
    def NW(self):
        self.worldview[self.loc].image=self.backup
        self.loc=(max(0,self.loc[0]-1),max(0,self.loc[1]-1))
        self.go()

    @_key(K_n)
    def S(self):
        self.worldview[self.loc].image=self.backup
        self.loc=(self.loc[0],min(self.height,self.loc[1]+1))
        self.go()

    @_key(K_u)
    def W(self):
        self.worldview[self.loc].image=self.backup
        self.loc=(max(0,self.loc[0]-1),self.loc[1])
        self.go()

    @_key(K_b)
    def E(self):
        self.worldview[self.loc].image=self.backup
        self.loc=(min(self.width,self.loc[0]+1),self.loc[1])
        self.go()

    @_key(K_j)
    def SE(self):
        self.worldview[self.loc].image=self.backup
        self.loc=(min(self.width,self.loc[0]+1),min(self.height,self.loc[1]+1))
        self.go()
    
    @_key(K_RIGHTBRACKET, (K_EQUALS, (KMOD_SHIFT,)))
    def next(self):
        if self.len_monsters_keys:
            self.worldview[self.loc].image=self.backup
            self.monster_index=(self.monster_index+1)%self.len_monsters_keys
            self.loc=self.perception.monsters_keys[self.monster_index]
            self.go()

    @_key(K_LEFTBRACKET, K_MINUS)
    def previous(self):
        if self.len_monsters_keys:
            self.worldview[self.loc].image=self.backup
            self.monster_index=(self.monster_index-1)%self.len_monsters_keys
            self.loc=self.perception.monsters_keys[self.monster_index]
            self.go()

    @_key(K_q, K_ESCAPE)
    def quit(self):
        self.message_buffer.addMessage('')
        self.worldview[self.loc].image=self.backup
        self.worldview.center(self.worldview[self.original_loc].rect)
        self.screen_manager.current.handlers.pop()
        self.screen_manager.current.view.draw()

class Examine(AbstractLook):
    ACTIONS='<Available actions: (jkyubn[]+-); e(x)amine, (t)arget, (q)uit.>'

    def __init__(self, cursor):
        super(Examine, self).__init__(cursor)

    def _addMessage(self):
        items=[contents[1] for contents in self.perception.examineTile(self.loc)]
        cover=self.perception[self.loc].cover
        message=Examine.ACTIONS
        if len(items):
            if cover<1.0:
                message+='\nYou see here '
            else:
                message+='\nYou remember seeing '
            message+=', '.join(items)+'.'
        if globals.wizard_mode:
            message+='\n[cover: '+str(self.perception[self.loc].cover)+']'
        self.message_buffer.addMessage(message)
    
    @_key(K_x)
    def examine(self):
        message=Examine.ACTIONS
        items=[contents[2] for contents in self.perception.examineTile(self.loc)]
        if len(items):
            message+='\n'+'\n'.join(items)
        self.message_buffer.addMessage(message)
    
    @_key(K_t)
    def target(self):
        self.message_buffer.addMessage('<TODO>')

def lookMode():
    look=Examine(globals.font.render('X',True,(255,255,100)))

    look.go()
