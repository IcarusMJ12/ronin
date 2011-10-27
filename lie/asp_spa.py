#!/usr/bin/env python
# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

from numpy import array as ar
from numpy import matrix
from math import sqrt, pi, sin, cos
import logging
from exceptions import AssertionError

SQRT3_4=sqrt(3.0/4)

__all__=['RayPair', 'Locus','FOV']

logger=logging.getLogger(__name__)

def _clockwiseCompare(p1, p2):
    """Compares items by clockwise direction starting at the positive y axis.
    y axis is used because it is vertically aligned."""
    (x1,y1)=(p1[0],p1[1])
    (x2,y2)=(p2[0],p2[1])
    if x1>0:
        if x2<=0:
            return -1
        if y1 > y2:
            return -1
        if y1 == y2:
            return 0
        return 1
    if x2>0:
        return 1
    if y2 > y1:
        return -1
    if y2 == y1:
        return 0
    return 1

def getClockwiseEquivalenceClass(coord):
    """Returns a tuple representing the locus's angle from the origin, as a sort of poor man's polar coordinates."""
    (x,y)=coord
    sign= x>=0
    try:
        slope=y/x
    except ZeroDivisionError:
        slope=float('inf' if y>0 else '-inf')
    #return (sign, -slope if sign else slope)
    return (sign, -slope)

def rayPairFromFF(facing, fov):
    fov=2*pi-fov
    reflex=fov>=pi
    facing=Locus.T.dot((facing[0],facing[1],1.0))
    logger.debug('facing:'+str(facing)+' reflex: '+str(reflex))
    facing=-facing[0:2]
    #left, right = [ar((-facing[1]/2.0,facing[0]/2.0)), facing], [ar((facing[1]/2.0,-facing[0]/2.0)), facing]
    left, right = [ar((0,0)), facing], [ar((0,0)), facing]
    # rotation matrix = [[ cos -sin ] [ sin cos ]] , rotates COUNTERCLOCKWISE
    ltheta, rtheta = fov/2.0, -fov/2.0
    cos_theta=cos(rtheta)
    sin_ltheta=sin(ltheta)
    sin_rtheta=-sin_ltheta
    rotate_left=ar(((cos_theta, sin_rtheta),(sin_ltheta, cos_theta)))
    rotate_right=ar(((cos_theta, sin_ltheta),(sin_rtheta, cos_theta)))
    #left, right = (rotate_left*matrix(left[0]).transpose(), rotate_left*matrix(left[1]).transpose()),(rotate_right*matrix(right[0]).transpose(), rotate_right*matrix(right[1]).transpose())
    left, right = (left[0], rotate_left*matrix(left[1]).transpose()),(right[0], rotate_right*matrix(right[1]).transpose())
    #left, right = (ar(left[0].transpose())[0], ar(left[1].transpose())[0]), (ar(right[0].transpose())[0],ar(right[1].transpose())[0])
    left, right = (left[0], ar(left[1].transpose())[0]), (right[0],ar(right[1].transpose())[0])
    logger.debug("left:"+str(left)+" right:"+str(right))
    rp=RayPair(None, None, reflex)
    (rp._left, rp._right)=(left, right)
    return rp

