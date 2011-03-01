#!/usr/bin/env python
from numpy import array as ar
from math import sqrt

SQRT3_4=sqrt(3.0/4)


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

    """A line pair is defined by two pairs of points and whether these lines form a reflex angle."""
    def __init__(self, left, right, reflex=False):
        self.left=left  #left line, as a pair of points
        self.right=right #right line, as a pair of points
        self.is_reflex=reflex #when considered from the intersection, whether the line pair makes a reflex angle (>pi)
        self.is_world=False #whether the linepair angle is 2*pi, i.e. the world
        self.culprits=[] #debug info
        self.id=LinePair.id
        LinePair.id+=1
        #print "Created linepair ",self.id
    
    def __repr__(self):
        if self.is_world:
            return "LinePair<world>"
        else:
            r="LinePair<"+str(self.id)+" l:"+str(self.left[0])+","+str(self.left[1])+" r:"+str(self.right[0])+","+str(self.right[1])
            if self.is_reflex:
                r+=" (ref)"
            r+=">"
            for c in self.culprits:
                r+="\n\t"+c.__repr__()
            return r

    def __cmp__(self, other):
        """Sort by clockwise direction."""
        return _clockwiseCompare(self.right[0], other.right[0])
    
    def mergeLocus(self, locus, line):
        """Updates the LinePair to contain the LOS-blocking locus provided."""
        self.culprits.append(locus)
        #print "Merging locus",locus,line,"into linepair",self.id
        if line==3:
            self.is_world=True
            return self
        if line==1:
            if LinePair._cross(self.right[0],self.left[0],locus.n) < 0:
                self.is_reflex=True
            self.left=(locus.n, locus.coord+locus.n)
        else:
            if LinePair._cross(self.left[0],self.right[0],-locus.n) > 0:
                self.is_reflex=True
            self.right=(-locus.n, locus.coord-locus.n)
        return self
    
    @classmethod
    def mergePairsByLocus(self, lp1_tuplet, lp2_tuplet):
        """Merges two LinePairs by a LOS-blocking locus that they share."""
        (lp1,lp1_line)=lp1_tuplet
        (lp2,lp2_line)=lp2_tuplet
        #print "Merging linepairs ",lp1.id,lp1_line,"and",lp2.id,lp2_line
        if lp1==lp2:
            ret=LinePair(None,None)
            ret.is_world=True
            return ret
        right=None
        left=None
        reflex=False
        assert(lp1_line!=lp2_line)
        if lp1_line==1:
            right=lp1.right
            left=lp2.left
            if LinePair._cross(lp1.right[0],lp1.left[0],lp2.left[0]) < 0:
                reflex=True
        else:
            left=lp1.left
            right=lp2.right
            if LinePair._cross(lp2.right[0],lp2.left[0],lp1.left[0]) < 0:
                reflex=True
        lp=LinePair(left,right,reflex)
        lp.culprits=lp1.culprits
        lp.culprits.extend(lp2.culprits)

    @classmethod
    def _unitCircleMetric(self,a,b):
        """Dot product minus r^2."""
        return a[0]*b[0]+a[1]*b[1]-0.251 #my unit circle is a little bigger than average (is what she said)

    @classmethod
    def _intersectsCircle(self,line,circle):
        """Returns True if a given line intersects a circle, False otherwise."""
        (x,y)=circle
        p1=(line[0][0]-x,line[0][1]-y)
        p2=(line[1][0]-x,line[1][1]-y)
        m1=LinePair._unitCircleMetric(p1,p1)
        if m1 <= 0: #p1 is inside circle, hence line intersects
            return True
        m2=LinePair._unitCircleMetric(p2,p2)
        if m2 <= 0: #p2 is inside circle, hence line intersects
            return True
        m12=LinePair._unitCircleMetric(p1,p2)
        #if m12 > 0: #points are on the same side of circle, so cannot intersect
        #   return False
        #compute the discriminant. >0 -> roots are real -> intersects
        #not testing for equality (tangent line) as our "unit" circles are already larger than most
        discriminant=m12*m12 - m1*m2
        if discriminant > 0: 
            #print sqrt(discriminant)/(m12*m12)
            return True
        return False

    def calculateCover(self, l):
        """Returns a tuple in the form (cover_amount: 0.0-1.0, side: 1 if left line, 2 if right line, 3 if both, 0 if doesn't matter)"""
        #TODO: compute actual cover
        if(self.is_world):
            return (1.0,0)
        if not self.is_reflex and LinePair._cross(self.left[0],self.right[0], l.coord)<0:
            return (0.0,0)
        left=LinePair._intersectsCircle(self.left, l.coord)
        right=LinePair._intersectsCircle(self.right, l.coord)
        if left:
            if right:
                if self.is_reflex: #returning tuple for cover, in case one of them is fresh and will be disregarded
                    return((0.25,0.25),3)
                return (1.0,0)
            return (0.25,1)
        if right:
            return (0.25,2)
        p=self._getPosition(l.coord)
        if not p:
            return (1.0,0)
        return (0.0,0)
    
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
        return lp

