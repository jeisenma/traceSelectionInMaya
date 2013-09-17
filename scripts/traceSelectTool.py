## Trace Selection Tool
## J Eisenmann
## ACCAD, The Ohio State University
## 2012-13

import maya.cmds as mc          
import maya.mel as mm
from Plane import *                 # for interaction plane calculations
from Trajectory import *            # for building motion trajectory curves
import buildMotionTraces as bmt
import sys, time

debug = 0
        
class TraceSelection:
    def __init__( self, xformRoots, traceableObjs ):
        self.xformRoots = xformRoots        # all rigs
        self.traceableObjs = traceableObjs  # the list of joints to pay attention to (ignore the rest)
        
        self.substeps = 1             # precision settings
        self.dragDensity = 0.2

        self.selectedMotions = {}     # a dictionary to hold the selected motions for each root
        self.motionPathsVisible = {}  # a dictionary to remember whether (or not) the motion paths for a root were visible when the interaction started

        self.forceReload = False      # force the re-definition of the tool?
        
        # for keeping track of time when mousePressed (when selection started)
        self.startTime = 0

        # make an empty trajectory dictionary
        self.trace = {}
        self.nearestRoot = None
        self.nearestPath = None
        self.interactionPlane = None

        # measure the fit-one truck distance for the camera
        mc.select( xformRoots[0] )
        mc.viewFit()
        self.viewFitDistance = self.CameraToPopDist()
        # zoom back out to view all
        mc.select(clear=True)
        mc.viewFit()


    def TraceGesturePress( self ):
        """ Procedure called on press """
        if debug>0: print("begin PRESS")
        # Clean up: if there are any locators or groups in the scene, delete them
        if( len(mc.ls("locator*")) > 0 ):
            mc.delete(mc.ls("locator*"))
        if( len(mc.ls("*Grp")) > 0 ):
            mc.delete(mc.ls("*Grp"))

        # find the position of the mouse click
        pressPosition = Vector( mc.draggerContext( 'TraceGesture', query=True, anchorPoint=True) )

        camPos = self.CameraPosition()
        viewAxis = self.CameraViewAxis()
        closestObj2Cam = self.FindNearestObjectToCamera()
        self.interactionPlane = Plane(viewAxis,closestObj2Cam)

        pressPosition = self.FindRayPlaneIntersect( camPos, pressPosition, self.interactionPlane )
        if debug > 0:
            mc.group(n="traceGrp",empty=True)
            loc = mc.spaceLocator(p=pressPosition)
            mc.parent(loc,"traceGrp")

        for root in self.xformRoots:
            # remember whether (or not) the motion paths for a root were visible when the interaction started
            self.motionPathsVisible[root] = mc.getAttr("%s_MotionTraces.visibility"%root)
            # set up all the traces
            self.trace[root].Clear()
            # set the trace normal to the viewing normal of the camera
            self.trace[root].normal = self.interactionPlane.normal #Vector( mc.xform(mc.lookThru(q=True), q=True, m=True)[8:11] )
            self.trace[root].planePt = self.interactionPlane.point #closestObj2Cam

        self.nearestRoot, rootDist = self.FindNearestRoot( pressPosition, self.interactionPlane )
        mc.setAttr("%s_MotionTraces.visibility"%self.nearestRoot, 1)   # vis the new display layer

        # make a group to hold the trace locators
        if debug > 0:
            mc.group(name="trace%sGrp"%self.nearestRoot,empty=True)
            loc = mc.spaceLocator(p=pressPosition)
            mc.parent(loc,"trace%sGrp"%self.nearestRoot)
        # reset the trace
        self.trace[self.nearestRoot].Clear()
        # start the timer
        self.startTime = time.time()
        # set the trace normal to the viewing normal of the camera
        self.trace[self.nearestRoot].normal = Vector( mc.xform(mc.lookThru(q=True), q=True, m=True)[8:11] )
        self.trace[self.nearestRoot].planePt = closestObj2Cam
                
        # add the initial click position to the trace
        self.trace[self.nearestRoot].AddPoint( pressPosition )
        
        self.nearestPath, pathDist = self.FindNearestMotionPath( pressPosition, self.nearestRoot )
        if not mc.draggerContext( 'TraceGesture', query=True, modifier=True) == "ctrl":
            self.trace[self.nearestRoot].SetUpDTWs()
            mc.refresh(currentView=True,force=True)
        if debug>0: print("end PRESS")

    def TraceGestureDrag( self ):
        """ Procedure called on drag """
        # find the current position of the mouse drag
        if debug>0: print("begin DRAG")

        if not mc.draggerContext( 'TraceGesture', query=True, modifier=True) == 'shift':
            if self.nearestRoot in self.selectedMotions.keys():
                for sm in self.selectedMotions[ self.nearestRoot ]:
                    if mc.objExists(sm):
                        mc.delete( sm )
                del self.selectedMotions[ self.nearestRoot ]

        currentCam = mc.lookThru(q=True)
        camPos = Vector(mc.xform(currentCam,q=True,t=True))
        dragPosition = Vector( mc.draggerContext( 'TraceGesture', query=True, dragPoint=True) )
        dragPosition = self.FindRayPlaneIntersect( camPos, dragPosition, Plane(self.trace[self.nearestRoot].normal,self.trace[self.nearestRoot].planePt) )
        # find the last recorded drag position
        lastDragPosition = self.trace[self.nearestRoot].points[ sorted(self.trace[self.nearestRoot].points.keys())[-1] ]
        # find the drag distance
        dragDist = (dragPosition-lastDragPosition).mag()
        # if far enough away from last drag position, add a new trace point and re-solve the DTWs
        if dragDist > self.dragDensity :
            self.trace[self.nearestRoot].AddPoint( dragPosition )
            if debug > 0:
                loc = mc.spaceLocator(p=dragPosition)
                mc.parent(loc,"traceGrp")
        if self.trace[self.nearestRoot].timespan and len(self.trace[self.nearestRoot].points) > 4*self.substeps and \
           not mc.draggerContext( 'TraceGesture', query=True, modifier=True) == "ctrl":        
            if debug > 0: print "DTW solved to timespan of ",trace[nearestRoot].timespan
            mc.currentTime( self.trace[self.nearestRoot].timespan[1] )
            if dragDist > self.dragDensity:
                mc.refresh(currentView=True,force=True)
        elif dragDist > self.dragDensity:
            if debug > 0: print "No DTW, attempting closest path... point..."
            self.ScrubToNearestTimeOnPath( dragPosition, self.nearestRoot, self.nearestPath )
        if debug>0: print("end DRAG")    
    
    def TraceGestureRelease( self ):
        """ when the mouse is released, find the matching joint trajectory """
        if debug>0: print("begin RELEASE")
        releasePosition = Vector( mc.draggerContext( 'TraceGesture', query=True, dragPoint=True) ).projectToPlane( self.trace[self.nearestRoot].normal, planePt=self.trace[self.nearestRoot].planePt )
        if debug>0: print "release! ", releasePosition
        theTrace = self.trace[self.nearestRoot]
        selectedMotion = None
        if theTrace.closestJoint and theTrace.timespan and (theTrace.timespan[1]-theTrace.timespan[0]) > 1 and \
           not mc.draggerContext( 'TraceGesture', query=True, modifier=True) == "ctrl":        
            theDTW = theTrace.dtws[theTrace.closest]
            if debug > 0:
                print "closest = ", theTrace.closestJoint, theTrace.timespan
                if not mc.objExists("DTW_Y"):
                    mc.group(n="DTW_Y",empty=True)
                for pt in theDTW.Y:
                    loc = mc.spaceLocator(p=pt)
                    mc.parent(loc,"DTW_Y")
        ##    ghostJoint(trace[nearestRoot].closestJoint,trace[nearestRoot].timespan)

            # Build the motion curve and store it's name in the selectedMotions dictionary
            duration = [ int(theTrace.timespan[0]), int(theTrace.timespan[1]+1) ]
            keyframes = [ theTrace.searchList[theTrace.closestJoint].points[frame] for frame in range(duration[0],duration[1]) ]
            selectedMotion = bmt.CurveMotionTrace( theTrace.closestJoint, keys=keyframes ) #duration=theTrace.timespan )
            
        else:
            self.ScrubToNearestTimeOnPath( releasePosition, self.nearestRoot, self.nearestPath )
            cam2pop = self.CameraToPopDist()
            path = theTrace.searchList[self.nearestPath]
            pointKey = path.ClosestTimeTo(releasePosition)
            closestPoint = path.points[pointKey]
            closestPtOnPath = closestPoint.projectToPlane( theTrace.normal, planePt=theTrace.planePt )
            mouse2path = (releasePosition - closestPtOnPath).mag()
            # if motion paths are visible and no drag happened
            # and releasePosition is very close to the path,
            # then select the whole motion path
            if self.motionPathsVisible[self.nearestRoot] and mouse2path < 0.3:  
                # Build the motion curve and store it's name in the selectedMotions dictionary
                duration = [ mc.playbackOptions(q=True,min=True),mc.playbackOptions(q=True,max=True)+1 ]
                keyframes = [ theTrace.searchList[self.nearestPath].points[frame] for frame in range(duration[0],duration[1]) ]
                selectedMotion = bmt.CurveMotionTrace( self.nearestPath, keys=keyframes ) #duration=[mc.playbackOptions(q=True,min=True),mc.playbackOptions(q=True,max=True)] )

            # if not scrubbing
            if not mc.draggerContext( 'TraceGesture', query=True, modifier=True) == "ctrl" and \
               cam2pop >= self.viewFitDistance:      # if trucked out, and mouse is clicked (w/ no drag)
                mc.select(self.nearestRoot)     # zoom in on the nearest root for a better view
                mc.viewFit(fitFactor=2.5)            # the invisible parts of the roots can artificially enlarge the BB, so truck in a little extra
                mc.select(clear=True)
        if selectedMotion:
            selectedMotionCurve = selectedMotion.construct(self.nearestPath)
            
            if not self.nearestRoot in self.selectedMotions.keys():
                self.selectedMotions[self.nearestRoot] = []
            mc.setAttr("%s_MotionTraces.visibility"%self.nearestRoot, 0)
            selectedMotionCurve = mc.rename(selectedMotionCurve, "%s_selection%d"%(self.nearestPath,len(self.selectedMotions[self.nearestRoot])))
            self.selectedMotions[self.nearestRoot].append( selectedMotionCurve )
            self.AddCustomAttr( selectedMotionCurve, "isTraceSelection", True )
            self.AddCustomAttr( selectedMotionCurve, "interactTime", time.time()-self.startTime )
            self.AddCustomAttr( selectedMotionCurve, "startFrame", duration[0] )
            self.AddCustomAttr( selectedMotionCurve, "endFrame", duration[1] )
        mc.select(cl=True)
