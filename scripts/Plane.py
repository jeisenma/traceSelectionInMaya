## a minimal 3D Plane class
## J Eisenmann
## ACCAD, The Ohio State University
## 2012

from Vector import *

class Plane:
    """ 3D Plane class """
    def __init__(self, normal, point):
        self.normal = Vector(normal).norm()
        self.point = Vector(point)

    def intersectWithRay(self, pointA, pointB):
        """ find intersection of this plane with the given ray """
        a = Vector(pointA)
        b = Vector(pointB)
        direction = (b-a).norm()
        denom = direction*self.normal
        if denom == 0:
            return None # there's no intersection
        else:
            d = (self.point - a)*self.normal
            d /= denom
            return a + direction*d
    
        