class FOV(object):
    """Field of View calculator."""
    def calculateHexFOV(self, me, world, linepairs=None):
        """Calculate Field of View from triples of the form (x,y,blocksLOS) where x and y are in hex coordinates."""
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
        while loci[-1].d_2==0:
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
                assert(wc==1)
                assert(len_linepairs==1)
            try:
                l=loci.pop()
            except IndexError:
                break
            #print l, len_linepairs
            if l.d_2 > d_2:
                d_2=l.d_2
                for x in linepairs:
                    x[1]=0 #distance increase means all lines are now 'stale'
            lp_index=0 #start with the 'leftmost' linepair again
            processed=False
            while lp_index<len_linepairs:
                (lp1, fresh1)=linepairs[lp_index]
                (cover1, line1) = lp1.calculateCover(l)
                #print 'lp1:',lp1
                #print 'fresh1:',fresh1,'cover1:',cover1,'line1:',line1
                if line1==3: #either reflex angle intersecting same locus from two different sides, or result of circle being > unit
                    (cover1,cover2)=(cover1[0],cover1[1])
                    l.cover=cover1*(not fresh1&1)+cover2*(not fresh1&2)
                    if l.blocksLOS:
                        lp1.is_world=True
                    processed=True
                    break
                if cover1 == 1: #guaranteed to be stale line by nature of the algorithm, so no point checking
                    l.cover=cover1
                    processed=True
                    break
                if cover1>0: #jackpot?
                    if line1==1: #as we're going clockwise, only possible cover; also left line cannot be fresh (!)
                        l.cover=cover1
                        if l.blocksLOS:
                            lp1.mergeLocus(l,line1)
                            linepairs[lp_index][1]=line1
                    else: #line1==2
                        (lp2,fresh2,cover2,line2)=(None,0,0,0)
                        if len_linepairs>1:
                            (lp2, fresh2)=linepairs[(lp_index+1)%len_linepairs]
                            (cover2, line2) = lp2.calculateCover(l)
                        #print 'lp2:',lp2
                        #print 'fresh2:',fresh2,'cover2:',cover2,'line2:',line2
                        assert(line2!=line1)
                        l.cover=cover1*(not fresh1&2)+cover2*(not fresh2&1)
                        if l.blocksLOS:
                            if cover2:
                                lp=LinePair.mergePairsByLocus((lp1, line1), (lp2, line2))
                                lp.culprits.append(l)
                                linepairs[lp_index]=[lp,fresh1|fresh2]
                                linepairs.pop((lp_index+1)%len_linepairs)
                                len_linepairs-=1
                            else:
                                lp1.mergeLocus(l, line1)
                                linepairs[lp_index][1]=line1
                    processed=True
                    break #if cover1>0
                lp_index+=1
            if not processed and l.cover==0 and l.blocksLOS:
                linepairs.append([l.toLinePair(),3])
                len_linepairs+=1
                linepairs.sort(reverse=True)
            ret.append(l)
        (x,y)=(me[0],me[1])
        return [((i.id[0]+x, i.id[1]+y), i.cover, i.d_2) for i in ret]

if __name__ == '__main__':
    f=FOV()
    world=[]
    for i in xrange(5):
        for j in xrange(5):
            if i==1 and j==2:
                world.append([i,j,True])
            elif i==2 and j==3:
                world.append([i,j,True])
            else:
                world.append([i,j,False])
    result=f.calculateHexFOV([1,1,0],world)
    ans=ar([[0]*5]*5)
    for r in result:
        ans[r[0][0],r[0][1]]=r[1]
    print ans