class RayPair(object):
    """A vector pair is defined by two pairs of points and whether these lines form a reflex angle."""
    id=1
    count_processed=0
    EPSILON=0.0000001 #woo yay, trying to compensate for floating point computation inaccuracies

    def __init__(self, left, right, reflex=False):
        self.left=left  #left ray, as a (point, unit vector)
        self.right=right #right ray, as a (point, unit vector)
        self.is_reflex=reflex #when considered from the intersection, whether the vector pair makes a reflex angle (>pi)
        self.is_world=False #whether the linepair angle is 2*pi, i.e. the world
        if logger.level<=logging.INFO:
            self.culprits=[] #debug info
        self.id=RayPair.id
        RayPair.id+=1
        if logger.level==logging.DEBUG:
            logger.debug("Created linepair "+str(self.id))
    
    def _vectorize(self, segment):
        if segment is None:
            return None
        seg=ar(segment)
        vector=seg[1]-seg[0]
        vector/=sqrt(sum(pow(vector,2)))
        seg[1]=vector
        return seg

    def setLeft(self, left):
        self._left=self._vectorize(left)
    
    def getLeft(self):
        return self._left

    def setRight(self, right):
        self._right=self._vectorize(right)
    
    def getRight(self):
        return self._right

    left=property(getLeft, setLeft)
    right=property(getRight, setRight)

    def __repr__(self):
        r="RayPair<"+str(self.id)+" l:"+str(self.left[0])+","+str(self.left[1])+" r:"+str(self.right[0])+","+str(self.right[1])
        if self.is_world:
            r+=" (W)"
        if self.is_reflex:
            r+=" (ref)"
        r+=">"
        if logger.level<=logging.INFO:
            for c in self.culprits:
                r+="\n\t"+str(c)
        return r

    def __cmp__(self, other):
        """Sort by clockwise direction."""
        return _clockwiseCompare(self.right[0], other.right[0])
    
    def mergeLocus(self, locus, line):
        """Updates the RayPair to contain the LOS-blocking locus provided."""
        if logger.level<=logging.INFO:
            self.culprits.append(locus)
        if logger.level==logging.DEBUG:
            logger.debug("Merging locus "+str(locus)+' '+str(line)+" into linepair "+str(self.id))
        if line==3:
            self.is_world = True
            return self
        if line==1:
            if RayPair._cross(self.right[0],self.left[0],locus.n) <= RayPair.EPSILON:
                self.is_reflex=True
            self.left=(locus.n, locus.coord+locus.n)
        else:
            if RayPair._cross(self.left[0],self.right[0],-locus.n) >= -RayPair.EPSILON:
                self.is_reflex=True
            self.right=(-locus.n, locus.coord-locus.n)
        return self
    
    @classmethod
    def mergePairsByLocus(self, lp1_tuplet, lp2_tuplet):
        """Merges two RayPairs by a LOS-blocking locus that they share."""
        (lp1,lp1_line)=lp1_tuplet
        (lp2,lp2_line)=lp2_tuplet
        if logger.level==logging.DEBUG:
            logger.debug("Merging linepairs "+str(lp1.id)+' '+str(lp1_line)+" and "+str(lp2.id)+' '+str(lp2_line))
        assert lp1!=lp2,str(lp1)+'=='+str(lp2)
        right=None
        left=None
        reflex=(lp1.is_reflex or lp2.is_reflex)
        assert lp1_line!=lp2_line, str(lp1_line)+'=='+str(lp2_line)
        if lp1_line==1:
            left,right = lp2.left,lp1.right
            if not reflex and RayPair._cross(lp1.right[0],lp1.left[0],lp2.left[0]) <= RayPair.EPSILON:
                reflex=True
        else:
            left,right = lp1.left,lp2.right
            if not reflex and RayPair._cross(lp2.right[0],lp2.left[0],lp1.left[0]) <= RayPair.EPSILON:
                reflex=True
        lp=RayPair(None,None,reflex)
        lp._left=left
        lp._right=right
        if logger.level<=logging.INFO:
            lp.culprits=lp1.culprits
            lp.culprits.extend(lp2.culprits)
        return lp

    def calculateCover(self, l):
        """Returns a tuple in the form (cover_amount: 0.0-1.0, side: 1 if left line, 2 if right line, 3 if both, 0 if doesn't matter)"""
        RayPair.count_processed+=1
        if self.is_world:
            if logger.level==logging.DEBUG:
                logger.debug("We are world!")
            return (1.0,0)
        if not self.is_reflex:
            n=-(self.right[0]+self.left[0])/2
            if RayPair._cross(self.left[0],self.right[0], l.coord+n)<0:
                if logger.level==logging.DEBUG:
                    logger.debug("We are south of the line.")
                return (-1,2) #assuming next linepair is right
        right=RayPair._crossVectors(self.right[1],l.coord-self.right[0]*2) #negative if locus entirely to the right
        if logger.level==logging.DEBUG:
            logger.debug('\t\tright:'+str(right))
        if right > -RayPair.EPSILON and right < RayPair.EPSILON: #account for potential floating point error to arrive at a "good enough" answer
            right=0 #tangent
        elif right > 1.0-RayPair.EPSILON:
            right=1 #fully contained
        if not self.is_reflex:
            if right < 0:
                return (-1,2)
        left=-RayPair._crossVectors(self.left[1],l.coord-self.left[0]*2) #negative if locus is entirely to the left
        if logger.level==logging.DEBUG:
            logger.debug('\t\tleft:'+str(left))
        if left > -RayPair.EPSILON and left < RayPair.EPSILON:
            left=0
        elif left > 1.0-RayPair.EPSILON:
            left=1
        if not self.is_reflex:
            if left < 0:
                return (-1,1)
            if left < right:
                return (left, 1)
            if right < 1:
                return (right, 2)
            return (1.0,0)
        #i guess we're a reflex angle, so things get harder...
        if left < 0 and right < 0:
            return (-1,2)
        if(self.left[1].dot(self.right[1])<0):  #angle between vectors between 90 and 270, i.e. possibly 180
            if left == 1 and right == 1:
                return (1.0, 0)
            if left - RayPair.EPSILON > right:
                return (left, 1)
            if left + RayPair.EPSILON > right: #typically l and r are the same line...
                if RayPair._cross((0,0),(-self.left[1][1],self.left[1][0]),l.coord)<0:
                    return (left, 1)
            return (right, 2)
        if left == 1 or right == 1:
            return (1.0, 0)
        if left>=0:
            if right>=0:
                return ((left,right),3)
            return (left,1)
        return (right,2)
    
    @classmethod
    def _cross(self, p1, p2, p3):
        """Returns positive value, 0, or negative value, if p3 is left, on, or right of the line going from p1 to p2."""
        return (p2[0]-p1[0])*(p3[1]-p1[1])-(p2[1]-p1[1])*(p3[0]-p1[0])

    @classmethod
    def _crossVectors(self, v1, v2):
        """Returns positive value, 0, or negative value, if v2 is counter-clockwise, on, or clockwise of v2."""
        return v1[0]*v2[1]-v1[1]*v2[0]

