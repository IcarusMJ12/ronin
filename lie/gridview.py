import abc
import globals
import math
import logging
import pygame
from pygame.rect import Rect
from reality import Grid

def computeTileColor(ptile):
    gray=globals.darkest_gray
    g=1.0
    r=ptile.cover
    if r==1:
        return(gray*255,gray*255,gray*255)
    b=1.0
    if ptile.d2:
        b=(1.0/math.pow(ptile.d2,0.25))
    return (r*255,g*255,b*255)

class RenderableTile(pygame.sprite.DirtySprite):
    __metaclass__ = abc.ABCMeta
    BLANK_IMAGE = None
    
    @abc.abstractmethod
    def __init__(self, loc):
        super(RenderableTile, self).__init__()
        self.loc=loc
        self.rect=None
        self._image=RenderableTile._blankImage()
        self.dirty=1
    
    def setImage(self, image):
        self._image=image
        self.dirty=1
    
    def getImage(self):
        return self._image
    
    @classmethod
    def _blankImage(self):
        if RenderableTile.BLANK_IMAGE is None:
            RenderableTile.BLANK_IMAGE = globals.font.render('',True,(255,255,255))
        return RenderableTile.BLANK_IMAGE

    image=property(getImage,setImage)

class SquareTile(RenderableTile):
    def __init__(self, loc):
        super(SquareTile, self).__init__(loc)
        self.rect=pygame.sprite.Rect((loc[0]*globals.cell_width, loc[1]*globals.cell_height),(globals.cell_width,globals.cell_height))

class PseudoHexTile(RenderableTile):
    def __init__(self, loc):
        super(PseudoHexTile, self).__init__(loc)
        self.rect=pygame.sprite.Rect(((loc[1]-loc[0])*(globals.cell_width+int(globals.cell_width*globals.scale_horizontally*0.75)), (loc[1]+loc[0])*globals.cell_height/2),(globals.cell_width,globals.cell_height))

class GridView(pygame.sprite.RenderUpdates):
    __metaclass__ = abc.ABCMeta

    def __init__(self,viewable_area,center=None):
        super(GridView, self).__init__()
        logging.info(str(viewable_area))
        self.viewport=globals.screen.subsurface(viewable_area)
        self._sprites=[]
        (self.x,self.y)=(self.viewport.get_width()/2,self.viewport.get_height()/2)
        logging.info(str(self.x)+' '+str(self.y))
        if center:
            self.center(center)
    
    def center(self,center):
        logging.info(str(center))
        (x,y)=(center.x+center.w/2,center.y+center.h/2)
        (dx,dy)=(self.x-x,self.y-y)
        logging.info(str(dx)+' '+str(dy))
        self.move(dx,dy)

    def move(self,x,y):
        map(lambda i:i.rect.move_ip(x,y), self._sprites)
    
    def draw(self):
        self.clear(self.viewport, globals.background)
        dirties=set(self.level.getDirtyLocations()).union(self.perception.getDirtyLocations())
        for loc in dirties:
            self[loc].image=globals.font.render(self.perception[loc].top().symbol,True,computeTileColor(self.perception[loc]))
        pygame.display.update(super(GridView, self).draw(self.viewport))
        for tile in self.level.tiles:
            tile.dirty=0
        for tile in self.perception.tiles:
            tile.dirty=0
    
    def setSprites(self, sprites):
        self._sprites=sprites
        self.empty()
        self.add(sprites)

class HexGridView(GridView, Grid):
    def __init__(self,level,perception,center=None):
        self.level=level
        self.perception=perception
        (width,height)=(level.width,level.height)
        viewable_area=Rect((0,globals.grid_offset),(min(width*globals.cell_width,globals.screen.get_width()),min(height*globals.cell_height,globals.screen.get_height()-globals.grid_offset)))
        Grid.__init__(self,width,height)
        GridView.__init__(self,viewable_area,center)
        self.grid=[[PseudoHexTile((i,j)) for j in xrange(height)] for i in xrange(width)]
        self.setSprites(self.tiles)
