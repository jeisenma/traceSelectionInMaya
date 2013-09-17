# Dynamic Time Warping 
# J Eisenmann
# ACCAD
# December 2012

from math import sqrt
from Vector import *

class DTW:
    def __init__( self, X, Y, subsequence=False, penalty=[0,5], maxPathLength=99999.0 ):
        self.X = list(X)
        self.Y = list(Y)
        self.subsequence = subsequence
        self.penalty = penalty
        self.maxPathLen = maxPathLength
        self.P = None
        self.minCost = None

    def DTW( self ):    # x and y are lists with members of dimension N
        """ Dynamic Time Warping distance:
            returns the cost of warping time
            series X to time series Y """
        self.C = self.ComputeCostMatrix( self.X, self.Y )
        self.ComputeAccumulatedCostMatrix()
        if self.subsequence:
            self.P, self.minCost = self.OptimalSubsequenceWarpingPath()
        else:
            self.P, self.minCost = self.OptimalWarpingPath()
        return self.P, self.minCost, self.D

    def UpdateX( self, newX ):
        """ Given a newX list (which is assumed to be 
            identical to the original X with extra entries 
            at the end, add corresponding entries to the 
            cost matrices and recalculate the best path """
        if not( len(newX) == len(self.X) and all( [ nx == x for nx,x in zip(newX, self.X) ] ) ):
            # if newX is different than self.X, re-compute with the extra parts of newX
            extraParts = newX[ len(self.X): ]
            self.UpdateCostMatrix( extraParts )
            self.X.extend(extraParts)
            self.ComputeAccumulatedCostMatrix( iterative=True )
            if self.subsequence:
                self.P, self.minCost = self.OptimalSubsequenceWarpingPath()
            else:
                self.P, self.minCost = self.OptimalWarpingPath()
        return self.P, self.minCost, self.D

    def ComputeCostMatrix( self, A, B ):
        """ Computes the two dimensional cost matrix between A and B """
        #return [[EuclideanDistance(a,b) for b in B] for a in A]
        return [[self.EuclideanDistanceSq(a,b) for b in B] for a in A]  # skip the sqrt operation until later

    def UpdateCostMatrix( self, extraXs ):
        """ Given the additions to the X list (extraXs), update 
            the cost matrix """
        for x in extraXs:
            newRow = [ self.EuclideanDistanceSq(x,y) for y in self.Y ]
            self.C.append(newRow)
        
    def ComputeAccumulatedCostMatrix( self, iterative=False ):
        """ Given the cost matrix C, calculate
            the accumulated cost matrix """
        start = 0
        if not iterative:   # if first time, make a matrix of zeros
            self.D = [[0 for x in range(len(self.C[0]))] for y in range(len(self.C))]
        else:               # else add rows of zeros until D has the same dimensions as C
            start = len(self.D)-1
            for row in range( len(self.C) - len(self.D) ):
                self.D.append( [ 0 for x in range(len(self.C[0])) ] )
        for n in range( start, len(self.C) ):
            for m in range( len(self.C[0]) ):
                if n == 0:
                    if(self.subsequence):
                        self.D[n][m] = 0+self.C[n][m]
                    else:
                        self.D[n][m] = sum( self.C[n][:m] )
                if m == 0:
    ##                print "col 0, row %d, sum=%f"%(n,sum( [row[m] for row in C[:n]] ))
    ##                print [row[m] for row in C[:n]]
                    self.D[n][m] = sum( [row[m]+self.penalty[1] for row in self.C[:n]] )
                else:
                    self.D[n][m] = self.C[n][m] + min( self.D[n-1][m-1], self.D[n-1][m]+self.penalty[0], self.D[n][m-1]+self.penalty[1])
                    if n == len(self.C)-1:  # last row
                        self.D[n][m] += self.penalty[1]*len(self.C[0])-m    # bias the cost of the last row, so that the algorithm prefers to start near the bottom right corner
        
    def OptimalWarpingPath( self, colStart=None ):
        """ Given the cost matrix D, find the
            lowest cost warping path from
            D[0][0] to D[rows-1][cols-1] """
        rows = len(self.D)
        cols = len(self.D[0])
        n = rows-1
        m = cols-1
        if colStart:
            m=colStart
        path = [(n,m)]
        while n > 0 or m > 0:
            if n == 0 :
                path.insert(0,(0,m-1))
                m -= 1
            elif m == 0 :
                path.insert(0,(n-1,0))
                n -= 1
            else:
                minStep = min( self.D[n-1][m-1], self.D[n-1][m], self.D[n][m-1] )
                if self.D[n-1][m-1] == minStep:
                    path.insert(0,(n-1,m-1))
                    n -= 1
                    m -= 1
                elif self.D[n-1][m] == minStep:
                    path.insert(0,(n-1,m))
                    n -= 1
                else:   # self.D[n][m-1] == min:
                    path.insert(0,(n,m-1))
                    m -= 1
        return path, self.CostOfPath( path, self.D )

    def OptimalSubsequenceWarpingPath( self ):
        """ Given the accumulated cost matrix D, find the
            lowest cost subsequence warping path from
            D[0][a*] to D[rows-1][b*] (Note: Y is assumed
            to be longer than X) """
        subseqCandidates = []
        subseqCosts = []

        lastRow = list(self.D[-1])
        bStar = lastRow.index( min(lastRow) )
        while lastRow[bStar] < self.maxPathLen or len(subseqCosts) == 0:
            # find aStar with minimum distance for subsequences ending at bStar
            P, cost = self.OptimalWarpingPath( bStar )
            subseqCandidates.append( P )
            subseqCosts.append( cost )
            lastRow[bStar] = float("inf")
            bStar = lastRow.index( min(lastRow) ) 
        minCost = min(subseqCosts)
        return subseqCandidates[ subseqCosts.index( minCost ) ], minCost
       
    def CostOfPath( self, P, D ):
        """ Given a path P and a cost matrix D,
            return the path cost """
        cost = 0
        for tup in P:
            cost += D[tup[0]][tup[1]]
        return cost

    def EuclideanDistanceSq( self, a, b ):
        """ Computes the squared Euclidean distance
            between two points in N-dimensions """
        if not (type(a) == list or type(a) == Vector):
            a = [a]
        if not (type(b) == list or type(a) == Vector):
            b = [b]
        assert len(a) == len(b)
        sqDist = 0
        for x,y in zip(a,b):
            sqDist += (x-y)**2
        return sqDist
        
    def EuclideanDistance( self, a, b ):
        """ Computes the Euclidean distance
            between two points in N-dimensions """
        return sqrt( self.EuclideanDistanceSq(a,b) )

    def DrawCostMatrixAndPath( self, fname ):
        """ spits out a p5py file that will draw the matrix and path when run """
        f = open(fname, 'w')
        w = len(self.D[0])
        h = len(self.D)
        f.write("img=None\n\ndef setup():\n\tglobal img\n")
        f.write("\tsize(%d,%d)\n"%( 5*w,5*h ))
        f.write("\timg = createImage( %d, %d, RGB )\n"%(w,h))
        f.write("\timg.loadPixels()\n")
        mx = max([ max([ x for x in row]) for row in self.D])
        pixels = []
        i=0
        for r,row in enumerate(self.D):
            for c,cell in enumerate(row):
                pixels.append( int( 255.0*cell/mx ) )
                if( (r,c) in self.P ):
                    pixels[-1] = 255
                i += 1
        for i,p in enumerate(pixels):
            f.write("\timg.pixels[%d] = color(%d)\n"%(i,p))
        f.write("\timg.updatePixels()\n\ndef draw():\n\tglobal img\n\timage(img,0,0,%d,%d)\n"%(5*w,5*h))
        f.close()

##### Module testing code:	
##s1 = [0,0,0,0,0,1,2,3,4,3,2,1,0,0,1,2,3,2,1]
##sub = [4,3,2,1]
##print s1
##print sub
##print ""
##dtw = DTW( sub, s1, True )
##dtw.DTW()
##
##
##print "before"
##for c in dtw.D:
## print c
##
##P,C,M = dtw.UpdateX( [0,1] )
##
##print "after"
##for c in dtw.D:
## print c

# print P
# print C
# for m in M:
#     print m


##C = ComputeCostMatrix( sub, s1 )
##D = ComputeAccumulatedCostMatrix( C, True )
##for c in C:
##    print c
##print ""
##for d in D:
##    print d
##path,cost = SubsequenceDTW( sub, s1, threshold = 10)
##print "final answer"
##print path
##print cost

##seq1 = [sin(x/5.0) for x in range(int(2*pi))]
##seq2 = [cos(x/5.0+pi/2) for x in range(int(3*pi))]
##
##print seq1
##print seq2
##print ""
##DTW(seq1,seq2)
