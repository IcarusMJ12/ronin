# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import abc
import copy
import logging
import math
from exceptions import NotImplementedError

__all__=['Actor', 'Floor', 'Terrain', 'Wall']

class BaseObject(object):
    """All in-game objects should derive from this or one of its children."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        self.blocks_los=False
        self.long_description=self.__doc__
        self.short_description=self.__doc__
    
    def getLongDescription(self, visibility=None):
        """Returns docstring by default.  You should probably override this."""
        return self.long_description or ''

    def getShortDescription(self, visibility=None):
        """Returns docstring by default.  You should probably override this."""
        return self.short_description or ''

class Terrain(BaseObject):
    """A terrain feature."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, passable_by):
        super(Terrain, self).__init__()
        self.passable_by=passable_by
        self.is_visible=False
        self.was_seen=False
    
    def isPassableBy(self, actor):
        if self.passable_by is None:
            return False
        return isinstance(actor,self.passable_by)

class Floor(Terrain):
    """A floor that can be walked on."""
    def __init__(self):
        super(Floor, self).__init__(Actor)
        self.short_description='a floor'
        self.symbol=u'\u00b7'
        self.blocks_los=False

class Wall(Terrain):
    """An impassable wall."""
    def __init__(self):
        super(Wall, self).__init__(None)
        self.short_description='a wall'
        self.symbol='#'
        self.blocks_los=True

class Actor(BaseObject):
    """Any object that can act of its own volition."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        super(Actor, self).__init__()
        self.short_description='an actor'
        self.perception=None
        self.facing=(0,0)

    def moveToTile(self, tile):
        if(tile.isPassableBy(self)):
            tile.actor=self
            self.parent.actor=None
            self.parent=tile
            return True
        else:
            self.moveBlocked(tile)
            return False
    
    @abc.abstractmethod
    def moveBlocked(self,tile):
        raise NotImplementedError()
    
    def moveN(self):
        return self.moveToOffset(0,-1)
    
    def moveNW(self):
        return self.moveToOffset(-1,-1)

    def moveNE(self):
        return self.moveToOffset(1,-1)
    
    def moveS(self):
        return self.moveToOffset(0,1)

    def moveSW(self):
        return self.moveToOffset(-1,1)

    def moveSE(self):
        return self.moveToOffset(1,1)

    def moveW(self):
        return self.moveToOffset(-1,0)

    def moveE(self):
        return self.moveToOffset(1,0)

    @abc.abstractmethod
    def moveToLocation(self,loc):
        raise NotImplementedError()
    
    def moveToOffset(self,x,y):
        src_tile=self.parent
        assert(src_tile)
        loc=(src_tile.loc[0]+x,src_tile.loc[1]+y)
        self.facing=(x,y)
        return self.moveToLocation(loc)

    def idle(self):
        self.facing=(0,0)
        return False

    def getFOV(self):
        if self.facing==(0,0):
            return 2*math.pi
        return math.pi/1.5
