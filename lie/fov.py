#!/usr/bin/env python
from numpy import array as ar
from math import sqrt
import logging
from exceptions import AssertionError

SQRT3_4=sqrt(3.0/4)
is_debug=False

__all__=['LinePair', 'Locus','FOV']

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

class LinePair(object):
    id=1
    EPSILON=0.001 #woo yay, trying to compensate for floating point computation inaccuracies

    """A line pair is defined by two pairs of points and whether these lines form a reflex angle."""
    def __init__(self, left, right, reflex=False):
        self.left=left  #left line, as a pair of points
        self.right=right #right line, as a pair of points
        self.is_reflex=reflex #when considered from the intersection, whether the line pair makes a reflex angle (>pi)
        self.is_world=False #whether the linepair angle is 2*pi, i.e. the world
        self.culprits=[] #debug info
        self.id=LinePair.id
        LinePair.id+=1
        if is_debug:
            logging.debug("Created linepair "+str(self.id))
    
    def _normalize(self, segment):
        seg=ar(segment)
        vector=seg[1]-seg[0]
        vector/=sqrt(sum(pow(vector,2)))
        seg[1]=seg[0]+vector
        return seg

    def setLeft(self, left):
        self._left=self._normalize(left)
    
    def getLeft(self):
        return self._left

    def setRight(self, right):
        self._right=self._normalize(right)
    
    def getRight(self):
        return self._right

    left=property(getLeft, setLeft)
    right=property(getRight, setRight)

    def __repr__(self):
        r="LinePair<"+str(self.id)+" l:"+str(self.left[0])+","+str(self.left[1])+" r:"+str(self.right[0])+","+str(self.right[1])
        if self.is_world:
            r+=" (W)"
        elif self.is_reflex:
            r+=" (ref)"
        r+=">"
        for c in self.culprits:
            r+="\n\t"+str(c)
        return r

    def __cmp__(self, other):
        """Sort by clockwise direction."""
        return _clockwiseCompare(self.right[0], other.right[0])
    
    def mergeLocus(self, locus, line):
        """Updates the LinePair to contain the LOS-blocking locus provided."""
        self.culprits.append(locus)
        if is_debug:
            logging.debug("Merging locus "+str(locus)+' '+str(line)+" into linepair "+str(self.id))
        if line==3:
            self.is_world=True
            return self
        if line==1:
            if LinePair._cross(self.right[0],self.left[0],locus.n) <= 0:
                self.is_reflex=True
            self.left=(locus.n, locus.coord+locus.n)
        else:
            if LinePair._cross(self.left[0],self.right[0],-locus.n) >= 0:
                self.is_reflex=True
            self.right=(-locus.n, locus.coord-locus.n)
        return self
    
    @classmethod
    def mergePairsByLocus(self, lp1_tuplet, lp2_tuplet):
        """Merges two LinePairs by a LOS-blocking locus that they share."""
        (lp1,lp1_line)=lp1_tuplet
        (lp2,lp2_line)=lp2_tuplet
        if is_debug:
            logging.debug("Merging linepairs "+str(lp1.id)+' '+str(lp1_line)+" and "+str(lp2.id)+' '+str(lp2_line))
        assert(lp1!=lp2)
        right=None
        left=None
        reflex=(lp1.is_reflex or lp2.is_reflex)
        assert(lp1_line!=lp2_line)
        if lp1_line==1:
            right=lp1.right
            left=lp2.left
            if not reflex and LinePair._cross(lp1.right[0],lp1.left[0],lp2.left[0]) <= 0:
                reflex=True
        else:
            left=lp1.left
            right=lp2.right
            if not reflex and LinePair._cross(lp2.right[0],lp2.left[0],lp1.left[0]) <= 0:
                reflex=True
        lp=LinePair(left,right,reflex)
        lp.culprits=lp1.culprits
        lp.culprits.extend(lp2.culprits)
        return lp

    def calculateCover(self, l):
        """Returns a tuple in the form (cover_amount: 0.0-1.0, side: 1 if left line, 2 if right line, 3 if both, 0 if doesn't matter)"""
        #TODO: compute actual cover
        if(self.is_world):
            if is_debug:
                logging.debug("We are world!")
            return (1.0,0)
        if not self.is_reflex:
            n=-(self.right[0]+self.left[0])/2
            if LinePair._cross(self.left[0],self.right[0], l.coord+n)<0:
                if is_debug:
                    logging.debug("We are south of the line.")
                return (-1,0)
        right=LinePair._cross(self.right[0],self.right[1],l.coord-self.right[0]) #negative if locus entirely to the right
        if is_debug:
            logging.debug('\t\t'+str(right))
        if right > -LinePair.EPSILON and right < LinePair.EPSILON: #account for potential floating point error to arrive at a "good enough" answer
            right=0
        if right > 1.0-LinePair.EPSILON:
            right=1
        if not self.is_reflex:
            if right < 0:
                return (-1,0)
        left=-LinePair._cross(self.left[0],self.left[1],l.coord-self.left[0]) #negative if locus is entirely to the left
        if is_debug:
            logging.debug('\t\t'+str(left))
        if left > -LinePair.EPSILON and left < LinePair.EPSILON:
            left=0
        if left > 1.0-LinePair.EPSILON:
            left=1
        if not self.is_reflex:
            if left < 0:
                return (-1,0)
            if left < 1 and left < right:
                return (left, 1)
            if right < 1:
                return (right, 2)
            return (1.0,0)
        #i guess we're a reflex angle, so things get harder...
        if left < 0 and right < 0:
            return (-1,0)
        if(self.left[0].dot(self.right[0])>0):  #angle between normals between -90 and 90
            if left == 1 and right == 1:
                return (1.0, 0)
            if left - LinePair.EPSILON > right:
                return (left, 1)
            if left + LinePair.EPSILON > right: #typically l and r are the same line...
                if LinePair._cross((0,0),self.left[0],l.coord)<0:
                    return (left, 1)
            return (right, 2)
        if left == 1 or right == 1:
            return (1.0, 0)
        if left>=0:
            if right>=0:
                return ((left,right),3)
            return (left,1)
        return (right,2)
    
    def _getPosition(self, point):
        """Returns 1, 0, or -1, if the point is left, between, or right of the line pair, respectively."""
        if(LinePair._cross(self.left[0], self.left[1], point)>0):
            return 1
        if self.is_reflex:
            return 0
        if(LinePair._cross(self.right[0], self.right[1], point)<0):
            return -1
        return 0

    @classmethod
    def _cross(self, p1, p2, p3):
        """Returns 1, 0, or -1, if p3 is left, on, or right of the line going from p1 to p2."""
        return (p2[0]-p1[0])*(p3[1]-p1[1])-(p2[1]-p1[1])*(p3[0]-p1[0])

