## A Collection of NURBS curve utility functions
## J Eisenmann
## ACCAD, The Ohio State University
## 2012-13

from math import *
from Vector import *

import maya.cmds as mc
import maya.mel as mm

mc.loadPlugin("closestPointOnCurve", quiet=True)

def drawLine(pt1, pt2):
    try:    # if pt1 and pt2 are Vectors
        mc.curve( p=[pt1.asTuple(), pt1.asTuple(), pt2.asTuple(), pt2.asTuple()] )
    except: # if pt1 and pt2 are tuples or lists
        mc.curve( p=[pt1, pt1, pt2, pt2] )
    
def connectedNodeOfType( curve, type ):
    for node in mc.connectionInfo( curve+".worldSpace", destinationFromSource=True):
        if( type == mc.nodeType(node) ):
            return node.split('.')[0].split('>')[-1]
    return None
          
def getCurveInfoNode( curve ):
    infoNode = connectedNodeOfType( curve, "curveInfo" )
    if not infoNode:
        print "adding an info node to curve: "+curve
        infoNode = mc.createNode("curveInfo")
        mc.connectAttr( curve+".worldSpace", infoNode+".inputCurve")
    return infoNode

def getCurveArcLenDimNode( curve ):
    arcLenDimNode = connectedNodeOfType( curve, "arcLengthDimension" )
    if not arcLenDimNode:
        max = mc.getAttr( curve+".maxValue" )
        print "adding an arcLengthDimension node to curve: "+curve
        arcLenDimNode = mc.arcLengthDimension( curve+".u[%f]"%max )
    return arcLenDimNode

def getClosestPointNode( curve ):
    cpNode = connectedNodeOfType( curve, "closestPointOnCurve" )
    if not cpNode:
        print "adding a closestPointOnCurve node to curve: "+curve
        cpNode = mc.closestPointOnCurve(curve);
    return cpNode

def findParamAtPoint( curve, point ):
    cpNode = getClosestPointNode( curve )
    mc.setAttr(cpNode+".inPosition", point[0], point[1], point[2] )
    return mc.getAttr(cpNode+".paramU")

def findArcLenAtParam( curve, param ):
    arcLenDimNode = getCurveArcLenDimNode( curve )
    mc.setAttr( arcLenDimNode+".uParamValue", param )
    return mc.getAttr( arcLenDimNode+".arcLength" )

def curveArcLen( curve ):
    max = mc.getAttr( curve+".maxValue" )
    arcLength = findArcLenAtParam( curve, max )
    return arcLength

def findParamAtArcLen( curve, distance, epsilon=0.0001 ):
    """ Returns the U parameter value at a specified length along a curve
        (Adapted from: http://ewertb.soundlinker.com/mel/mel.108.php) """
    
    u = 0.0

    min = mc.getAttr( curve+".minValue" )
    max = mc.getAttr( curve+".maxValue" )

    arcLength = findArcLenAtParam( curve, max )

    # Don't bother doing any work for the start or end of the curve.
    if ( distance <= 0.0 ):
        return 0.0
    if ( distance >= arcLength ):
        return max

    # This is merely a diagnostic to measure the number of passes required to 
    # find any particular point. You may be surprised that the number of 
    # passes is typically quite low.
    passes = 1

    while ( True ):
        u = ( min + max ) / 2.0
        #mc.setAttr( arcLenDimNode+".uParamValue", u)
        arcLength = findArcLenAtParam( curve, u ) #mc.getAttr( arcLenDimNode+".arcLength" )
        if ( abs(arcLength-distance) < tol ):
            break
        if ( arcLength > distance ):
            max = u
        else:
            min = u
        passes+=1

    return u

def findParamAtArcPercent( curve, percent, epsilon=0.0001 ):
    """ Returns the U parameter value at a specified % of the length along a curve """

    max = mc.getAttr( curve+".maxValue" )
    arcLength = findArcLenAtParam( curve, max ) 
    return findParamAtArcLen( curve, percent*arcLength, epsilon )

