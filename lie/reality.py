# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import abc
from objects import *
from exceptions import NotImplementedError
import logging

HEX_NEIGHBORS=((1,1),(-1,-1),(0,-1),(-1,0),(1,0),(0,1))
SQUARE_NEIGHBORS=((1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1))

class Tile(object):
    """A tile containing actual game objects.  Floor implied."""
    def __init__(self, loc):
        super(Tile, self).__init__()
        self._actor=None
        self._terrain=None
        self.items=None
        self.loc=loc
        self.setTerrain(Floor())
        self.dirty=1

    def blocksLOS(self):
        return (self.terrain and self.terrain.blocks_los) or (self.actor and self.actor.blocks_los)
    
    def setActor(self,val):
        if val:
            assert(isinstance(val,Actor))
            assert(self.isPassableBy(val))
        self._actor=val
        self.dirty=1
    
    def getActor(self):
        return self._actor
    
    actor=property(getActor, setActor)

    def setTerrain(self,val):
        assert(isinstance(val,Terrain))
        if(self.actor is None or val.isPassableBy(self.actor)):
            self._terrain=val
            self.dirty=1
        else:
            raise 'Attempted to set terrain to a non-passable type while an actor was present.'
    
    def getTerrain(self):
        return self._terrain

    terrain=property(getTerrain, setTerrain)

    def top(self):
        if self.actor:
            return self.actor
        if self.items:
            return self.items
        return self.terrain
    
    def isPassableBy(self, actor):
        if(self.actor is not None):
            return False
        if(self.terrain is not None and self.terrain.isPassableBy(actor)):
            return True
        return False

class Grid(object):
    """An abstract grid on a level plane."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self,width,height,neighbors=HEX_NEIGHBORS):
        self.width=width
        self.height=height
        self.grid=None
        self.neighbors=neighbors
    
    def __getitem__(self,loc):
        return self.grid[loc[0]][loc[1]]

    def getTiles(self):
        return [item for sublist in self.grid for item in sublist]
    
    tiles=property(getTiles,None)

    def getDirtyLocations(self):
        return [(i,j) for j in xrange(self.height) for i in xrange(self.width) if self[i,j].dirty]

    def markClean(self):
        for tile in self.tiles:
            tile.dirty=0

    def areAdjacent(self, loc1, loc2):
        return (loc1[0]-loc2[0],loc1[1]-loc2[1]) in self.neighbors

    def getNeighbors(self, loc):
        neighbors=[]
        for l in self.neighbors:
            try:
                neighbors.append(self[loc[0]+l[0],loc[1]+l[1]])
            except IndexError:
                pass
        return neighbors

class Level(Grid):
    """A world level containing tiles."""
    def __init__(self,width,height):
        super(Level,self).__init__(width,height)
        self.grid=[[Tile((i,j)) for j in xrange(self.height)] for i in xrange(self.width)]

class World(object):
    def __init__(self):
        raise NotImplementedError()
