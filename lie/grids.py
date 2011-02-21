import pygame
from pygame.rect import Rect
import abc
from objects import *
import globals
from exceptions import NotImplementedError

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
        self._is_visible=False
        self._was_seen=False
        self._is_identified=False #TODO: make things work
        self._unseen_image=globals.font.render('',True,(255,255,255))
        self._cover=(0,0) #(this tile's, player's)
        self.image=self._unseen_image
        self._real_image=None
        self.setTerrain(Floor())
        self.dirty=1
    
    def setIsVisible(self,val):
        if(val==self._is_visible):
            return
        self._is_visible=val
        if(val):
            self._was_seen=True
            self.image=self._real_image
            self.dirty=1
        elif(self._was_seen):
            g=globals.darkest_gray
            self.image=globals.font.render(self.terrain.symbol,True,(255*g,255*g,255*g))
            self.dirty=1
    
    def getIsVisible(self):
        return self._is_visible

    is_visible=property(getIsVisible,setIsVisible)

    def blocksLOS(self):
        return (self._terrain and self._terrain.blocks_los) or (self._actor and self._actor.blocks_los)
    
    def setActor(self,val):
        if val:
            assert(isinstance(val,Actor))
            assert(self.isPassableBy(val))
        self._actor=val
        if(val):
            self._real_image=globals.font.render(self.actor.symbol,True,(255,255,255))
            if(self._is_visible):
                self.image=self._real_image
                self.dirty=1
        elif(self.terrain):
            self._real_image=globals.font.render(self.terrain.symbol,True,(255,255,255))
            if(self._is_visible):
                self.image=self._real_image
                self.dirty=1
    
    def getActor(self):
        return self._actor
    
    actor=property(getActor, setActor)

    def setTerrain(self,val):
        assert(isinstance(val,Terrain))
        if(self.actor is None or val.isPassableBy(self.actor)):
            self._terrain=val
            self._real_image=globals.font.render(self.terrain.symbol,True,(255,255,255))
            if(self._was_seen):
                self.image=self._real_image
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

    def FOV(self,tile,radius):
        (x1,y1)=(tile.location.x,tile.location.y)
        for x2 in xrange(len(self.grid)):
            for y2 in xrange(len(self.grid[x2])):
                if pow(x2-x1,2)+pow(y2-y1,2)-(y2-y1)*(x2-x1)<=pow(radius,2)+radius:
                    if self._LOS((x1,y1),(x2,y2))[0]<1:
                        self.grid[x2][y2].is_visible=True
                        continue
                self.grid[x2][y2].is_visible=False

    def _LOS(self,src,dst):
        (x1,y1)=src
        (x2,y2)=dst
        (x_min,x_max)=(min(x1,x2),max(x1,x2)+1)
        (x_min,x_max)=(max(x_min-1,0),min(len(self.grid),x_max+1))
        (y_min,y_max)=(min(y1,y2),max(y1,y2)+1)
        (y_min,y_max)=(max(y_min-1,0),min(len(self.grid[x_max]),y_max+1))
        #tiles=filter(lambda i: i.blocksLOS(), [item for sublist in self.grid[x_min:x_max] for item in sublist[y_min:y_max]])
        #if len(tiles) == 0:
        return (0,0)
        #return (1,1)

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
