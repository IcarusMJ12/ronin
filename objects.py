#Copyright (c) 2011 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import pygame
from pygame.locals import *
from lie.context import Context as Context
import logging
from lie.input_handling import InputHandler
import lie.objects
from lie.objects import State

__all__=['PC', 'Oni']

class Actor(lie.objects.Actor):
    def moveToLocation(self, loc):
        ctx=Context.getContext()
        dst_tile=ctx.world[loc]
        return self.moveToTile(dst_tile)

class Human(Actor):
    def __init__(self):
        super(Human, self).__init__()
        self.short_description='a human'
        self.symbol='@'

class PC(Human):
    """A samurai, armed with a katana and a yumi."""
    def __init__(self):
        super(PC, self).__init__()
        self.short_description='a rugged samurai'

    def moveBlocked(self,tile):
        ctx=Context.getContext()
        if(tile.actor and isinstance(tile.actor,Oni)):
            ctx.message_buffer.addMessage("You hit the oni and slay it.")
            ctx.enemies.remove(tile.actor)
            tile.actor=None
        else:
            ctx.message_buffer.addMessage("Thud! You run into a wall.")
    
    def moveToTile(self,dst_tile):
        ret=super(PC,self).moveToTile(dst_tile)
        ctx=Context.getContext()
        if ret:
            ctx.worldview.center(ctx.worldview[dst_tile.loc].rect)
        return ret

class Oni(Actor):
    """An ugly, fanged humanoid with a mean disposition, wielding a tetsubo."""
    def __init__(self):
        super(Oni, self).__init__()
        self.short_description='an oni'
        self.symbol='o'
        #self.state=State.Unaware
        self.state=State.Hostile
    
    def moveBlocked(self,tile):
        ctx=Context.getContext()
        if(tile.actor==ctx.pc):
            ctx.message_buffer.addMessage("An oni hits you.  You die! [Enter or Space to quit]")
            death_handler=InputHandler()
            death_handler.addFunction(ctx.quit, K_RETURN)
            death_handler.addFunction(ctx.quit, K_SPACE)
            ctx.screen_manager.current.handlers.push(death_handler)
    
    def act(self):
        ctx=Context.getContext()
        choice=ctx.random.randint(0,5)
        if(choice==0):
            self.moveN()
        elif(choice==1):
            self.moveS()
        elif(choice==2):
            self.moveNW()
        elif(choice==3):
            self.moveE()
        elif(choice==4):
            self.moveW()
        elif(choice==5):
            self.moveSE()
