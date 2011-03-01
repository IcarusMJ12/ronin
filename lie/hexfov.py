#!/usr/bin/env python
from numpy import array as ar
from math import sqrt
import fractions

class HexFOV(object):
    def __init__(self, grid):
        self.grid=grid
        r=sqrt(3.0/4)
        rr=1.0/(4*r)
        #rotation matrix in hex, T*R*Tinv, where T transforms coordinates to hex, R rotates, Tinv inverts coordinate transform
        self.TILE_SAMPLE_COUNT=16
        self.R90=ar([[-r+rr,r+rr,0],[-r-rr,r-rr,0],[0,0,1]])
        self._cache={}
        self.cache_metrics=[0,0] #hits, misses
        self.circles_considered={}
    
    #algorithm mostly courtesy of Bruce Bell
    def _unitCircleMetric(self, a,b):
        """compute a scaled metric value for circle of a given diameter
        (if a==b, return value is negative iff the point is inside the circle;
        note that the formula could be simplified for this case...)
        aruments:
        a, b are tuples (x,y) representing nonorthogonal hex coordinates
        d is the diameter of the circle
        returns: 4*(metric value) for unit circle (so you can work /w integers)
        """
        (ax,ay)= a
        (bx,by)= b
        return 4*(ax*bx + ay*by) - 2*(ax*by + bx*ay) - 1

    def FOV(self, tile, radius):
        (x1,y1)=(tile.location.x,tile.location.y)
        for x2 in xrange(len(self.grid)):
            for y2 in xrange(len(self.grid[x2])):
                d=pow(x2-x1,2)+pow(y2-y1,2)-(y2-y1)*(x2-x1)
                self.grid[x2][y2].d2=d
                if d<=pow(radius,2)+radius:
                    self.grid[x2][y2].cover=self._LOS((x1,y1),(x2,y2))
                    print (x1,y1), (x2,y2), self.grid[x2][y2].cover, d
                    continue
                self.grid[x2][y2].cover=(1,1)

    #algorithm mostly courtesy of Bruce Bell
    def _LOS(self, src, dst):
        """calculates the cover tuplet from src to dst grid indices"""
        if src == dst:
            return (0,0)
        (x1,y1)=src
        (x2,y2)=dst
        #determine bounding parallelogram for candidate blocking tiles
        (x_min,x_max)=(min(x1,x2),max(x1,x2)+1)
        (x_min,x_max)=(max(x_min-1,0),min(len(self.grid),x_max+1))
        (y_min,y_max)=(min(y1,y2),max(y1,y2)+1)
        (y_min,y_max)=(max(y_min-1,0),min(len(self.grid[x_max]),y_max+1))
        tiles=map(lambda i: (i.location.x, i.location.y), filter(lambda i: i.blocksLOS() and not (i.location.x==x1 and i.location.y==y1) and not (i.location.x==x2 and i.location.y==y2), [item for sublist in self.grid[x_min:x_max] for item in sublist[y_min:y_max]]))
        if len(tiles) == 0:
            return (0,0)
        #determine if there are any tiles that are literally between src and dst
        interval=abs(fractions.gcd(x2-x1,y2-y1))
        if interval>1:
            x_step=(x2-x1)/interval
            y_step=(y2-y1)/interval
            x_y=[(x1+x_step*(i+1), y1+y_step*(i+1)) for i in xrange(interval-1)]
            full_cover_tiles=filter(lambda i: i in x_y, tiles)
            if len(full_cover_tiles):
                return (1,1)
        #otherwise do things the hard way, by sampling
        n=self.R90.dot([x2-x1,y2-y1,1])
        n_magnitude=sqrt(pow(n[0],2)+pow(n[1],2)-n[0]*n[1])
        n=(n[0]/(n_magnitude*2),n[1]/(n_magnitude*2))
        tile_sample_intervals=map(lambda i: float(i)/(self.TILE_SAMPLE_COUNT-1)*2, xrange(0.0,self.TILE_SAMPLE_COUNT))
        src_samples=map(lambda i: (x1+n[0]-n[0]*i, y1+n[1]-n[1]*i), tile_sample_intervals)
        dst_samples=map(lambda i: (x2+n[0]-n[0]*i, y2+n[1]-n[1]*i), tile_sample_intervals)
        src_accumulator= [0]*self.TILE_SAMPLE_COUNT
        dst_accumulator= [0]*self.TILE_SAMPLE_COUNT
        src_index= 0
        for s in src_samples:
            dst_index= 0
            for d in dst_samples:
                blocked = self._blocksLine(s,d, tiles)
                if not blocked:
                    src_accumulator[src_index]+= 1
                    dst_accumulator[dst_index]+= 1
                dst_index+= 1
            src_index+= 1
        try:
            self.circles_considered[len(tiles)]+=1
        except:
            self.circles_considered[len(tiles)]=1
        return (1.0-float(max(src_accumulator))/self.TILE_SAMPLE_COUNT, 1.0-float(max(dst_accumulator))/self.TILE_SAMPLE_COUNT)

    def _blocksLine(self, src, dst, circles):
        """determines if a unit circle blocks a segment between two lines
        arguments:
        src, dst are tuples (a,b) representing nonorthogonal hex coordinates
        circles is a list of tuples, each the center of a blocking unit circle
        returns: boolean, true iff any unit circle blocks segment from src to dst
        """
        (x1,y1)= src
        (x2,y2)= dst

        for (x,y) in circles:
        # compute offset from circle
            src_diff= (x1-x,y1-y)
            dst_diff= (x2-x,y2-y)
            ret = None
            try:
                ret = self._cache[(src_diff,dst_diff)]
                self.cache_metrics[0]+=1
                if ret > -1:
                    return ret
                else:
                    continue
            except:
                pass
            m_src = self._unitCircleMetric(src_diff,src_diff)
            if m_src <= 0:  # src is inside circle; ignore it
                self._cache[(src_diff,dst_diff)]=-1
                self.cache_metrics[1]+=1
                continue
            m_dst = self._unitCircleMetric(dst_diff,dst_diff)
            if m_dst <= 0:  # dst is inside circle; ignore it
                self._cache[(src_diff,dst_diff)]=-1
                self.cache_metrics[1]+=1
                continue
            m_cross = self._unitCircleMetric(src_diff,dst_diff)
            if m_cross > 0:  # points are on the same side; segment can't intersect
                self._cache[(src_diff,dst_diff)]=-1
                self.cache_metrics[1]+=1
                continue
            discriminant = m_cross*m_cross - m_src*m_dst
            if discriminant > 0:  # segment intersects circle
                self._cache[(src_diff,dst_diff)]=1
                self.cache_metrics[1]+=1
                return True  # the line is blocked
        self._cache[(src_diff,dst_diff)]=0
        self.cache_metrics[1]+=1
        return False    # no circles block the segment