##        # select the related keyframes
##        if theTrace.closestJoint:
##            if debug > 0: print "anim channels are", self.GetAnimChans( mc.listRelatives( theTrace.closestJoint, parent=True ) )
##            mc.selectKey( clear=True )
##            jointParent = mc.listRelatives( theTrace.closestJoint, parent=True )[0]
##            for channel in self.GetAnimChans( jointParent ):
##                mc.selectKey( jointParent, time=(theTrace.timespan[0],theTrace.timespan[1]), attribute=channel.split(jointParent)[1].lstrip('_'), add=True )

    def GetAnimChans( self, joint ):
        """ Given a joint name, it finds the attached animation channels """
        mc.select(joint)
        atls = mc.listConnections(type="animCurveTL")
        atus = mc.listConnections(type="animCurveTU")
        atas = mc.listConnections(type="animCurveTA")
        atts = mc.listConnections(type="animCurveTT")

        chans = []
        if atls:
            chans.extend(atls)
        if atus:
            chans.extend(atus)
        if atas:
            chans.extend(atas)
        if atts:
            chans.extend(atts)

        return chans

    def AddCustomAttr( self, object, attrName, attrVal ):
        """ Adds a new attribute to an object and assigns the given name and value """
        typ = str(type(attrVal)).split('\'')[1]
        mc.select(object)
        
        if typ == 'str':
            mc.addAttr( longName=attrName, dataType='string'  )
            mc.setAttr( "%s.%s"%(object, attrName), attrVal, type="string")
        elif typ == 'int':
            mc.addAttr( longName=attrName, attributeType='long'  )
            mc.setAttr( "%s.%s"%(object, attrName), attrVal )
        else:
            mc.addAttr( longName=attrName, attributeType=typ  )
            mc.setAttr( "%s.%s"%(object, attrName), attrVal )
    
    def CameraToPopDist( self ):
        camPos = Vector(mc.xform(mc.lookThru(q=True),q=True,t=True))
        if self.nearestRoot:
            popPos = Vector(mc.objectCenter(self.nearestRoot))
        else:
            popPos = self.FindNearestObjectToCamera()
        return (camPos-popPos).mag()
    
    def ghostJoint( self, joint, framespan ):
        """ ghosts a given joint for a given span of frames """
        mc.setAttr( "%s.ghosting"%joint, 1)
        mc.setAttr( "%s.ghostingControl"%joint, 1)
        frameList = range(framespan[0],framespan[1])
        mc.setAttr( "%s.ghostFrames"%joint, frameList, type="Int32Array" ) 

    def ToggleAllMotionPathsVisibility( self ):
        """ shows/hides all the motion paths """
        allVizs = [mc.getAttr("%s.visibility"%group) for group in mc.ls(type="transform") if group.endswith("_MotionTraces")]
        if not all(allVizs):
            for group in mc.ls(type="transform"):
                if group.endswith("_MotionTraces"):
                    mc.setAttr("%s.visibility"%group, 1)
        else:
            for group in mc.ls(type="transform"):
                if group.endswith("_MotionTraces"):
                    mc.setAttr("%s.visibility"%group, 0)
                
    def FindRayPlaneIntersect( self, source, dest, plane ):
            """ given a source and destination (location) and a plane definition, 
                return the point along a line between the source and the destination
                that intersects the given plane """
            return plane.intersectWithRay(source,dest)

    def CameraViewAxis( self ):
        """ return the Z-axis of the lookThru camera """
        currentCam = mc.lookThru(q=True)
        return Vector( mc.xform(currentCam, q=True, m=True)[8:11] )
    
    def CameraPosition( self ):
        """ return the Z-axis of the lookThru camera """
        currentCam = mc.lookThru(q=True)
        return Vector(mc.xform(currentCam,q=True,t=True))

    def FindNearestObjectToCamera( self ):
        camPos = self.CameraPosition()
        minDist = float("inf")
        closestObj = Vector()
        for obj in self.xformRoots: 
            objPos = Vector(mc.objectCenter(obj))
            dist = ( camPos - objPos ).mag()
            if dist < minDist:
                minDist = dist
                closestObj = objPos
        return closestObj

    def FindNearestRoot( self, mousePos, plane ):
        """ find the root nearest to the mouse """
        nearest = None
        minDist = float("inf")
        for root in self.xformRoots: #trueCenterMatchString):
            path, dist = self.FindNearestMotionPath( mousePos, root, plane=plane)
            if minDist > dist:
                minDist = dist
                nearest = root
        if debug > 0: print "nearest root is ", nearest
        return nearest, minDist

    def FindNearestMotionPath( self, mousePos, root, plane=None ):
        """ Finds the motion path of the given root that is nearest the given mouse position """
        minDist = float("inf")
        for joint in sorted(self.trace[root].searchList.keys()):
            closestPoint = self.trace[root].searchList[joint].ClosestPointTo( mousePos, plane=plane )  #DistanceTo( mousePos, plane=plane )
            dist = (mousePos - closestPoint.projectToPlane(self.interactionPlane.normal,planePt=self.interactionPlane.point)).mag()
            if minDist > dist:
                minDist = dist
                nearestPath = joint
        if debug>0:  print "FindNearestMotionPath found nearest path: ", nearestPath
        return nearestPath, minDist

    def ScrubToNearestTimeOnPath( self, mousePos, root, motionPath ):
        """ Given the name of a joint (motion path), find the nearest
            point in time to the mouse location and change the current
            playback time to match """
        path = self.trace[root].searchList[motionPath]
        frame = path.ClosestTimeTo( mousePos, plane=self.interactionPlane )
        if debug>0: print "ScrubToNearestTimeOnPath setting time to: ", frame
        mc.currentTime( frame )
    
    def DrawJointMotionPaths( self, roots ):
        """ Gathers points for each joint of each root and build motion paths (optimized to only cycle thru timeline once) """
        # prep the data structure
        keypoints = {}
        for root in roots:
            keypoints[root] = {}
            #.split(':')[-1]
            joints = [j for j in mc.listRelatives( root, allDescendents=True ) if j in self.traceableObjs]  # TODO: just get the nearby joints by projecting them all onto the viewing plane and finding the distance
            for j in joints:
                keypoints[root][j] = []
        # cycle through the timeline and record data
        for t in range(int(mc.playbackOptions(q=True,minTime=True)), int(mc.playbackOptions(q=True,maxTime=True))+1):
            mc.currentTime(t)
            for root in roots:
                #.split(':')[-1]
                joints = [j for j in mc.listRelatives( root, allDescendents=True ) if j in self.traceableObjs]
                for j in joints:
                    keypoints[root][j].append( mc.xform( j, q=True, ws=True, translation=True ) )
        # use the data to build motion curves
        cols = [9,12,13,14,15,17,18,23,29,31]   # color indices for the display layers
        for root in roots:
            joints = [j for j in mc.listRelatives( root, allDescendents=True ) if j in self.traceableObjs]
            if len(joints) > 0:
                traceGroup = mc.group(n="%s_MotionTraces"%root,empty=True)
                curves = []
                for num, j in enumerate(joints):
                    curve = bmt.CurveMotionTrace( j, keys=keypoints[root][j] )
                    curveGeom = curve.construct("%s_trace"%j)
                    curves.append( curveGeom )   # add the motion paths to the trace's search list and set up the DTWs

                    displayLayerName = "%s_MotionPaths"%j#.split(':')[-1]
                    if not mc.objExists(displayLayerName):
                        mc.createDisplayLayer(name=displayLayerName)
                        mc.setAttr("%s.color"%displayLayerName, cols[num])  
                        mc.editDisplayLayerMembers( displayLayerName, curveGeom )
                    else:
                        objs = mc.editDisplayLayerMembers(displayLayerName, query=True )
                        if objs:
                            objs.append( curveGeom )
                        else:
                            objs = [curveGeom]
                        mc.editDisplayLayerMembers( displayLayerName, objs )
                mc.parent(curves, traceGroup)
                mc.parent(traceGroup, root)
                mc.select(cl=True)
                
            
    def LoadJointMotionPaths( self, roots ):
        """ prep the data structure that holds the motion paths """
        animPaths = {}
        for root in roots:
            animPaths[root] = {}
            self.trace[root] = Trajectory("%sTrace"%root)
            # find all nearby joints
            joints = [j for j in mc.listRelatives( root, allDescendents=True ) if j in self.traceableObjs]  # TODO: just get the nearby joints by projecting them all onto the viewing plane and finding the distance
            # get the motion path of each nearby joint
            if len(joints) > 0:
                for j in joints:
                    animPaths[root][j] = Trajectory( "%s_path"%j )
                    if debug > 0:
                        mc.group(name="%sGrp"%j,empty=True)
        
        startFrame = mc.playbackOptions(q=True,minTime=True)
        endFrame = mc.playbackOptions(q=True,maxTime=True)+1
        for t in [float(x)/self.substeps+startFrame for x in range(0, int(endFrame-startFrame)*self.substeps)]:
            mc.currentTime(t)
            for root in roots:
                joints = [j for j in mc.listRelatives( root, allDescendents=True ) if j in self.traceableObjs]
                for j in joints:
                    point = Vector( mc.xform(j, q=True, ws=True, t=True) ) 
                    animPaths[root][j].AddPoint( point, t )
                    if debug > 0:
                        loc = mc.spaceLocator(p=point)
                        mc.parent(loc,"%sGrp"%j)
                self.trace[root].SetSearchList( animPaths[root] )

