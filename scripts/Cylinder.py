## A minimal 3D Rectangle class
## J Eisenmann
## ACCAD
## Dec 2012

from Vector import *

class Cylinder:
    """ A 3D Cylinder class """
    
    def __init__( self, center, axis, radius ):
        assert  type(center) == Vector and type(axis) == Vector
        self.center = center
        self.axis = axis
        self.radius = radius
        
    def DistToAxis( self, point ):
        """ finds the distance between a point and the cylinder's axis """
        x1 = self.center
        x2 = x1+self.axis
        return ((point-x1).cross(point-x2)).mag() / (x2-x1).mag()
    
    def Contains( self, point ):
        """ Determines if the point lies within this rectangle """
        return self.DistToAxis( point ) < self.radius
        
