import pygame
from pygame.locals import *
from context import Context as Context
import logging
from lie.input import InputHandler
import lie.objects

__all__=['PC', 'Mogwai']

ctx=Context.getContext()

class Actor(lie.objects.Actor):
    def moveToLocation(self, loc):
        dst_tile=ctx.world.getTile(loc.x,loc.y)
        return self.moveToTile(dst_tile)

class Human(Actor):
    """A typical Terran."""
    def __init__(self):
        self.symbol='@'

class PC(Human):
    """The man himself."""
    def moveBlocked(self,tile):
        if(tile.actor and isinstance(tile.actor,Mogwai)):
            ctx.message_buffer.addMessage("You hit the mogwai and slay it.")
            ctx.enemies.remove(tile.actor)
            tile.actor=None
        else:
            ctx.message_buffer.addMessage("Thud! You run into a wall.")
    
    def moveToTile(self,dst_tile):
        ret=super(PC,self).moveToTile(dst_tile)
        if ret:
            ctx.world.center(dst_tile.rect)
        return ret

class Mogwai(Actor):
    """A vicious and hungry demon without much intelligence or sense of direction."""
    def __init__(self):
        self.symbol='m'
    
    def moveBlocked(self,tile):
        if(tile.actor==ctx.pc):
            ctx.message_buffer.addMessage("A mogwai hits you.  You die! [Enter or Space to quit]")
            death_handler=InputHandler()
            death_handler.addFunction(ctx.quit, K_RETURN)
            death_handler.addFunction(ctx.quit, K_SPACE)
            ctx.screen_manager.current.handlers.push(death_handler)
    
    def move(self):
        choice=ctx.random.randint(0,5)
        if(choice==0):
            self.moveN()
        elif(choice==1):
            self.moveS()
        elif(choice==2):
            self.moveW()
        elif(choice==3):
            self.moveE()
        elif(choice==4):
            self.moveNE()
        elif(choice==5):
            self.moveSW()