def findXformRoot( jointRoot ):
    """ Returns the transform root of a given jointRoot """
    for parent in mc.listRelatives( jointRoot, allParents=True ):
        if not mc.listRelatives( parent, parent=True ):
            return parent
    return jointRoot

def findIKhandles():
    """ Returns a list of all IK handles in the scene """
    return mc.ls(type="ikHandle")

def findRoots():
    """ Returns a list that contains the root joint for all joint heirarchies in the scene """
    roots = []
    for joint in mc.ls(type="joint"):
        if( mc.nodeType(mc.listRelatives(joint,parent=True)) != "joint" ):
            roots.append(joint)
    return roots

def findEndEffectorJoints( root ):
    """ Returns a list of the leaf joints in a given rig (specified by the root joint).
        Ignores leaf joints that have an incoming IK handle connection. """
    leafs = []
    for joint in mc.listRelatives(root, allDescendents=True, type="joint"):
        if( not( mc.listRelatives(joint, type="joint", children=True) ) and                    # if joint has no joint children
            not( 'ikEffector' in [mc.nodeType(n) for n in mc.listConnections(joint)] ) ):      # if joint has no incoming IK connection
            leafs.append( joint )
    return leafs

def findRootsFromTraceables(traceables):
    jointRoots = []
    xformRoots = []
    for thing in traceables:
        itr = thing
        pitr = mc.listRelatives( itr, parent=True ) 
        while pitr:
            itr = pitr[0]
            pitr = mc.listRelatives( itr, parent=True )
            if mc.nodeType(itr) == "joint" and (not pitr or mc.nodeType(pitr) != "joint") and not itr in jointRoots:
                jointRoots.append( itr )
        if not itr in xformRoots:
            xformRoots.append( itr )
    return jointRoots, xformRoots

