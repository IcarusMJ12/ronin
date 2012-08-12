# Copyright (c) 2011-2012 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import abc
from numpy import array as ar
import math
import logging
import pygame
from pygame.rect import Rect
from pygame import draw
from copy import copy

import globals
from reality import Grid
from objects import State, Actor
from lie.reality import HEX_NEIGHBORS
from lie.context import Context as Context

logger=logging.getLogger(__name__)

MAX_COLOR=ar((1.0,1.0,1.0))
MIN_COLOR=ar((0.0,0.0,0.0))

STATE_HUE_MAP={
        State.Friendly: ar((0.2,1.0,0.2))*(255,255,255),
        State.Neutral: ar((0.2,0.2,1.0))*(255,255,255),
        State.Unaware: ar((1.0,1.0,1.0))*(255,255,255),
        State.Alert: ar((1.0,1.0,0.2))*(255,255,255),
        State.Hostile: ar((1.0,0.2,0.2))*(255,255,255)
        }

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
        self.hue=ar((0.0,0.0,0.0))

class GridView(pygame.sprite.RenderUpdates):
    __metaclass__ = abc.ABCMeta

    def __init__(self,viewable_area,center=None):
        super(GridView, self).__init__()
        logger.debug(str(viewable_area))
        self.viewport=globals.screen.subsurface(viewable_area)
        self._sprites=[]
        (self.x,self.y)=(self.viewport.get_width()/2,self.viewport.get_height()/2)
        logger.debug(str(self.x)+' '+str(self.y))
        self.ctx = Context.getContext()
        if center:
            self.center(center)
    
    def center(self,center):
        logger.debug(str(center))
        (x,y)=(center.x+center.w/2,center.y+center.h/2)
        (dx,dy)=(self.x-x,self.y-y)
        logger.debug(str(dx)+' '+str(dy))
        self.move(dx,dy)

    def move(self,x,y):
        map(lambda i:i.rect.move_ip(x,y), self._sprites)
    
    def draw(self):
        self.clear(self.viewport, globals.background)
        dirties=set(self.level.getDirtyLocations()).union(self.perception.getDirtyLocations())
        #dirties=[(i,j) for j in xrange(self.height) for i in xrange(self.width)]
        gray=globals.darkest_gray
        gray=ar((gray,gray,gray))
        white=1.0
        white=ar((white,white,white))
        npcs=[]
        for loc in dirties:
            if self.perception[loc].cover==1.0:
                self[loc].hue=copy(gray)
            else:
                self[loc].hue=copy(white)
                #obj = self.perception[loc].top().obj if self.perception[loc].top() else None
                #if isinstance(obj, Actor) and obj!=self.perception.actor:
                #   npcs.append((ar(loc), obj.facing, STATE_HUE_MAP[obj.state]))
        """
        for loc, facing, hue in npcs:
            print loc, facing, hue
            index=HEX_NEIGHBORS.index(facing)
            self[tuple(loc+facing)].hue+=hue
            self[tuple(loc+HEX_NEIGHBORS[index-1])].hue+=hue/2
            try:
                self[tuple(loc+HEX_NEIGHBORS[index+1])].hue+=hue/2
            except IndexError:
                self[tuple(loc+HEX_NEIGHBORS[0])].hue+=hue/2
        """
        for loc in dirties:
            try:
                element=self.perception[loc].top()
                #self[loc].image = globals.font.render(element.symbol,True,ar(map(max,map(min, self[loc].hue, MAX_COLOR), MIN_COLOR))*element.hue*(255,255,255))
                self[loc].image = element.obj.render(ar(map(max,map(min, self[loc].hue, MAX_COLOR), MIN_COLOR))*(255,255,255))
                if element.facing and element.obj != self.ctx.pc and (element.facing[0] or element.facing[1]):
                    h, w = globals.cell_height-1, globals.cell_width-1
                    pointlist = ()
                    vertical, horizontal = h*((element.facing[0] or element.facing[1])*0.5+0.5), w*((element.facing[1]-element.facing[0])*0.5+0.5)
                    print horizontal, w/2.0
                    if horizontal == w/2.0:
                        pointlist = ((horizontal-3, vertical-cmp(vertical, 1)*3), (horizontal, vertical), (horizontal+3, vertical-cmp(vertical,1)*3))
                    else:
                        pointlist = ((horizontal, vertical-cmp(vertical,1)*3), (horizontal, vertical), (horizontal-cmp(horizontal,1)*3, vertical))
                    draw.lines(self[loc].image, STATE_HUE_MAP[element.obj.state], False, pointlist, True)
            except AttributeError:
                pass
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
        #viewable_area=Rect((0,globals.grid_offset),(min(width*globals.cell_width*(1.0+globals.scale_horizontally*0.75),globals.screen.get_width()),min(height*globals.cell_height,globals.screen.get_height()-globals.grid_offset)))
        viewable_area=Rect((0,globals.grid_offset),(globals.screen.get_width(),globals.screen.get_height()-globals.grid_offset))
        Grid.__init__(self,width,height)
        GridView.__init__(self,viewable_area,center)
        self.grid=[[PseudoHexTile((i,j)) for j in xrange(height)] for i in xrange(width)]
        self.setSprites(self.tiles)