class Locus(object):
    """Generally speaking, a circle positioned using Cartesian coordinates that may block line of sight."""
    T=ar([[-SQRT3_4, SQRT3_4, 0],[-0.5, -0.5, 0], [0, 0, 1]]) #hex -> cartesian

    def __init__(self, coord_blocks_triple):
        (x, y, self.blocksLOS)=coord_blocks_triple
        self.id=(x,y)
        self.d_2=x*x+y*y-x*y
        coord=Locus.T.dot((x,y,1))
        factor=sqrt(coord[0]*coord[0]+coord[1]*coord[1])*2.0
        n=ar((-coord[1]/factor, coord[0]/factor)) #rotate -pi/2 and scale producing the 'left' normal
        self.coord=coord[0:2]
        self.n=n
        self.cover=0.0

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
        return "Locus<x:"+str(self.id[0])+" y:"+str(self.id[1])+" ["+str(self.coord)+"] d^2:"+str(self.d_2)+" ("+str(self.blocksLOS)+")>"
    
    def toLinePair(self):
        """Returns the relevant LinePair for this locus, used if this locus blocks line of sight."""
        lp=LinePair((self.n,self.coord+self.n),(-self.n,self.coord-self.n),False)
        lp.culprits.append(self)
        if is_debug:
            logging.debug("Created linepair "+str(lp.id)+" from locus "+str(self))
        return lp

