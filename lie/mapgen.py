#!/usr/bin/env python
# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

from reality import Level
from numpy import zeros

class CellularAutomata(object):
    def __init__(self, random, floor, wall, undiggable=None):
        self.floor=floor
        self.wall=wall
        if undiggable:
            self.undiggable=undiggable
        else:
            self.undiggable=wall
        self.random=random
        self._scratch={}
    
    def makeBlankLevel(self, width, height):
        """Generates a level of width x height and puts (undiggable if available) walls on the border."""
        #blank level
        level=Level(width, height)
        #surround with undiggable walls
        for i in xrange(level.height):
            level[0,i].terrain=self.undiggable()
            level[level.width-1,i].terrain=self.undiggable()
        for i in xrange(level.width-2):
            level[i+1,0].terrain=self.undiggable()
            level[i+1,level.height-1].terrain=self.undiggable()
        return level
    
    def placeRandomWalls(self, level, wall_fill_ratio=0.45):
        """Randomly fills the specified ratio of non-border tiles with walls."""
        (width,height)=(level.width,level.height)
        tiles=[tile for tile in level.tiles if tile.loc[0]!=0 and tile.loc[1]!=0 and tile.loc[0]!=width-1 and tile.loc[1]!=height-1]
        for i in xrange(int(wall_fill_ratio*len(tiles))):
            tiles.pop(self.random.randint(0,len(tiles)-1)).terrain=self.wall()
        for tile in tiles:
            tile.terrain=self.floor()
    
    def iterate(self, level, rule=(1,4,5)):
        (width,height)=(level.width,level.height)
        if level not in self._scratch.keys():
            self._scratch[level]=zeros((width,height))
        scratch=self._scratch[level]
        for w in xrange(width-2):
            for h in xrange(height-2):
                wall_count=len([tile for tile in level.getNeighbors((w,h)) if tile.blocksLOS()])
                am_wall=False
                if level[w,h].blocksLOS():
                    wall_count+=1
                    am_wall=True
                if wall_count<rule[0]:
                    if not am_wall:
                        scratch[w,h]=1 #make wall
                elif wall_count>=rule[2]:
                    if not am_wall:
                        scratch[w,h]=1 #make wall
                elif wall_count<rule[1]:
                    if am_wall:
                        scratch[w,h]=2 #make floor
        for w in xrange(width-2):
            for h in xrange(height-2):
                (tile,terrain_type)=(level[w,h],scratch[w,h])
                if terrain_type==1:
                    tile.terrain=self.wall()
                elif terrain_type==2:
                    tile.terrain=self.floor()
        scratch.fill(0)
    
    def cleanUp(self, level):
        self._scratch.pop(level)
    
    def countPockets(self, level):
        floors=[tile.loc for tile in level.tiles if not tile.blocksLOS()]
        pockets=[]
        while len(floors):
            pocket=[floors.pop()]

    def generateLevel(self, width, height, initial_wall_ratio=0.45, rule=(1,4,5), iterations_count=5):
        level=self.makeBlankLevel(width,height)
        #initial wall placement
        self.placeRandomWalls(level)
        #iterative generation
        for count in xrange(iterations_count):
            self.iterate(level, rule)
        self.cleanUp(level)
        return level

if __name__=='__main__':
    from random import Random
    from objects import Floor, Wall

    random=Random(1)
    generator=CellularAutomata(random, Floor, Wall)
    level=generator.generateLevel(51,25, iterations_count=5)
    print [tile.loc for tile in level.tiles if not tile.blocksLOS()]
