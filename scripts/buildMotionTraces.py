## Build Motion Traces
## J Eisenmann
## ACCAD, The Ohio State University
## 2012-13

import maya.cmds as mc
import curveUtil as cu
from Vector import *

class CurveMotionTrace:
    """ Given a moving object, this class will construct a
        NURBS curve in 3D space that traces the motion over
        time. Optionally, a tube can be extruded along the
        resulting curve (in sync with the motion). """
    
    def __init__(self,
                 obj,
                 keys=None,
                 duration=  [
                             mc.playbackOptions(q=True,minTime=True),
                             mc.playbackOptions(q=True,maxTime=True)
                            ],
                 smooth=0.25,
                 tstep=1.0,
                 tube=False,
                 radius=0.5,
                 multVel=False,
                 invertVel=False ):
        self.object = obj
        self.timeSpan = duration
        self.smooth = smooth
        self.timestep = tstep
        self.tube = tube
        self.radius = radius
        self.multVel = multVel
        self.invertVel = invertVel
        self.points = keys
        self.traceBits = []
        
    def construct(self,name=None):
        """ builds the trace """
        minVel = 99999.0
        maxVel = 0.0
        pPos = None
        if not self.points:     # if points is not yet defined, iterate through keys and gather the points
            self.points = []
            frames = [x*self.timestep+self.timeSpan[0] for x in range(0, int((self.timeSpan[1]-self.timeSpan[0])/self.timestep)+1)]
            frames.append(self.timeSpan[1])
            for t in frames:
                mc.currentTime(t)
                pos = mc.xform( self.object, q=True, ws=True, translation=True )
                if not pPos == None:
                    vel = Vector(pos) - Vector(pPos)
                    if( vel.mag() > maxVel ):
                        maxVel = vel.mag()
                    if( vel.mag() < minVel ):
                        minVel = vel.mag()
                if( len(self.points) == 0 or
                    (Vector(pos) - Vector(self.points[-1])).mag() > 0.001 ):
                    self.points.append(pos)
                pPos = pos
        self.origCurve = mc.curve(d=1, ep=self.points, n="nurbsCurveTrace")
        self.origCurve = mc.rebuildCurve(self.origCurve,
                                         constructionHistory=0,
                                         replaceOriginal=1,
                                         rebuildType=0,
                                         endKnots=1,
                                         keepRange=1,
                                         keepControlPoints=0,
                                         keepEndPoints=1,
                                         keepTangents=0,
                                         spans=len(self.points)*self.timestep*self.smooth,
                                         degree=3,
                                         tolerance=0.01)[0]
        if name:
            self.origCurve = mc.rename(self.origCurve,name)
            
        if( self.tube == True ):
            self.extrusion = self.extrude()
            frames = [x*self.timestep+self.timeSpan[0] for x in range(0, int((self.timeSpan[1]-self.timeSpan[0])/self.timestep)+1)]
            frames.append(self.timeSpan[1])
            for t in frames:
                mc.currentTime(t)
                end = cu.curveArcLen( self.origCurve )
                mc.select( self.object )
                pt = mc.xform( q=True, ws=True, t=True )
                now = cu.findArcLenAtParam( self.origCurve, cu.findParamAtPoint( self.origCurve, pt ) )
                # find subCurve2 of the extrusion
                shape = mc.listRelatives(self.curve2, fullPath=True, shapes=True)[0]
                for sub in mc.listConnections(shape):
                    if(sub.startswith("subCurve")):
                        mc.setKeyframe( "%s.maxValue"%sub, t=t, v=max(0.0001,now/end) )  # key the visibility
                
            prev = None
            frames = [x*self.timestep+self.timeSpan[0] for x in range(0, int((self.timeSpan[1]-self.timeSpan[0])/self.timestep)+1)]
            frames.append(self.timeSpan[1])
            for prevT in frames:
                mc.currentTime(prevT)
                mc.select( self.object )
                pt = mc.xform( q=True, ws=True, t=True )
                
                scalePivot = Vector()
                for i in range(0,8):
                    mc.select( "%s.cv[%d][%d]"%( self.extrusion, i, int(t/self.timestep) ) )
                    scalePivot.add( Vector( mc.xform(q=True, ws=True, t=True) ) )
                scalePivot.mult(1.0/8.0)
                
                mc.select( "%s.cv[0:7][%d]"%( self.extrusion,int(t/self.timestep) ) )
                if( self.multVel ):
                    sz = 1.0
                    if( prev == None ):
                        sz = 0.0
                    else:
                        vel = Vector(pt) - Vector(prev)
                        if( self.invertVel ):
                            sz = self.taper(prevT, self.timeSpan[0], self.timeSpan[1], 0.2, 0.8) #remap(vel.mag(), minVel, maxVel, 1, 0)
                        else:
                            sz = 1-self.taper(prevT, self.timeSpan[0], self.timeSpan[1], 0.2, 0.8) #remap(vel.mag(), minVel, maxVel, 0, 1)
                    mc.scale( sz, sz, sz, centerPivot=True, relative=True, p=scalePivot )
                prev = pt
                
            groupName = mc.group(self.traceBits,n=self.object+"TubeTraceGroup")
            mc.setKeyframe( groupName+".visibility", t=self.timeSpan[0]-1, v=0.0 )
            mc.setKeyframe( groupName+".visibility", t=self.timeSpan[0], v=1.0 )

            # center the pivot on the newly created trace
            mc.select(groupName)
            mc.xform(cp=True)
            
            return groupName

        else:
            # center the pivot on the newly created trace
            mc.select(self.origCurve)
            mc.xform(cp=True)
            
            return self.origCurve

    def extrude(self,caps=True):
        """ extrudes a tube along the NURBS curve """
        self.curve2 = mc.duplicate(self.origCurve, name=self.origCurve+"_copy")[0]
        # select the first CV of the path (curve)
        mc.select("%s.cv[0]"%self.curve2,replace=True)
        # figure out where to put the circle and which way to point it
        circleCenter = mc.xform(q=True,ws=True,t=True)
        circleNormal = mc.pointOnCurve(self.curve2, parameter=0, tangent=True)
        # create a circle to use for extrusion
        circle = mc.circle(radius=self.radius, center=circleCenter, normal=circleNormal)[0]
        # extrude!
        extrusion = mc.extrude( circle, self.curve2, n="nurbsTubeTrace", extrudeType=2, range=True )[0]
        self.traceBits = [extrusion, self.curve2, self.origCurve, circle]
        if caps:
            # select the first isoparm
            mc.select(extrusion+".v[%f]"%cu.findParamAtArcPercent( self.origCurve, 0.0))
            # create planar surface
            begCap = mc.planarSrf(n="cap1")[0]
            # select the last isoparm
            mc.select(extrusion+".v[%f]"%cu.findParamAtArcPercent( self.origCurve, 1.0))
            # create planar surface
            endCap = mc.planarSrf(n="cap2")[0]
            mc.setKeyframe( endCap+".visibility", t=self.timeSpan[1]-1, v=0.0 )
            mc.setKeyframe( endCap+".visibility", t=self.timeSpan[1], v=1.0 )
            # add the caps to the traceBits list
            self.traceBits.extend([begCap,endCap])
        return extrusion
    
    def taper(self, frame, start, end, taperA, taperB):
        """ Provides a curve up, curve down shape from 0 to 1 based on
            start/end frames and taper percentages """
        t = max((frame-start)/(end-start),0);
        if( t < taperA ):
            return 1-(t/taperA-1)**2
        elif( t < taperB ):
            return 1.0
        else:
            return 1-(t/(1-taperB)-1)**2

# utility function
def remap( v, fromLo, fromHi, toLo, toHi):
    """ remaps a value (v) from one range to another """
    return float(v-fromLo)/(fromHi-fromLo)*(toHi-toLo)+toLo
