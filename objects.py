import pygame
import copy
from context import Context as Context
from exceptions import NotImplementedError
import sys
import logging

ctx=Context.getContext()

class BaseObject(object):
    """All in-game objects should derive from this or one of its children."""

class Terrain(BaseObject):
    """A terrain feature."""
    def __init__(self, passable_by):
        self.passable_by=passable_by
    
    def isPassableBy(self, actor):
        if self.passable_by is None:
            return False
        return isinstance(actor,self.passable_by)

class Floor(Terrain):
    """A floor that can be walked on."""
    def __init__(self):
        Terrain.__init__(self,Actor)
        self.symbol='.'

class Wall(Terrain):
    """An impassable wall, that may, however, be mined."""
    def __init__(self):
        Terrain.__init__(self,None)
        self.symbol='#'

class Actor(BaseObject):
    """Any object that can act of its own volition."""
    def moveToTile(self, tile):
        if(tile.isPassableBy(self)):
            tile.actor=self
            self.parent.actor=None
            self.parent=tile
            return True
        else:
            self.moveBlocked(tile)
            return False
    
    def moveBlocked(self,tile):
        raise NotImplementedError()
    
    def moveN(self):
        self.moveToOffset(0,-1)
    
    def moveS(self):
        self.moveToOffset(0,1)

    def moveW(self):
        self.moveToOffset(-1,0)

    def moveE(self):
        self.moveToOffset(1,0)

    def moveToLocation(self,loc):
        dst_tile=ctx.world.getTile(loc.x,loc.y)
        self.moveToTile(dst_tile)
    
    def moveToOffset(self,x,y):
        src_tile=self.parent
        assert(src_tile)
        loc=copy.deepcopy(src_tile.location)
        loc.x+=x
        loc.y+=y
        logging.debug(loc)
        self.moveToLocation(loc)

class Human(Actor):
    """A typical Terran."""
    def __init__(self):
        self.symbol='@'

class PC(Human):
    """The man himself."""
    def moveBlocked(self,tile):
        if(tile.actor and isinstance(tile.actor,Mogwai)):
                print "You hit the mogwai and slay it."
                ctx.enemies.remove(tile.actor)
                tile.actor=None

class Mogwai(Actor):
    """A vicious and hungry demon without much intelligence or sense of direction."""
    def __init__(self):
        self.symbol='m'
    
    def moveBlocked(self,tile):
        if(tile.actor==ctx.pc):
            print "A mogwai hits you.  You die!"
            pygame.display.quit()
            sys.exit(0)
    
    def move(self):
        choice=ctx.random.randint(0,3)
        if(choice==0):
            self.moveN()
        elif(choice==1):
            self.moveS()
        elif(choice==2):
            self.moveW()
        elif(choice==3):
            self.moveE()