class Locus(object):
    """Generally speaking, a circle positioned using Cartesian coordinates that may block line of sight."""
    T=ar([[-SQRT3_4, SQRT3_4, 0.0],[-0.5, -0.5, 0.0], [0.0, 0.0, 1.0]]) #hex -> cartesian

    def __init__(self, coord_blocks_triple):
        (x, y, self.blocksLOS)=coord_blocks_triple
        self.id=(x,y)
        self.d_2=x*x+y*y-x*y
        coord=Locus.T.dot((x,y,1))
        factor=sqrt(coord[0]*coord[0]+coord[1]*coord[1])*2.0
        n=ar((-coord[1]/factor, coord[0]/factor)) #rotate -pi/2 and scale producing the 'left' normal
        self.coord=coord[0:2]
        self.n=n
        self.cover_left=0.0
        self.cover_right=0.0

    def __cmp__(self, other):
        """Comparison by distance from origin and clockwise angle around the origin from the y axis."""
        comp=self.d_2.__cmp__(other.d_2)
        if comp:
            return comp
        return _clockwiseCompare(self.coord, other.coord)

    def distance_2(self, other):
        """Computed in hex coordinates for quickness and accuracy due to integer arithmetic."""
        dx=(other.id.x-self.id.x)
        dy=(other.id.y-self.id.y)
        return dx*dx+dy*dy-dx*dy
    
    def __repr__(self):
        return "Locus<x:"+str(self.id[0])+" y:"+str(self.id[1])+" "+str(self.coord)+" d^2:"+str(self.d_2)+" "+str(self.cover_left)+"/"+str(self.cover_right)+" ("+str(self.blocksLOS)+")>"
    
    def toRayPair(self):
        """Returns the relevant RayPair for this locus, used if this locus blocks line of sight."""
        lp=RayPair((self.n,self.coord+self.n),(-self.n,self.coord-self.n),False)
        if logger.level<=logging.INFO:
            lp.culprits.append(self)
        if logger.level==logging.DEBUG:
            logger.debug("Created linepair "+str(lp.id)+" from locus "+str(self))
        return lp

