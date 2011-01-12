import pygame
import copy
from context import Context as Context

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
        else:
            print "Thud! You bump into something."
    
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
        print loc
        self.moveToLocation(loc)

class Human(Actor):
    """A typical Terran."""
    def __init__(self):
        self.symbol='@'
