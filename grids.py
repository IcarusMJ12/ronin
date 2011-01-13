import pygame
from objects import *
from context import Context as Context

ctx=Context.getContext()

class Location(object):
    def __init__(self, level, x, y):
        self.level=level
        self.x=x
        self.y=y
    
    def __repr__(self):
        return "<Location(level:"+self.level.__repr__()+" x:"+self.x.__repr__()+" y:"+self.y.__repr__()+")>"

class Tile(pygame.sprite.DirtySprite):
    def __init__(self,location):
        pygame.sprite.DirtySprite.__init__(self)
        self.ctx=ctx
        self._actor=None
        self._terrain=None
        self.items=None
        self.location=location
        self.rect=pygame.sprite.Rect((location.x*ctx.CELL_WIDTH, location.y*ctx.CELL_HEIGHT),(ctx.CELL_WIDTH,ctx.CELL_HEIGHT))
        self.image=None
        self.setTerrain(Floor())
        self.dirty=1
    
    def setActor(self,val):
        if val:
            assert(isinstance(val,Actor))
        self._actor=val
        if(val):
            self.image=self.ctx.font.render(self.actor.symbol,True,(255,255,255))
            self.dirty=1
        elif(self.terrain):
            self.image=self.ctx.font.render(self.terrain.symbol,True,(255,255,255))
            self.dirty=1
    
    def getActor(self):
        return self._actor
    
    actor=property(getActor, setActor)

    def setTerrain(self,val):
        assert(isinstance(val,Terrain))
        if(self.actor is None or val.isPassableBy(self.actor)):
            self._terrain=val
            self.image=self.ctx.font.render(self.terrain.symbol,True,(255,255,255))
            self.dirty=1
        else:
            raise 'Attempted to set terrain to a non-passable type while an actor was present'
    
    def getTerrain(self):
        return self._terrain

    terrain=property(getTerrain, setTerrain)
    
    def isPassableBy(self, actor):
        if(self.actor is not None):
            return False
        if(self.terrain is not None and self.terrain.isPassableBy(actor)):
            return True
        return False

class Grid(object):
    def __init__(self,level,width,height):
        self.level=level
        self.width=width
        self.height=height
        self.grid=[[Tile(Location(level,j,i)) for i in xrange(width)] for j in xrange(height)]

    def getTile(self,x,y):
        return self.grid[x][y]

    def getTiles(self):
        return [item for sublist in self.grid for item in sublist]

class SquareGrid(Grid):
    pass