def findCVsInRange( curve, start, end ):
    """ Returns a list of the (index, u)'s of the CVs of "curve" that have u parameter
        values between "start" and "end" (percentages of arc length) """
    indices = []
    if( end >= start and start >= 0.0 and end <= 1.0):
        a = findParamAtArcPercent( curve, start )
        b = findParamAtArcPercent( curve, end )
        # get CV positions in local (object) space
        CVs = mc.getAttr( curve+".cv[*]" )
        # translate them into global (world) space
        CVs = [(Vector(cv)+Vector(mc.xform(curve, q=True, ws=True, translation=True))).asTuple() for cv in CVs]
        for I,cv in enumerate(CVs):
            U = findParamAtPoint(curve, cv)
            L = findArcLenAtParam(curve, U)/curveArcLen(curve)  # arc length as a percentage
            if( a <= U and U <= b ):
                indices.append((I,U,L))
    return indices
    
def arcCurve( curve, t1, t2 ):
    """ Perturb the tangents on the initial curve """
    cv1 = list(mc.getAttr( curve+".cv[1]" )[0])
    cv2 = list(mc.getAttr( curve+".cv[2]" )[0])
    print cv1, cv2
    for i in range(3):
        cv1[i] += t1[i]
        cv2[i] += t2[i]
    mc.setAttr( curve+".cv[1]", cv1[0], cv1[1], cv1[2] )
    mc.setAttr( curve+".cv[2]", cv2[0], cv2[1], cv2[2] )
    return curve

def evenlyDivideCurve( curve, numDiv ):
    """ Divides a curve into numDiv.
        Assumes there are two CVs at the start and end of the curve """
    # first, move the curve to the origin
    translation = mc.xform(curve, q=True, ws=True, translation=True)
    rotation = mc.xform(curve, q=True, ws=True, rotation=True)
    mc.move(0, 0, 0, curve)
    mc.rotate(0, 0, 0, curve)

    # get the curve info node
    infoNode = getCurveInfoNode(curve)
    Knots = list( mc.getAttr( infoNode+".knots" )[0] )
    CVs = mc.getAttr( curve+".cv[*]" )
    numOrigCVs = len(CVs)
    numOrigKnots = len(Knots)

    if( not numOrigCVs == 4 ):
        print("ERROR: original curve must have exactly 4 CVs")
        return
    else:
        for p in range(0,(numDiv-numOrigCVs+4+1)):
            percent = (p-1)/float(numDiv-2)
            u = findParamAtArcPercent( curve, percent )
            if p < 2 or p >= (numDiv-numOrigCVs+3):
                CVs[p] = tuple(mc.pointOnCurve(curve, parameter=u))
            else:
                CVs.insert(p, tuple(mc.pointOnCurve(curve, parameter=u)) )
                Knots.insert(p+1, u)
    curve = mc.curve( curve,r=True, p=CVs, k=Knots)

    mc.move(translation[0], translation[1], translation[2], curve)
    mc.rotate(rotation[0], rotation[1], rotation[2], curve)
    return curve

def bias(b, t):
    return t**(log(b)/log(0.5))

def gain(g, t):
    if(t<0.5):
        return 0.5*bias(1-g,2*t)
    else:
        return 1-bias(1-g,2-2*t)/2.0

def smoothstep(a, fuzz, t):
    if(t < a-fuzz):
        return 0.0
    elif(t > a):
        return 1.0
    else:
        return gain(0.9, (t-(a-fuzz))/fuzz)

def pulse(a, b, fuzz, t):
    return smoothstep(a, fuzz, t) - smoothstep(b, fuzz, t)

def oscillateCurve( curve, start=0.0, end=1.0, freq=1.0, ease=0.5, strength=1.0 ):
    """ Oscillates a given curve by moving each vertex in an alternating
        direction based on the normal.  This process takes place over the
        range defined by "start" and "end" as percentages of arc length.
        Oscillation eases to full strength as determined by the "ease" and
        "strength" arguments. """
    if(ease > (end-start)*0.5):
        ease = (end-start)*0.5
    if(start < end):
        CVs = mc.getAttr( curve+".cv[*]" )
        newCVs = findCVsInRange(curve, start, end)
        for (I,U,L) in newCVs:
            interp = (L-start)/(end-start)
            osc = sin(freq*interp)
            scale = pulse(start+ease, end, ease, L)  # ease must be between 0 and 0.5
