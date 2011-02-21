import pygame
from pygame.rect import Rect
import abc
from objects import *
import globals
import math
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
        self._was_seen=False
        #self._was_seen=True #TODO: change back
        self._is_identified=False #TODO: make things work
        self._unseen_image=globals.font.render('',True,(255,255,255))
        self._cover=(0,0) #(this tile's, player's)
        self.image=self._unseen_image
        self._real_image=None
        self.setTerrain(Floor())
        self.dirty=1
    
    def setCover(self,val):
        if(val==self._cover):
            return
        self._cover=val
        if(val[0]<1):
            self._was_seen=True
            self.image=self._real_image
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
            if(self._cover[0]<1):
                self.image=self._real_image
                self.dirty=1
        elif(self.terrain):
            self._real_image=globals.font.render(self.terrain.symbol,True,(255,255,255))
            if(self._cover[0]<1):
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
            if(self._is_visible):
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

    def FOV(self,tile,radius):
        (x1,y1)=(tile.location.x,tile.location.y)
        for x2 in xrange(len(self.grid)):
            for y2 in xrange(len(self.grid[x2])):
                if pow(x2-x1,2)+pow(y2-y1,2)-(y2-y1)*(x2-x1)<=pow(radius,2)+radius:
                    self.grid[x2][y2].cover=self._LOS((x1,y1),(x2,y2))
                    continue
                self.grid[x2][y2].cover=(1,1)

    def _LOS(self,src,dst):
        printing=False
        if src == dst:
            return (0,0)
        (x1,y1)=src
        (x2,y2)=dst
        if(x1==x2 and y2==y1+1):
            printing=True
            print src, dst
        (x_min,x_max)=(min(x1,x2),max(x1,x2)+1)
        (x_min,x_max)=(max(x_min,0),min(len(self.grid),x_max))
        (y_min,y_max)=(min(y1,y2),max(y1,y2)+1)
        (y_min,y_max)=(max(y_min,0),min(len(self.grid[x_max]),y_max))
        #determine if there are any candidate tiles that could block LOS, i.e. tiles falling within the rectangle defined by corners x1,y1 x2,y2
        if x1 == x2:
            (x_min,x_max)=(max(x_min-1,0),min(len(self.grid),x_max+1))
        if y1 == y2:
            (y_min,y_max)=(max(y_min-1,0),min(len(self.grid),y_max+1))
        tiles=map(lambda i: (i.location.x, i.location.y), filter(lambda i: i.blocksLOS() and not (i.location.x==x1 and i.location.y==y1) and not (i.location.x==x2 and i.location.y==y2), [item for sublist in self.grid[x_min:x_max] for item in sublist[y_min:y_max]]))
        if printing:
            print (x_min,y_min),(x_max,y_max)
            print tiles
        #if no tiles, there can be no cover
        if len(tiles) == 0:
            return (0,0)
        #otherwise convert to rectangular cartesian coordinates for further processing
        (x1,y1,x2,y2)=(x1-y1*math.sin(math.pi/6),y1*math.cos(math.pi/6),x2-y2*math.sin(math.pi/6),y2*math.cos(math.pi/6))
        tiles=map(lambda i: (i[0]-i[1]*math.sin(math.pi/6),i[1]*math.cos(math.pi/6)), tiles)
        if printing:
            print tiles
        #if vertical lines, rotate 90 degrees
        if x1 == x2:
            (x1,y1)=(y1,x1)
            (x2,y2)=(y2,x2)
            tiles=map(lambda i: (i[1],i[0]), tiles)
        normal1=(y1-y2,x2-x1)
        normal1=(normal1[0]/math.sqrt(pow(normal1[0],2)+pow(normal1[1],2)),normal1[1]/math.sqrt(pow(normal1[0],2)+pow(normal1[1],2)))
        normal2=(-normal1[0],-normal1[1])
        dydx=(y2-y1)/(x2-x1) #dy/dx actually
        y_intercept=-dydx*x1+y1
        y_intercept1=y_intercept+(-dydx*normal1[0]+normal1[1])
        y_intercept2=y_intercept+(-dydx*normal2[0]+normal2[1])
        normal_slope=normal1[0]/normal1[1]
        x_intercept1=x1-y1*normal_slope
        x_intercept2=x2-y2*normal_slope
        (y_intercept_min,y_intercept_max)=(min(y_intercept1,y_intercept2),max(y_intercept1,y_intercept2))
        (x_intercept_min,x_intercept_max)=(min(x_intercept1,x_intercept2),max(x_intercept1,x_intercept2))
        if printing:
            print (x1,y1),(x2,y2),tiles
            print normal1, normal2, dydx
            print y_intercept_min,y_intercept_max
            for i in tiles:
                print i,':',-dydx*i[0]+i[1]
        tiles=filter(lambda i: y_intercept_min<(-dydx*i[0]+i[1])<y_intercept_max, tiles)
        tiles=filter(lambda i: x_intercept_min<(i[0]-i[1]*normal_slope)<x_intercept_max, tiles)
        if len(tiles) == 0:
            return (0,0)
        return (1,1)

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
