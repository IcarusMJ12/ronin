#!/usr/bin/env python
# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

from reality import Level
from numpy import zeros
import logging

__all__=['CellularAutomata']

class DisjointSetNode(object):
    """A Disjoined Set Node."""
    def __init__(self, data):
        self.data=data
        self.parent=self
        self.rank=0

    def __repr__(self):
        return 'Node<data:'+str(self.data)+' parent:'+str(self.parent.data)+' rank:'+str(self.rank)+'>'

    def getRootAndCompress(self):
        if self.parent==self:
            return self
        self.parent=self.parent.getRootAndCompress()
        return self.parent
    
    def join(self, other):
        logging.debug('joining'+str(self)+str(other))
        root1=self.getRootAndCompress()
        root2=other.getRootAndCompress()
        if root1==root2:
            return
        if root1.rank<root2.rank:
            root1.parent=root2
        else:
            root2.parent=root1
            if root1.rank==root2.rank:
                root1.rank+=1
    
class CellularAutomata(object):
    """Generates cave-like levels using cellular automata."""
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
        """Performs an iteration on a level according to the rule specified as a 3-tuple.

        Will turn a tile into a wall if it has <rule[0] or >=rule[2] neighboring wall tiles, including self.
        Will turn a tile into a floor if it has <rule[1] neighboring wall tiles, including self."""
        (width,height)=(level.width,level.height)
        if level not in self._scratch.keys():
            self._scratch[level]=zeros((width,height))
        scratch=self._scratch[level]
        for w in xrange(1,width-1):
            for h in xrange(1,height-1):
                wall_count=len([tile for tile in level.getNeighbors((w,h)) if tile.blocksLOS()])
                am_wall=False
                if level[w,h].blocksLOS():
                    wall_count+=1
                    am_wall=True
                #print '\t',w,h,wall_count
                if wall_count<rule[0]:
                    if not am_wall:
                        scratch[w,h]=1 #make wall
                elif wall_count>=rule[2]:
                    if not am_wall:
                        scratch[w,h]=1 #make wall
                elif wall_count<rule[1]:
                    if am_wall:
                        scratch[w,h]=2 #make floor
        walled_count=0
        floored_count=0
        for w in xrange(1,width-1):
            for h in xrange(1,height-1):
                (tile,terrain_type)=(level[w,h],scratch[w,h])
                if terrain_type==1:
                    tile.terrain=self.wall()
                    walled_count+=1
                elif terrain_type==2:
                    tile.terrain=self.floor()
                    floored_count+=1
        #print walled_count, floored_count
        scratch.fill(0)
    
    def cleanUp(self, level):
        """Removes level temporary data, to be called after all iterations have been done."""
        self._scratch.pop(level)
    
    def getPockets(self, level):
        """Determines the number of disjoint caves using the disjoint set algorithm."""
        current_row=[]
        previous_row=[]
        completed_nodes=[]
        for row in xrange(level.width):
            completed_nodes.extend(previous_row)
            previous_row=current_row
            len_previous_row=len(previous_row)
            current_row=[]
            previous_row_index=0
            for col in xrange(level.height):
                tile=level[row,col]
                if not tile.blocksLOS():
                    node=DisjointSetNode(tile)
                    logging.debug(str(node))
                    if len(current_row) and level.areAdjacent(node.data.loc, current_row[-1].data.loc):
                        current_row[-1].join(node)
                    for index in range(previous_row_index,len_previous_row):
                        if not level.areAdjacent(node.data.loc, previous_row[index].data.loc):
                            continue
                        previous_row_index=index
                        previous_row[index].join(node)
                        break
                    for index in range(previous_row_index+1, len_previous_row):
                        if level.areAdjacent(node.data.loc,previous_row[index].data.loc):
                            previous_row[index].join(node)
                        else:
                            break
                    current_row.append(node)
        completed_nodes.extend(previous_row)
        completed_nodes.extend(current_row)
        pockets={}
        for node in completed_nodes:
            parent=node.getRootAndCompress()
            if parent not in pockets.keys():
                pockets[parent]=[]
            pockets[parent].append(node.data)
        return sorted(pockets.values(), key=len)

    def generateLevel(self, width, height, initial_wall_ratio=0.45, rule=(1,4,5), iterations_count=5):
        """A convenience method for level generation that iterates using the same rule.

        Will also fill single tile pockets."""
        level=self.makeBlankLevel(width,height)
        #initial wall placement
        self.placeRandomWalls(level)
        #iterative generation
        for count in xrange(iterations_count):
            self.iterate(level, rule)
        self.iterate(level, (0,0,len(level.neighbors))) #fill single-tile pockets
        self.cleanUp(level)
        return level

if __name__=='__main__':
    from random import Random
    from objects import Floor, Wall

    for seed in xrange(256):
        random=Random(seed)
        generator=CellularAutomata(random, Floor, Wall)
        level=generator.generateLevel(51,25, iterations_count=5)
        pockets=generator.getPockets(level)
        pockets=[len(pocket) for pocket in pockets]
        print sum(pockets), pockets
