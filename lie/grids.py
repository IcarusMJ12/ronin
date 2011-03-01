import pygame
from pygame.rect import Rect
import abc
from objects import *
#from hexfov import HexFOV
from fov import FOV
import globals
import math
from exceptions import NotImplementedError
import fractions
import profile

TILE_SAMPLE_COUNT=16

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
        self._was_seen=True #TODO: False
        self._is_identified=False #TODO: make things work
        self._unseen_image=globals.font.render('',True,(255,255,255))
        #self._cover=(1,1) #(this tile's, player's)
        self._cover=1
        self.d2=0 #distance squared
        self.image=self._unseen_image
        self._real_image=None
        self.setTerrain(Floor())
        self.dirty=1
    
    #this function has been hijacked to showcase FOV
    def _computeTileColor(self):
        gray=globals.darkest_gray
        g=1.0
        if self._cover>0:
            g=gray
        r=0.8
        b=0
        if self.d2:
            b=(1.0/math.pow(self.d2,0.25))
        return (r*255,g*255,b*255)

    def setCover(self,val):
        if(val==self._cover):
            return
        self._cover=val
        if(val<1):
            self._was_seen=True
            #self.image=self._real_image
            c=self._computeTileColor()
            if self.actor:
                self.image=globals.font.render(self.actor.symbol,True,c)
            else:
                self.image=globals.font.render(self.terrain.symbol,True,c)
            self.dirty=1
        elif(self._was_seen):
            g=globals.darkest_gray
            self.image=globals.font.render(self.terrain.symbol,True,(255*g,255*g,255*g))
            self.dirty=1
    
    def getCover(self):
        return self._cover

    cover=property(getCover,setCover)

    def blocksLOS(self):
        return (self._terrain and self._terrain.blocks_los) or (self._actor and self._actor.blocks_los)
    
    def setActor(self,val):
        if val:
            assert(isinstance(val,Actor))
            assert(self.isPassableBy(val))
        self._actor=val
        if(val):
            self._real_image=globals.font.render(self.actor.symbol,True,(255,255,255))
            if(self._cover<1):
                #self.image=self._real_image
                self.image=globals.font.render(self.actor.symbol,True,self._computeTileColor())
                self.dirty=1
        elif(self.terrain):
            self._real_image=globals.font.render(self.terrain.symbol,True,(255,255,255))
            if(self._cover<1):
                self.image=globals.font.render(self.terrain.symbol,True,self._computeTileColor())
                #self.image=self._real_image
                self.dirty=1
    
    def getActor(self):
        return self._actor
    
    actor=property(getActor, setActor)

    def setTerrain(self,val):
        assert(isinstance(val,Terrain))
        if(self.actor is None or val.isPassableBy(self.actor)):
            self._terrain=val
            self._real_image=globals.font.render(self.terrain.symbol,True,(255,255,255))
            if(self._cover<1):
                self.image=self._real_image
                self.dirty=1
            elif(self._was_seen):
                g=globals.darkest_gray
                self.image=globals.font.render(self.terrain.symbol,True,(255*g,255*g,255*g))
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
        self.rect=pygame.sprite.Rect((location.x*globals.cell_width, location.y*globals.cell_height),(globals.cell_width,globals.cell_height))

class PseudoHexTile(Tile):
    def __init__(self, location):
        super(PseudoHexTile, self).__init__(location)
        self.rect=pygame.sprite.Rect(((location.y-location.x)*(globals.cell_width+int(globals.cell_width*globals.scale_horizontally*0.75)), (location.y+location.x)*globals.cell_height/2),(globals.cell_width,globals.cell_height))

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
    
    @abc.abstractmethod
    def FOV(self,tile,radius):
        raise NotImplementedError()

class SquareGrid(Grid):
    def __init__(self,level,width,height):
        super(SquareGrid, self).__init__(level, width, height)
        self.grid=[[SquareTile(Location(level,i,j)) for j in xrange(height)] for i in xrange(width)]
        self.view=GridView(Rect((0,globals.grid_offset),(min(width*globals.cell_width,globals.screen.get_width()),min(height*globals.cell_height,globals.screen.get_height()-globals.grid_offset))),self.getTiles())

    def FOV(self,tile,radius):
        raise NotImplementedError() #TODO
    
class PseudoHexGrid(Grid):
    def __init__(self,level,width,height):
        super(PseudoHexGrid, self).__init__(level, width, height)
        self.grid=[[PseudoHexTile(Location(level,i,j)) for j in xrange(height)] for i in xrange(width)]
        self.view=GridView(Rect((0,globals.grid_offset),(min(width*globals.cell_width,globals.screen.get_width()),min(height*globals.cell_height,globals.screen.get_height()-globals.grid_offset))),self.getTiles())
        self.fov=FOV()
    
    def FOV(self, tile, radius):
        me=(tile.location.x,tile.location.y,tile.blocksLOS())
        world=[(tile.location.x,tile.location.y,tile.blocksLOS()) for tile in self.getTiles()]
        ret=self.fov.calculateHexFOV(me,world)
        for r in ret:
            self.grid[r[0][0]][r[0][1]].cover=r[1]
            self.grid[r[0][0]][r[0][1]].d2=r[2]

class GridView(pygame.sprite.RenderUpdates):
    def __init__(self,viewable_area,sprites,center=None):
        super(GridView, self).__init__()
        print viewable_area
        self.viewport=globals.screen.subsurface(viewable_area)
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
        self.clear(self.viewport, globals.background)
        pygame.display.update(super(GridView, self).draw(self.viewport))
    
    def setSprites(sprites):
        self._sprites=sprites
        self.empty()
        self.add(sprites)
