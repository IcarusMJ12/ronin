import pygame
from pygame.locals import *
from lie.context import Context as Context
import logging
from lie.input import InputHandler
import lie.objects

__all__=['PC', 'Oni']

ctx=Context.getContext()

class Actor(lie.objects.Actor):
    def moveToLocation(self, loc):
        dst_tile=ctx.world[loc]
        return self.moveToTile(dst_tile)

class Human(Actor):
    def __init__(self):
        super(Human, self).__init__()
        self.symbol='@'

class PC(Human):
    """The man himself."""
    def moveBlocked(self,tile):
        if(tile.actor and isinstance(tile.actor,Oni)):
            ctx.message_buffer.addMessage("You hit the oni and slay it.")
            ctx.enemies.remove(tile.actor)
            tile.actor=None
        else:
            ctx.message_buffer.addMessage("Thud! You run into a wall.")
    
    def moveToTile(self,dst_tile):
        ret=super(PC,self).moveToTile(dst_tile)
        if ret:
            ctx.worldview.center(ctx.worldview[dst_tile.loc].rect)
        return ret

class Oni(Actor):
    def __init__(self):
        super(Oni, self).__init__()
        self.symbol='o'
    
    def moveBlocked(self,tile):
        if(tile.actor==ctx.pc):
            ctx.message_buffer.addMessage("An oni hits you.  You die! [Enter or Space to quit]")
            death_handler=InputHandler()
            death_handler.addFunction(ctx.quit, K_RETURN)
            death_handler.addFunction(ctx.quit, K_SPACE)
            ctx.screen_manager.current.handlers.push(death_handler)
    
    def act(self):
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