class FOV(object):
    """Field of View calculator."""
    def calculateHexFOV(self, me, world, linepairs=None):
        """Calculate Field of View from triples of the form (x,y,blocksLOS) where x and y are in hex coordinates."""
        logging.info(str(me))
        #if me==(42,23, False):
        #   globals()['is_debug']=True
        #else:
        #   globals()['is_debug']=False
        LinePair.id=1
        if linepairs is None:
            linepairs=[]
        loci=[Locus((i[0]-me[0],i[1]-me[1],i[2])) for i in world]
        loci.sort(reverse=True)
        if len(linepairs):
            linepairs.sort()
            linepairs=[[l,0] for l in linepairs] #adding the 'freshness' metric
            #freshness affects whether the line(s) actually provide cover or are only considered as neighbors to blocking loci
            #freshness can be 1 (left is fresh), 2 (right is fresh), 3 (both), or 0 (neither), hence initially all lines are 'stale'
        d_2=0
        ret=[]
        #process origin, i.e. myself in the world
        while len(loci) and loci[-1].d_2==0:
            l=loci.pop()
            l.cover=0.0 #an object cannot provide cover for itself
            ret.append(l)
        #process everything else
        d_2=1
        lp_index=0
        len_linepairs=len(linepairs)
        while True:
            assert(sum([lp[0].is_reflex for lp in linepairs])<2)
            wc=sum([lp[0].is_world for lp in linepairs])
            if wc:
                if len_linepairs!=1:
                    logging.error(str(wc)+' '+str(len_linepairs)+' '+str(len(linepairs)))
                    for lp in linepairs:
                        logging.error(str(lp[0]))
                    raise AssertionError("More than one linepair when world linepair exists.")
            try:
                l=loci.pop()
            except IndexError:
                break
            if is_debug:
                logging.debug(str(l)+' '+str(len_linepairs))
            if l.d_2 > d_2:
                d_2=l.d_2
                for x in linepairs:
                    x[1]=0 #distance increase means all lines are now 'stale'
            lp_index=0 #start with the 'leftmost' linepair again
            processed=False
            while lp_index<len_linepairs:
                (lp1, fresh1)=linepairs[lp_index]
                (cover1, line1) = lp1.calculateCover(l)
                if is_debug:
                    logging.debug('lp1: '+str(lp1))
                    logging.debug('fresh1: '+str(fresh1)+' cover1: '+str(cover1)+' line1: '+str(line1))
                if line1==3: #either reflex angle intersecting same locus from two different sides, or result of circle being > unit
                    (cover1,cover2)=(cover1[0],cover1[1])
                    l.cover=min(max(cover1,0.0)*(not fresh1&1)+max(cover2,0.0)*(not fresh1&2),1)
                    if l.blocksLOS and lp1.is_reflex:
                        lp1.is_world=True
                    processed=True
                    break
                if cover1 == 1: #guaranteed to be stale line by nature of the algorithm (i.e. adjacencies at same distance cannot completely occlude each other)
                    l.cover=cover1
                    processed=True
                    break
                (lp2,fresh2,cover2,line2)=(None,0,-1,0)
                if cover1>=0: #jackpot?
                    if len_linepairs>1:
                        if line1==1:
                            (lp2, fresh2)=linepairs[(lp_index-1)%len_linepairs]
                            (cover2, line2) = lp2.calculateCover(l)
                        else: #line1==2
                            (lp2, fresh2)=linepairs[(lp_index+1)%len_linepairs]
                            (cover2, line2) = lp2.calculateCover(l)
                        if is_debug:
                            logging.debug('lp2: '+str(lp2))
                            logging.debug('fresh2: '+str(fresh2)+' cover2: '+str(cover2)+' line2: '+str(line2))
                        if line2==line1:
                            logging.error(str(me))
                            logging.error('locus: '+str(l))
                            logging.error('line1, len(linepairs), len_linepairs:'+str(line1)+' '+str(len(linepairs))+' '+str(len_linepairs))
                            logging.error('lp1: '+str(lp1))
                            logging.error('lp2: '+str(lp2))
                            raise AssertionError("line1 == line2")
                        assert(line2!=3)
                    l.cover=min(max(cover1,0.0)*(not fresh1&line1)+(max(cover2,0.0)*(not fresh2&line2)),1)
                    if l.blocksLOS:
                        if cover2>=0:
                            lp=LinePair.mergePairsByLocus((lp1, line1), (lp2, line2))
                            lp.culprits.append(l)
                            linepairs[lp_index]=[lp,fresh1|fresh2]
                            if line1==1:
                                linepairs.pop((lp_index-1)%len_linepairs)
                            else:
                                linepairs.pop((lp_index+1)%len_linepairs)
                            len_linepairs-=1
                        else:
                            lp1.mergeLocus(l, line1)
                            linepairs[lp_index][1]|=line1
                    processed=True
                    break #if cover1>=0
                lp_index+=1
            if not processed and l.cover==0 and l.blocksLOS:
                linepairs.append([l.toLinePair(),3])
                len_linepairs+=1
                linepairs.sort()
            ret.append(l)
        (x,y)=(me[0],me[1])
        return [((i.id[0]+x, i.id[1]+y), i.cover, i.d_2) for i in ret]

if __name__ == '__main__':
    import unittest
    import copy
    from sys import argv

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
            assert(l==len(cover_values))
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

    suite = None
    if len(argv)>1:
        tests=argv[1:]
        suite = unittest.TestSuite(map(FOVTest,tests))
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(FOVTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