class FOV(object):
    """Field of View calculator."""
    def _processOrigin(self, loci, processed_loci):
        while len(loci) and loci[-1].d_2==0:
            l=loci.pop()
            l.cover_left=0.0 #an object cannot provide cover for itself
            l.cover_right=0.0
            processed_loci.append(l)
    
    def _getEquivalenceClasses(self, loci, offset):
        equivalence_classes={}
        for locus in loci:
            key=getClockwiseEquivalenceClass(offset+locus.coord)
            try:
                equivalence_classes[key].append(locus)
            except KeyError:
                equivalence_classes[key]=[locus]
        return equivalence_classes

    def _processInitialFOV(self, loci, facing, fov):
        raypair=rayPairFromFF(facing, fov)
        for l in loci:
            if l.id!=(0,0):
                cover_left, cover_right = 0, 0
                (cover, line)=raypair.calculateCover(l)
                if line==3:
                    cover_left, cover_right = cover
                elif line==0:
                    cover_left, cover_right = cover, cover
                else:
                    cover=max(0.0, cover)
                    if line==1:
                        cover_left = cover
                    else:
                        cover_right = cover
                l.cover_left, l.cover_right = max(l.cover_left, 1.0 if cover_left>0.866 else cover_left), max(l.cover_right, 1.0 if cover_right>0.866 else cover_right)
        
    def calculateHexFOV(self, me, world, fov=None, facing=None):
        """Calculate Field of View from triples of the form (x,y,blocksLOS) where x and y are in hex coordinates."""
        result=None
        for result in self.hexFOVGenerator(me, world, fov, facing, yield_each_iteration=False):
            pass
        return result[0]

    def hexFOVGenerator(self, me, world, fov=None, facing=None, yield_each_iteration=True):
        """Auxiliary function for calculateHexFOV."""
        loci=[Locus((i[0]-me[0],i[1]-me[1],i[2])) for i in world]
        loci.sort(reverse=True)
        ret=[]
        self._processOrigin(loci, ret)
        RayPair.id=1
        linepairs=[]
        len_linepairs=len(linepairs)
        if len_linepairs:
            linepairs.sort()
            linepairs=[[l,0] for l in linepairs] #adding the 'freshness' metric
            #freshness affects whether the line(s) actually provide cover or are only considered as neighbors to blocking loci
            #freshness can be 1 (left is fresh), 2 (right is fresh), 3 (both), or 0 (neither), hence initially all lines are 'stale'
        #process everything else
        d_2=1
        lp_index=0 #start with the 'leftmost' linepair again
        while True:
            assert sum([lp[0].is_reflex for lp in linepairs])<2, 'sum>=2'
            wc=sum([lp[0].is_world for lp in linepairs])
            if wc:
                if len_linepairs!=1:
                    logger.error(str(wc)+' '+str(len_linepairs)+' '+str(len(linepairs)))
                    for lp in linepairs:
                        logger.error(str(lp[0]))
                    raise AssertionError("More than one linepair when world linepair exists.")
            try:
                l=loci.pop()
            except IndexError:
                break
            if logger.level==logging.DEBUG:
                logger.debug(str(l)+' '+str(len_linepairs))
                logger.debug('------------------')
                logger.debug('current linepairs:')
                for linepair in linepairs:
                    logger.debug(str(linepair))
                logger.debug('------------------')
            if l.d_2 > d_2:
                d_2=l.d_2
                lp_index=0 #restarting
                for x in linepairs:
                    x[1]=0 #distance increase means all lines are now 'stale'
            processed=False
            direction=0
            line1=None
            for ignored in xrange(len_linepairs):
                (lp1, fresh1)=linepairs[lp_index]
                (cover1, line1) = lp1.calculateCover(l)
                if logger.level==logging.DEBUG:
                    logger.debug('lp1 ['+str(lp_index)+']: '+str(lp1))
                    logger.debug('fresh1: '+str(fresh1)+' cover1: '+str(cover1)+' line1: '+str(line1))
                if line1==3: #either reflex angle intersecting same locus from two different sides, or result of circle being > unit
                    (cover1,cover2)=(cover1[0],cover1[1])
                    l.cover_right=max(cover1,0.0)*(not fresh1&1)
                    l.cover_left=max(cover2,0.0)*(not fresh1&2)
                    if l.blocksLOS and lp1.is_reflex:
                        lp1.is_world = True
                    processed=True
                    break
                if cover1 == 1: #guaranteed to be stale line by nature of the algorithm (i.e. adjacencies at same distance cannot completely occlude each other)
                    if line1==2:
                        l.cover_left=cover1
                    else:
                        l.cover_right=cover1
                    processed=True
                    break
                (lp2,fresh2,cover2,line2)=(None,0,-1,0)
                if cover1>=0: #jackpot?
                    if len_linepairs>1:
                        if line1==1 and direction!=1:
                            if logger.level==logging.DEBUG:
                                debug_index=(lp_index-1)%len_linepairs
                            (lp2, fresh2)=linepairs[(lp_index-1)%len_linepairs]
                            (cover2, line2) = lp2.calculateCover(l)
                        elif direction!=-1: #line1==2
                            if logger.level==logging.DEBUG:
                                debug_index=(lp_index-1)%len_linepairs
                            (lp2, fresh2)=linepairs[(lp_index+1)%len_linepairs]
                            (cover2, line2) = lp2.calculateCover(l)
                        if logger.level==logging.DEBUG:
                            logger.debug('lp2: ['+str(debug_index)+']'+str(lp2))
                            logger.debug('fresh2: '+str(fresh2)+' cover2: '+str(cover2)+' line2: '+str(line2))
                        if cover2>=0 and line2==line1:
                            logger.error(str(me))
                            logger.error('locus: '+str(l))
                            logger.error('line1, len(linepairs), len_linepairs:'+str(line1)+' '+str(len(linepairs))+' '+str(len_linepairs))
                            logger.error('lp1: '+str(lp1))
                            logger.error('lp2: '+str(lp2))
                            raise AssertionError("line1 == line2")
                        assert line2!=3, 'line2==3'
                    if line1==2:
                        l.cover_right=max(cover1,0.0)*(not fresh1&line1)
                        l.cover_left=max(cover2,0.0)*(not fresh2&line2)
                    else:
                        l.cover_left=max(cover1,0.0)*(not fresh1&line1)
                        l.cover_right=max(cover2,0.0)*(not fresh2&line2)
                    if l.blocksLOS:
                        if cover2>=0:
                            lp=RayPair.mergePairsByLocus((lp1, line1), (lp2, line2))
                            if logger.level<=logging.INFO:
                                lp.culprits.append(l)
                            linepairs[lp_index]=[lp,fresh1|fresh2]
                            if line1==1:
                                linepairs.pop((lp_index-1)%len_linepairs)
                            else:
                                linepairs.pop((lp_index+1)%len_linepairs)
                            len_linepairs-=1
                            lp_index=(lp_index-1)%len_linepairs
                        else:
                            lp1.mergeLocus(l, line1)
                            linepairs[lp_index][1]|=line1
                    processed=True
                    break #if cover1>=0
                if not direction:
                    if line1 == 1:
                        direction=-1
                    elif line1 == 2:
                        direction=1
                elif (direction==-1 and line1 !=1) or (direction==1 and line1 !=2):
                    break
                lp_index=(lp_index+direction)%len_linepairs
            if not processed and l.blocksLOS:
                linepairs.append([l.toRayPair(),3])
                len_linepairs+=1
                linepairs.sort()
            ret.append(l)
            if yield_each_iteration:
                (x,y)=(me[0],me[1])
                try:
                    next_locus = loci[-1]
                    yield ([((i.id[0]+x, i.id[1]+y), min(i.cover_right+i.cover_left,1.0), i.d_2) for i in ret],next_locus.id)
                except IndexError:
                    pass
        (x,y)=(me[0],me[1])
        logger.debug("RayPairs processed: "+str(RayPair.count_processed))
        if fov is not None and facing is not None:
            self._processInitialFOV(ret, facing, fov)
        yield ([((i.id[0]+x, i.id[1]+y), min(i.cover_right+i.cover_left,1.0), i.d_2) for i in ret],None)

