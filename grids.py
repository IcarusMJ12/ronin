import pygame
from pygame.rect import Rect
import abc
from objects import *
from context import Context as Context
from copy import copy
import lie.globals

ctx=Context.getContext()

class Location(object):
    def __init__(self, level, x, y):
        self.level=level
        self.x=x
        self.y=y
    
    def __repr__(self):
        return "<Location(level:"+self.level.__repr__()+" x:"+self.x.__repr__()+" y:"+self.y.__repr__()+")>"

class Tile(pygame.sprite.DirtySprite):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self,location):
        super(Tile, self).__init__()
        self._actor=None
        self._terrain=None
        self.items=None
        self.location=location
        self.image=None
        self.setTerrain(Floor())
        self.dirty=1
    
    def setActor(self,val):
        if val:
            assert(isinstance(val,Actor))
            assert(self.isPassableBy(val))
        self._actor=val
        if(val):
            self.image=ctx.font.render(self.actor.symbol,True,(255,255,255))
            self.dirty=1
        elif(self.terrain):
            self.image=ctx.font.render(self.terrain.symbol,True,(255,255,255))
            self.dirty=1
    
    def getActor(self):
        return self._actor
    
    actor=property(getActor, setActor)

    def setTerrain(self,val):
        assert(isinstance(val,Terrain))
        if(self.actor is None or val.isPassableBy(self.actor)):
            self._terrain=val
            self.image=ctx.font.render(self.terrain.symbol,True,(255,255,255))
            self.dirty=1
        else:
            raise 'Attempted to set terrain to a non-passable type while an actor was present.'
    
    def getTerrain(self):
        return self._terrain

    terrain=property(getTerrain, setTerrain)
    
    def isPassableBy(self, actor):
        if(self.actor is not None):
            return False
        if(self.terrain is not None and self.terrain.isPassableBy(actor)):
            return True
        return False

class SquareTile(Tile):
    def __init__(self, location):
        super(SquareTile, self).__init__(location)
        self.rect=pygame.sprite.Rect((location.x*ctx.CELL_WIDTH, location.y*ctx.CELL_HEIGHT),(ctx.CELL_WIDTH,ctx.CELL_HEIGHT))

class PseudoHexTile(Tile):
    def __init__(self, location):
        super(PseudoHexTile, self).__init__(location)
        self.rect=pygame.sprite.Rect((location.x*ctx.CELL_WIDTH, (location.y+float(location.x)/2)*ctx.CELL_HEIGHT),(ctx.CELL_WIDTH,ctx.CELL_HEIGHT))

class Grid(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self,level,width,height):
        self.level=level
        self.width=width
        self.height=height
        self.grid=None

    def getTile(self,x,y):
        return self.grid[x][y]

    def getTiles(self):
        return [item for sublist in self.grid for item in sublist]

    def draw(self):
        self.view.draw()
    
    def center(self, center):
        self.view.center(center)
    
    def move(self,x,y):
        self.view.move(x,y)

class SquareGrid(Grid):
    def __init__(self,level,width,height):
        super(SquareGrid, self).__init__(level, width, height)
        self.grid=[[SquareTile(Location(level,i,j)) for j in xrange(height)] for i in xrange(width)]
        self.view=GridView(Rect((0,ctx.GRID_OFFSET),(min(width*ctx.CELL_WIDTH,lie.globals.screen.get_width()),min(height*ctx.CELL_HEIGHT,lie.globals.screen.get_height()-ctx.GRID_OFFSET))),self.getTiles())
    
class PseudoHexGrid(Grid):
    def __init__(self,level,width,height):
        super(PseudoHexGrid, self).__init__(level, width, height)
        self.grid=[[PseudoHexTile(Location(level,i,j)) for j in xrange(height)] for i in xrange(width)]
        self.view=GridView(Rect((0,ctx.GRID_OFFSET),(min(width*ctx.CELL_WIDTH,lie.globals.screen.get_width()),min(height*ctx.CELL_HEIGHT,lie.globals.screen.get_height()-ctx.GRID_OFFSET))),self.getTiles())

class GridView(pygame.sprite.RenderUpdates):
    def __init__(self,viewable_area,sprites,center=None):
        super(GridView, self).__init__()
        print viewable_area
        self.viewport=ctx.screen.subsurface(viewable_area)
        self._sprites=sprites
        self.add(sprites)
        (self.x,self.y)=(self.viewport.get_width()/2,self.viewport.get_height()/2)
        print self.x, self.y
        if center:
            self.center(center)
    
    def center(self,center):
        print center
        (x,y)=(center.x+center.w/2,center.y+center.h/2)
        (dx,dy)=(self.x-x,self.y-y)
        print dx, dy
        self.move(dx,dy)

    def move(self,x,y):
        map(lambda i:i.rect.move_ip(x,y), self._sprites)
    
    def draw(self):
        self.clear(self.viewport, lie.globals.background)
        pygame.display.update(super(GridView, self).draw(self.viewport))
    
    def setSprites(sprites):
        self._sprites=sprites
        self.empty()
        self.add(sprites)
