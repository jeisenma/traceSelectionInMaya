## A class for working with trajectories (basically animation paths)
## J Eisenmann
## ACCAD
## 2012-13

from IterativeDynamicTimeWarping import *
from Vector import *
from Plane import *
from Cylinder import *

import maya.cmds as mc

class Trajectory:
    """ A class to hold spatio-temporal path information """
    def __init__( self, name="" ):
        self.name = name
        self.points = {}
        self.searchList = {}        # the dict of trajectories to check for a match (indexed by joint name)
        self.dtws = []
        self.closest = -1
        self.closestJoint = None    # the closest motion path in the searchList (measured by DTW distance)
        self.normal = None        # the selected timespan
        self.planePt = None
        
    def Clear( self ):
        """ removes all points from the trajectory """
        self.points.clear()
        del(self.dtws[:])
        self.closest = -1
        self.closestJoint = None    
        self.timespan = None
        self.normal = None
        self.planePt = None

    def AddPoint( self, p, t=None ):
        if not type(p) == Vector:
            try:
                p = Vector(p)
            except:
                print "Error: input point p must be a Vector"
                return
        if t:
            self.points[t] = p
        else:
            self.points[ len(self.points.keys()) ] = p  # if no time is provided, just use and index
        self.UpdateDTWs()

    def SetSearchList( self, trajectories ):
        """ Sets the dict of trajectories to check for a match """
        self.searchList = trajectories

    def SetUpDTWs( self ):
        """ Initializes the DTWs """
        del self.dtws[:]
        do_subsequence = True
        selfData  = [ [self.points[t].x, self.points[t].y, self.points[t].z] for t in sorted(self.points.keys()) ]
        for joint in sorted(self.searchList.keys()):
            jointMotionPath = self.searchList[joint]
            currentCam = mc.lookThru(q=True)
            camPos = Vector(mc.xform(currentCam,q=True,t=True))
            otherData = [ Plane(self.normal,self.planePt).intersectWithRay( camPos, jointMotionPath.points[t] ).asList() for t in sorted(jointMotionPath.points.keys()) ]
            self.dtws.append( DTW( selfData, otherData, do_subsequence ) )

    def UpdateDTWs( self ):
        """ Augments the cost matrices of the DTWs and re-solves for the optimal paths """
        minCost = None
	minP = None
	minC = float("inf")
	for i, (joint, dtw) in enumerate( zip( sorted(self.searchList.keys()), self.dtws ) ):
            if dtw.P and dtw.minCost and dtw.D:     # if not first time, get an updated optimal cost and path
                selfData = [ [self.points[t].x, self.points[t].y, self.points[t].z] for t in sorted(self.points.keys()) ]
                P,C,M = dtw.UpdateX( selfData )
            else:                                   # if first time, fresh start
                P,C,M = dtw.DTW()
            if C < minC:
                minCost = M
                minP = P
                minC = C
                self.closestJoint = joint
                self.closest = i
                start = 0
                for s,step in enumerate(minP):
                    if step[0] > 0:
                        start = sorted(self.searchList[joint].points.keys())[s-1]
                        break
                stop  = sorted(self.searchList[joint].points.keys())[minP[-1][1]]
                if stop-start > 1:
                    self.timespan = [ start, stop ]
                    
            
    def Center( self ):
        """ Returns the center of this trajectory """
        psum = Vector()
        for p in self.points.values():
            psum = psum + p
        return psum/len(self.points.values())

    def ClosestTimeTo( self, point, plane=None ):
        """ Returns the closest point in this trajectory to the given point in 3d space (or 2d if plane is defined) """
        if not type(point) == Vector:
            point = Vector(point)
        if plane:
            point = point.projectToPlane(plane.normal,planePt=plane.point)
        minDist = float("inf")
        ft = None
        camPos = Vector( mc.xform(mc.lookThru(q=True), q=True, t=True) )
        for i,t in enumerate(sorted(self.points.keys())):
            p = self.points[t]
            if plane:
                p = p.projectToPlane(plane.normal,planePt=plane.point)
                dist = (point-p).mag()
            else:
                ray = (p-camPos).norm()     # build a ray from the camera to the path point in question
                dist = ray.cross(point-p).mag()
            if minDist > dist:
                minDist = dist
                ft = t
        return ft   # return the key of the closest point in the points dictionary

    def ClosestPointTo( self, point, plane=None ):
        """ Returns the key of the closest point in this trajectory to the given point in 3d space (or 2d if plane is defined) """
        return self.points[self.ClosestTimeTo(point,plane=plane)]

    def DistanceTo( self, point, plane=None ):
        """ Returns the distance between the closest point in this trajectory and a point in 3d space (or 2d if plane is defined) """
        if plane:
            point = point.projectToPlane(plane.normal,planePt=plane.point)
        return ( point - self.ClosestPointTo(point, plane=plane) ).mag()         
    
    def __repr__( self ):
        """ So we can print this object """
        string = ""
        for t in sorted( self.points.keys() ):
            string += "%.2f:\t%s\n"%(t, self.points[t])
        return string
