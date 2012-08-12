# Copyright (c) 2011-2012 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import logging
import globals
from asp_spa import FOV
from reality import Grid
from objects import Actor
from math import pi, sin

logger=logging.getLogger(__name__)

PI_2 = pi*2

class Memory(object):
    __slots__ = ['obj', 'facing']

    def __init__(self, obj):
        self.obj = obj
        try:
            self.facing = obj.facing
        except AttributeError:
            self.facing = None

class PTile(object):
    def __init__(self, tile):
        super(PTile, self).__init__()
        self.tile=tile
        self._cover=1
        self._d2=0
        self.was_seen=False
        self.dirty=1
        self.memory=None
    
    def setCover(self,val):
        if self._cover==val:
            return
        self._cover=val
        self.dirty=1
        if(val<1):
            self.was_seen=True
    
    def getCover(self):
        return self._cover

    cover=property(getCover,setCover)

    def setD2(self,val):
        if self._d2==val:
            return
        self._d2=val
        self.dirty=1
    
    def getD2(self):
        return self._d2

    d2=property(getD2,setD2)

    def top(self):
        if not self.was_seen:
            return None
        if self.cover==1:
            return self.memory
        self.memory = Memory(self.tile.top())
        return self.memory

class PGrid(Grid):
    def __init__(self, grid, actor):
        super(PGrid, self).__init__(grid.width, grid.height)
        self.grid=[[PTile(grid[i,j]) for j in xrange(grid.height)] for i in xrange(grid.width)]
        self.fov=FOV()
        self.actor=actor
        self.target=None
        self.monsters={}

    def calculateFOV(self, radius=None):
        loc=self.actor.parent.loc
        tile=self[loc[0],loc[1]].tile
        me=(loc[0],loc[1],tile.blocksLOS())
        world=[(i,j,self[i,j].tile.blocksLOS()) for i in xrange(self.width) for j in xrange(self.height)]
        fov=self.actor.getFOV()
        if fov==PI_2:
            ret=self.fov.calculateHexFOV(me,world)
        else:
            ret=self.fov.calculateHexFOV(me, world, fov, self.actor.facing)
        for r in ret:
            self[r[0][0],r[0][1]].d2=r[2]
            if r[1]>1:
                logger.error(str(me))
                logger.error(str(r))
                raise AssertionError("cover > 1")
            self[r[0][0],r[0][1]].cover=sin(r[1]*pi/2)
        self.monsters=dict([(tile.tile.loc,tile.top()) for tile in self.tiles if tile.cover<1 and isinstance(tile.top(), Actor) and tile.top()!=self.actor])
        visible_actors=set(self.monsters.values())
        for tile in self.tiles:
            if tile.cover==1 and tile.memory and tile.memory.obj in visible_actors:
                tile.memory = Memory(tile.tile.terrain)
        self.monsters_keys=sorted(self.monsters.keys(), key=lambda x: pow(x[0]-me[0],2)+pow(x[1]-me[1],2)-(x[0]-me[0])*(x[1]-me[1]))
        logger.debug('me:'+str(self.actor.parent.loc)+' them:'+str(self.monsters_keys))
    
    def examineTile(self, loc):
        objects=None
        if self[loc].cover==1:
            objects=[]
            if self[loc].memory:
                objects.append(self[loc].memory.obj)
            if self[loc].was_seen:
                terrain=self[loc].tile.terrain
                if terrain not in objects:
                    objects.append(self[loc].tile.terrain)
        else:
            objects=self[loc].tile.contents()
        return [(id(obj), obj.getShortDescription(self[loc].cover), obj.getLongDescription(self[loc].cover)) for obj in objects]
