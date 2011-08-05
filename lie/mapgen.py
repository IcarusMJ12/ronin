#!/usr/bin/env python
# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

from reality import Level

class CellularAutomata(object):
    def __init__(self, random, floor, wall, undiggable=None):
        self.floor=floor
        self.wall=wall
        if undiggable:
            self.undiggable=undiggable
        else:
            self.undiggable=wall
        self.random=random
    
    def _countNeighboringWalls(self, level, loc):
        wall_count=0
        for l in ((1,1),(-1,-1),(0,-1),(-1,0),(1,0),(0,1)):
            try:
                if level[loc[0]+l[0],loc[1]+l[1]].blocksLOS():
                    wall_count+=1
            except IndexError:
                pass
        return wall_count

    def generateLevel(self, width, height, initial_wall_ratio=0.45, rule=(4,5), iterations_count=5):
        #blank level
        level=Level(width, height)
        #surround with undiggable walls
        for i in xrange(height):
            level[0,i].terrain=self.undiggable()
            level[width-1,i].terrain=self.undiggable()
        for i in xrange(width-2):
            level[i+1,0].terrain=self.undiggable()
            level[i+1,height-1].terrain=self.undiggable()
        #initial wall placement
        tiles=[tile for tile in level.tiles if tile.loc[0]!=0 and tile.loc[1]!=0 and tile.loc[0]!=width-1 and tile.loc[1]!=height-1]
        for i in xrange(int(initial_wall_ratio*len(tiles))):
            tiles.pop(self.random.randint(0,len(tiles)-1)).terrain=self.wall()
        for tile in tiles:
            tile.terrain=self.floor()
        #iterative generation
        for count in xrange(iterations_count):
            for w in xrange(width-2):
                for h in xrange(height-2):
                    wall_count=self._countNeighboringWalls(level,(w,h))
                    if level[w,h].blocksLOS():
                        wall_count+=1
                    if wall_count==0:
                        level[w,h].should_be_wall=True
                    elif wall_count>=rule[1]:
                        level[w,h].should_be_wall=True
                    elif wall_count<rule[0]:
                        level[w,h].should_be_wall=False
            for tile in level.tiles:
                try:
                    if tile.should_be_wall:
                        tile.terrain=self.wall()
                    else:
                        tile.terrain=self.floor()
                except AttributeError:
                    pass
        for tile in level.tiles:
            try:
                del tile.should_be_wall
            except AttributeError:
                pass
        return level

if __name__=='__main__':
    from random import Random
    from objects import Floor, Wall

    random=Random(1)
    generator=CellularAutomata(random, Floor, Wall)
    level=generator.generateLevel(51,25, iterations_count=5)
    print [tile.loc for tile in level.tiles if not tile.blocksLOS()]