if __name__ == '__main__':
    import unittest
    import copy
    from sys import argv
    from getopt import getopt, GetoptError

    def usage():
        print "Usage: "
        print ""
        print '\t'+argv[0]+' -h|--help'
        print '\t'+argv[0]+' [-u|--unit] [<test> ...]'
        print '\t'+argv[0]+' -r|--regression [-s|--seeds <X>[-<Y>]] [-g|--geometry <W>x<H>]'
        print '\t'+argv[0]+' -t|--step-through -s|--seeds <X>'

    class FOVTest(unittest.TestCase):
        """Performs a series of tests by running FOV's calculateHexFOV function on a 5x5 world with different scenarios."""

        def setUp(self):
            """Initializes FOV and sets up base_world and cover constants."""
            self.fov=FOV()
            self.base_world=[
                    [0,0,0], [1,0,0], [2,0,0], [3,0,0], [4,0,0],
                    [0,1,0], [1,1,0], [2,1,0], [3,1,0], [4,1,0],
                    [0,2,0], [1,2,0], [2,2,0], [3,2,0], [4,2,0],
                    [0,3,0], [1,3,0], [2,3,0], [3,3,0], [4,3,0],
                    [0,4,0], [1,4,0], [2,4,0], [3,4,0], [4,4,0],
                    ]
            self.almost_cover=-SQRT3_4+1 #tile edge shaving

        def _checkResult(self, result, *args):
            """Verifies that the tiles returned have correct cover.
            Accepts the result of calculateHexFOV as the first parameter, followed by location_tuples, cover_value in unpacked form.
            location_tuples must be lists, individual tuples, or the special parameter 'None' signifying all otherwise unmatched locations.
            e.g. _checkResult(result, [(1,2),(3,4)], 1, (2,4), 0.5, None, 0)"""
            tilesets,cover_values=list(args[0::2]),list(args[1::2])
            default_cover=None
            try:
                idx=tilesets.index(None)
                tilesets.pop(idx)
                default_cover=cover_values.pop(idx)
            except ValueError:
                pass
            l=len(tilesets)
            assert l==len(cover_values),'l!=len(cover_values)'
            for i in xrange(l):
                if tilesets[i] and not isinstance(tilesets[i],list):
                    tilesets[i]=[tilesets[i]]
            for i in result:
                found=False
                for j in xrange(l):
                    if tilesets[j] and i[0] in tilesets[j]:
                        self._assertEqualCover(i,cover_values[j])
                        found=True
                        break
                if not found and default_cover is not None:
                    self._assertEqualCover(i,default_cover)

        def _assertEqualCover(self, tile, cover):
            """Tests that the tile's cover is exactly 1 or 0 if the cover is 1 or 0, or else is equal to the value of cover to within 12 decimal places."""
            if cover>0 or cover <1:
                self.assertAlmostEqual(tile[1], cover, 12, "Expected cover "+str(cover)+" for "+str(tile[0])+", got "+str(tile[1]))
            else:
                self.assertEqual(tile[1], cover, "Expected cover "+str(cover)+" for "+str(tile[0])+", got "+str(tile[1]))

        def test01_Singular(self):
            """Performing basic sanity check"""
            self.assertEqual(self.fov.calculateHexFOV([0,0],[[0,0,0]]),[((0,0),0,0)])

        def test02_Distance(self):
            """Verifying that FOV computes distances correctly"""
            me=(2,2)
            world=self.base_world
            res=self.fov.calculateHexFOV(me,world)
            for i in res:
                self.assertEqual(i[2],pow(i[0][0]-me[0],2)+pow(i[0][1]-me[1],2)-(i[0][0]-me[0])*(i[0][1]-me[1]))

        def test03_CardinalE(self):
            """Testing East wall"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[13][2]=1 #(3,2) E
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(4,2),1,[(4,3),(3,1),(4,1)],self.almost_cover,None,0)

        def test04_CardinalN(self):
            """Testing North wall"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[17][2]=1 #(2,3) N
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(2,4),1,[(1,3),(1,4),(3,4)],self.almost_cover,None,0)

        def test05_CardinalW(self):
            """Testing West wall"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[11][2]=1 #(1,2) W
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(0,2),1,[(0,1),(1,3),(0,3)],self.almost_cover,None,0)

        def test06_CardinalS(self):
            """Testing South wall"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[7][2]=1 #(2,1) S
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(2,0),1,[(1,0),(3,1),(3,0)],self.almost_cover,None,0)

        def test07_DiagonalNE(self):
            """Testing Northeast wall"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[18][2]=1 #(3,3) NE
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(4,4),1,[(4,3),(3,4)],self.almost_cover,None,0)
    
        def test08_DiagonalSW(self):
            """Testing Southwest wall"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[6][2]=1 #(1,1) SW
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(0,0),1,[(0,1),(1,0)],self.almost_cover,None,0)

        def test09_1_3(self):
            """Testing wall at (-1,1) to character"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[16][2]=1 #(1,3)
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(0,4),1,[(0,3),(1,4)],0.5,None,0)

        def test10_EandN(self):
            """Testing East and North walls (not adjacent)"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[13][2]=1 #(3,2) E
            world[17][2]=1 #(2,3) N
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(4,2),(2,4)],1,[(4,3),(3,1),(4,1),(1,3),(1,4),(3,4)],self.almost_cover,None,0)

        def test11_NandSW(self):
            """Testing North and Southwest walls (not adjacent)"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[17][2]=1 #(2,3) N
            world[6][2]=1 #(1,1) SW
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(2,4),(0,0)],1,[(1,3),(1,4),(3,4),(0,1),(1,0)],self.almost_cover,None,0)

        def test12_EandW(self):
            """Testing East and West walls (opposite sides)"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[13][2]=1 #(3,2) E
            world[11][2]=1 #(1,2) W
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(4,2),(0,2)],1,[(4,3),(3,1),(4,1),(0,1),(1,3),(0,3)],self.almost_cover,None,0)

        def test13_EandNE(self):
            """Testing East and Northeast walls (adjacent)"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[13][2]=1 #(3,2) E
            world[18][2]=1 #(3,3) NE
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(4,2),(4,3),(4,4)],1,[(3,1),(4,1),(3,4)],self.almost_cover,None,0)

        def test14_NandW(self):
            """Testing North and West walls (adjacent)"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[17][2]=1 #(2,3) N
            world[11][2]=1 #(1,2) W
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(0,2),(0,3),(0,4),(1,3),(1,4),(2,4)],1,[(0,1),(3,4)],self.almost_cover,None,0)

        def test15_Nand1_3(self):
            """Testing walls at (0,1) [East] and (-1,1) to character (adjacent)"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[17][2]=1 #(2,3) N
            world[16][2]=1 #(1,3)
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(2,4),(1,4),(0,4)],1,(0,3),0.5,[(1,3),(3,4)],self.almost_cover,None,0)

        def test16_Wand1_3(self):
            """Testing walls at (-1,0) [West] and (-1,1) to character (adjacent)"""
            me=(2,2)
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[11][2]=1 #(1,2) W
            world[16][2]=1 #(1,3)
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(0,2),(0,3),(0,4)],1,(1,4),0.5,[(1,3),(0,1)],self.almost_cover,None,0)

        def test17_NN(self):
            """Testing two blocking tiles in a line"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[17][2]=1 #(2,3) N
            world[22][2]=1 #(2,4) NN
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,(2,4),1,[(1,3),(1,4),(3,4)],self.almost_cover,None,0)

        def test18_NandWand1_3(self):
            """Testing a fully contained tile"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[17][2]=1 #(2,3) N
            world[11][2]=1 #(1,2) W
            world[16][2]=1 #(1,3)
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(0,2),(0,3),(0,4),(1,3),(1,4),(2,4)],1,[(0,1),(3,4)],self.almost_cover,None,0)

        def test19_PiX1(self):
            """Trying a North-facing 180 degree angle from the X-axis"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[13][2]=1 #(3,2) E
            world[18][2]=1 #(3,3) NE
            world[17][2]=1 #(2,3) N
            world[11][2]=1 #(1,2) W
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(0,0),(1,0),(1,1),(2,0),(2,1),(2,2),(3,0),(4,0),(3,2),(3,3),(2,3),(1,2)],0,[(0,1),(3,1),(4,1)],self.almost_cover,None,1)

        def test20_PiX2(self):
            """Trying a South-facing 180 degree angle from the X-axis"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[13][2]=1 #(3,2) E
            world[7][2]=1 #(2,1) S
            world[6][2]=1 #(1,1) SW
            world[11][2]=1 #(1,2) W
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(4,4),(3,4),(3,3),(2,4),(2,3),(2,2),(1,4),(0,4),(3,2),(2,1),(1,1),(1,2)],0,[(4,3),(1,3),(0,3)],self.almost_cover,None,1)

        def test21_PiXY1(self):
            """Trying an East-facing 180 degree angle from XY"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[18][2]=1 #(3,3) NE
            world[13][2]=1 #(3,2) E
            world[7][2]=1 #(2,1) S
            world[6][2]=1 #(1,1) SW
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(0,2),(0,3),(0,4),(1,1),(1,2),(1,3),(1,4),(2,1),(2,2),(2,3),(2,4),(3,2),(3,3)],0,[(0,1),(3,4)],self.almost_cover,None,1)

        def test22_PiXY2(self):
            """Trying a West-facing 180 degree angle from XY"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[18][2]=1 #(3,3) NE
            world[17][2]=1 #(2,3) N
            world[11][2]=1 #(1,2) W
            world[6][2]=1 #(1,1) SW
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(4,2),(4,1),(4,0),(3,3),(3,2),(3,1),(3,0),(2,3),(2,2),(2,1),(2,0),(1,2),(1,1)],0,[(4,3),(1,0)],self.almost_cover,None,1)

        def test23_almostWorld1(self):
            """Walling off 5 out of 6 nearby tiles"""
            me=(2,2)
            world=copy.deepcopy(self.base_world)
            world[18][2]=1 #(3,3) NE
            world[17][2]=1 #(2,3) N
            world[11][2]=1 #(1,2) W
            world[6][2]=1 #(1,1) SW
            world[7][2]=1 #(2,1) S
            res=self.fov.calculateHexFOV(me,world)
            self._checkResult(res,[(1,1),(1,2),(2,1),(2,2),(2,3),(3,2),(3,3),(4,0),(4,1),(4,2)],0,[(3,0),(3,1),(4,3)],self.almost_cover,None,1)

    (opts,args)=(None,None)
    unit=False
    regression=False
    step_through=False
    seeds=(0,255)
    geometry=(25,25)
    try:
        opts, args = getopt(argv[1:], "hurs:g:t", ['help','unit','regression','seeds','geometry','step-through'])
        for opt, arg in opts:
            if opt in ('-h','--help'):
                usage()
                exit(0)
            if opt in ('-u','--unit'):
                unit=True
            elif opt in ('-r','--regression'):
                regression=True
            elif opt in ('-s','--seeds'):
                if '-' in arg:
                    seeds=arg.split('-')
                else:
                    seeds=(arg,arg)
            elif opt in ('-g','--geometry'):
                geometry=arg.split('x')
                geometry=(int(geometry[0]),int(geometry[1]))
            elif opt in ('-t','--step-through'):
                step_through=True
        if unit and regression and step_through:
            raise GetoptError
        if not regression and not step_through:
            unit=True
    except GetoptError:
        usage()
        exit(1)
    if unit:
        suite = None
        if len(args)>0:
            suite = unittest.TestSuite(map(FOVTest,args))
        else:
            suite = unittest.TestLoader().loadTestsFromTestCase(FOVTest)
        unittest.TextTestRunner(verbosity=2).run(suite)
    elif regression:
        from mapgen import CellularAutomata
        from objects import Floor, Wall
        from random import Random

        logger.setLevel(logging.INFO)

        fov=FOV()
        errors=[]
        successes=0
        for seed in xrange(int(seeds[0]),int(seeds[1])+1):
            print "processing world for seed "+str(seed)
            generator=CellularAutomata(Random(seed),Floor,Wall)
            level=generator.generateLevel(geometry[0],geometry[1])
            tiles=[level[geometry[0]/2,geometry[1]/2]]
            done_tiles=[]
            while tiles[0].blocksLOS():
                tile=tiles.pop(0)
                tiles.extend([t for t in level.getNeighbors(tile.loc) if t not in tiles and t not in done_tiles])
                done_tiles.append(tile)
            tile=tiles[0]
            world=[(i,j,level[i,j].blocksLOS()) for i in xrange(level.width) for j in xrange(level.height)]
            me=(tile.loc[0],tile.loc[1],False)
            try:
                result=fov.calculateHexFOV(me,world)
                for item in result:
                    if item[1]>1:
                        raise AssertionError("cover > 1")
                successes+=1
            except AssertionError as e:
                errors.append((seed,geometry,e,me,world,level))
        len_errors=len(errors)
        if len_errors>0:
            print "Failed with "+str(len_errors)+" errors."
            for error in errors:
                print "seed:"+str(error[0])+" geometry:"+str(error[1])+" error:"+str(error[2])
                print '\t'+str(error[3])
                print '\t'+str(error[4])
            exit(1)
        else:
            print str(successes)+" tests completed successfully."
            exit(0)
    elif step_through:
        from random import Random
        import sys

        from mapgen import CellularAutomata
        from objects import Floor, Wall
        import ui
        from gridview import HexGridView
        from perception import PGrid
        import globals
        from __init__ import init

        is_debug=True
        logger.setLevel(logging.DEBUG)

        if seeds[0]!=seeds[1]:
            usage()
            exit(1)
        init('asp_spa.conf')
        generator=CellularAutomata(Random(int(seeds[0])),Floor,Wall)
        level=generator.generateLevel(geometry[0],geometry[1])
        tiles=[level[geometry[0]/2,geometry[1]/2]]
        done_tiles=[]
        while tiles[0].blocksLOS():
            tile=tiles.pop(0)
            tiles.extend([t for t in level.getNeighbors(tile.loc) if t not in tiles and t not in done_tiles])
            done_tiles.append(tile)
        tile=tiles[0]
        world=[(i,j,level[i,j].blocksLOS()) for i in xrange(level.width) for j in xrange(level.height)]
        me=(tile.loc[0],tile.loc[1],False)
        perception=PGrid(level, None)
        for t in perception.getTiles():
            t.was_seen=True
        worldview=HexGridView(level, perception)
        worldview.center(worldview[tile.loc].rect)
        worldview.draw()
        for result in perception.fov.hexFOVGenerator(me, world):
            for r in result[0]:
                perception[r[0][0],r[0][1]].d2=r[2]
                if r[1]>1:
                    logger.error(str(me))
                    logger.error(str(r))
                    raise AssertionError("cover > 1")
                perception[r[0][0],r[0][1]].cover=r[1]
            try:
                next_tile=perception[me[0]+result[1][0],me[1]+result[1][1]]
                next_tile.d2=255
                next_tile.cover=0
            except TypeError:
                pass
            worldview.draw()
            print '[press any key...]'
            sys.stdin.read(1)