## Don't use Maya's normalized normal -- it flip flops with curvature so it's not good for oscillating offset
#            normal = Vector(mc.pointOnCurve(curve, parameter=cv[1], normalizedNormal=True))
#            if(normal.mag() == 0.0):
#                print "Getting normal from up x tangent"
            normal = Vector(0,1,0)**Vector(mc.pointOnCurve(curve, parameter=U, tangent=True))
            normal = normal.norm()
            pos = Vector(CVs[I])
            pos = pos+normal*scale*strength*osc
            CVs[I] = pos.asTuple()

    for i,cv in enumerate(CVs):
        mc.setAttr(curve+".cv[%d]"%i, cv[0], cv[1], cv[2])

    return curve

def noise(x=0, y=None, z=None):
    """ Returns a Perlin noise value based on 1D or 3D input """
    try:
        if( isinstance(x, Vector) ):                                 # if x is a Vector
            return mm.eval("noise <<%f, %f, %f>>"%x.asTuple())
        elif( len(x) == 3 ):                                    # if x is a sequence
            return mm.eval("noise <<%f, %f, %f>>"%x)
    except:
        if(not y == None and not z == None):                # if y and z have values
            return mm.eval("noise <<%f, %f, %f>>"%(x,y,z))
        else:                                               # otherwise just use 1D data
            return mm.eval("noise %f"%x)

def noiseCurve( curve, start=0.0, end=1.0, freq=1.0, ease=0.5, strength=1.0 ):
    """ Adds noise to a given curve by moving each vertex with Perlin
        noise based on the normal.  This process takes place over the
        range defined by "start" and "end" as percentages of arc length.
        Noise eases to full strength as determined by the "ease" and
        "strength" arguments. """
    if(ease > (end-start)*0.5):         # ease must be between 0 and 0.5
        ease = (end-start)*0.5
    if(start < end):
        CVs = mc.getAttr( curve+".cv[*]" )
        newCVs = findCVsInRange(curve, start, end)
        for (I,U,L) in newCVs:
            interp = (L-start)/(end-start)
            noiz = noise(freq*interp)
            scale = pulse(start+ease, end, ease, L)  
            normal = Vector(0,1,0)**Vector(mc.pointOnCurve(curve, parameter=U, tangent=True))
            normal = normal.norm()
            pos = Vector(CVs[I])
            pos = pos+normal*scale*strength*noiz
            CVs[I] = pos.asTuple()
    for i,cv in enumerate(CVs):
        print(curve+".cv[%d]"%cv[0], cv[0], cv[1], cv[2])
        mc.setAttr(curve+".cv[%d]"%i, cv[0], cv[1], cv[2])

def twistCurve( curve, start=0.0, end=1.0, freq=1.0, ease=0.5, strength=1.0 ):
    """ Twist the curve over the range defined by "start" and "end" as percentages of arc length.
        The twist operation happens in world space. Twist eases to full strength as determined by
        the "ease" and "strength" arguments. """
    if(ease > (end-start)*0.5):         # ease must be between 0 and 0.5
        ease = (end-start)*0.5
    if(start < end):
        CVs = mc.getAttr( curve+".cv[*]" )
        newCVs = findCVsInRange(curve, start, end)
        for (I,U,L) in newCVs:
            interp = (L-start)/(end-start)
            bounds = mc.exactWorldBoundingBox(curve)
            boundsXmin = bounds[0]
            boundsWidth = bounds[3] - bounds[0]
            boundsZcenter = (bounds[2]+bounds[5])*0.5
            scale = pulse(start+ease, end, ease, L)
            twistT = (((CVs[I][0] - boundsXmin)/boundsWidth))*2*pi*freq
            print "(((%f - %f)/%f)) = %f  -->  %f"%(CVs[I][0],boundsXmin,boundsWidth,(((CVs[I][0] - boundsXmin)/boundsWidth)), twistT)
            CVs[I] = (CVs[I][0],
                      0, 
                      scale*strength*((CVs[I][2]-boundsZcenter)*sin(twistT) + CVs[I][1]*cos(twistT)) + boundsZcenter)
                      
    for i,cv in enumerate(CVs):
        mc.setAttr(curve+".cv[%d]"%i, cv[0], cv[1], cv[2])
        
def printCurveDetails( curve ):
    infoNode = getCurveInfoNode(curve)
    Knots = list( mc.getAttr( infoNode+".knots" )[0] )
    CVs = mc.getAttr( curve+".cv[*]" )
    print "Curve Details for: "+curve
    for k in Knots:
        print k
    for cv in CVs:
        print cv
    