def autoFindTraceables():
    jointRoots = findRoots()
    xformRoots = [findXformRoot(r) for r in jointRoots]
    # find the important parts of each rig -- so that trajectories can be built for them
    traceableObjs = []
    traceableObjs.append( jointRoots )      # joint roots of each joint hierarchy
    traceableObjs.append( xformRoots )      # DAG roots of each joint hierarchy (topmost transform)
    traceableObjs.extend( findIKhandles() ) # all IK handles in the scene
    for root in jointRoots:
        traceableObjs.extend( findEndEffectorJoints(root) )   # all end-effector joints under the root
    return jointRoots, xformRoots, traceableObjs
    
def main( traceables=None ):
    global traceSelect

    if(traceables):
        traceableObjs = traceables
        jointRoots, xformRoots = findRootsFromTraceables(traceables)
    else:
        jointRoots, xformRoots, traceableObjs = autoFindTraceables()
        
    # if nothing traceable is in the scene, give up
    if len(xformRoots) == 0:
        mc.warning("no trace-able objects (e.g. joints or IK handles) are in your scene.")
        return None
              
    # otherwise, keep going...
    traceSelect = TraceSelection( xformRoots, traceableObjs )
    
    # Define draggerContext with press and drag procedures
    if not traceSelect.forceReload and mc.draggerContext( 'TraceGesture', exists=True ) :
        mc.draggerContext( 'TraceGesture', edit=True, space='world',
                           pressCommand='traceSelect.TraceGesturePress()',
                           dragCommand='traceSelect.TraceGestureDrag()',
                           releaseCommand='traceSelect.TraceGestureRelease()',
                           cursor='default')

    else:
        mc.draggerContext( 'TraceGesture', space='world',
                           pressCommand='traceSelect.TraceGesturePress()',
                           dragCommand='traceSelect.TraceGestureDrag()',
                           releaseCommand='traceSelect.TraceGestureRelease()',
                           cursor='default')
    if len(mc.ls('*_MotionPaths')) == 0:
        # if first time script has been called on this scene
        traceSelect.DrawJointMotionPaths(xformRoots)

    traceSelect.LoadJointMotionPaths(xformRoots)
        
    mc.setToolTo('TraceGesture')
    return traceSelect

if __name__ == "__main__":
    main()
