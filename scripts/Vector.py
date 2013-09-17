## Vector class
## J Eisenmann
## ACCAD, The Ohio State University
## 2012

from random import uniform as _VectorUniform     # be careful here to not import on top of 
from math import sqrt as _VectorSqrt             # other imports that may already exist
from math import acos as _VectorAcos

class Vector(list):
    """ Vector class: 3D vector storage and operations """
    def __init__(self, x=0, y=0, z=0):
        """ Constructor -- you can either pass in a
            Vector or three separate values or a list
            with three values """
        try:
            list.__init__(self, [x.x, x.y, x.z])
            self.x = x.x
            self.y = x.y
            self.z = x.z
        except:
            try:
                list.__init__(self, x)
                self.x = x[0]
                self.y = x[1]
                self.z = x[2]
            except:
                list.__init__(self, [x, y, z])
                self.x = x
                self.y = y
                self.z = z

    def asList(self):
        """ Returns the vector as a list """
        return [self.x, self.y, self.z]
    
    def mag(self):
        """ Returns the length of the vector. """
        return _VectorSqrt(self.dot(self))

    def norm(self):
        """ Returns a normalized version of the vector. """
        return self*(1.0/self.mag())

    def distTo(self, other):
        """ Returns the length of the vector between this point and another. """
        return (other-self).mag()

    def angleBetween(self,other):
        """ Returns the angle between this vector and another (radians) """
        if(self.mag() == 0 or other.mag() == 0):
            return 0
        else:
            #return _VectorAcos(min(1,max(0,self.dot(other)/(self.mag()*other.mag()))))
            return _VectorAcos(min(1,max(-1,self.dot(other)/(self.mag()*other.mag()))))

    def random(self, hi=0.0, lo=1.0):
        """ Assigns random values [hi,lo] to the vector components. """
        self.x = _VectorUniform(hi,lo)
        self.y = _VectorUniform(hi,lo)
        self.z = _VectorUniform(hi,lo)
    
    def add(self, other):
        """ Adds the other vector to myself. """
        self.x += other.x
        self.y += other.y
        self.z += other.z

    def __len__(self):
        """ Returns the length -- always 3 """
        return 3
        
    def __add__(a,b):
        """ Returns the addition of two vectors. """
        result = Vector(a.x,a.y,a.z)
        result.add(b)
        return result

    def sub(self, other):
        """ Subtracts the other vector from myself. """
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z

    def __sub__(a,b):
        """ Returns the subtraction of two vectors. """
        result = Vector(a.x,a.y,a.z)
        result.sub(b)
        return result

    def __neg__(a):
        """ Returns the negation of a vector. """
        result = Vector(a.x,a.y,a.z)
        result.mult(-1)
        return result
    
    def mult(self, factor):
        """ Multiplies my values by a factor. """
        self.x *= factor
        self.y *= factor
        self.z *= factor

    def dot(self, other):
        """ Returns the dot product between another vector and myself. """
        return self.x*other.x + self.y*other.y + self.z*other.z

    def __div__(self, factor):
        """ divides each element in this vector by the given factor """
        result = Vector(self)
        result *= 1.0/factor
        return result
    
    def __mul__(self, other):
        """ If two vectors are provided, returns the dot product.
            If a vector and a number are provided, returns the
            multiplication of the two. """
        result = Vector(self)
        try:
            return result.dot(other)
        except:
            result.mult(other)
            return result
        
    def __rmul__(self,other):
        """ If two vectors are provided, returns the dot product.
            If a vector and a number are provided, returns the
            multiplication of the two. """
        result = Vector(self)
        try:
            return result.dot(other)
        except:
            result.mult(other)
            return result

    def power(self, factor):
        """ Raise each of my values to a power specified by factor """
        self.x = self.x**factor
        self.y = self.y**factor
        self.z = self.z**factor
    
    def cross(self, other):
        """ Returns the cross product of myself with the other vector. """
        return Vector(self.y*other.z - other.y*self.z,
                       self.z*other.x - other.z*self.x,
                       self.x*other.y - other.x*self.y)

    def projectToPlane(self, normal, planePt=None):
        """ projects this point onto an origin-intersecting plane with
            the given normal """
        temp = Vector(self)
        normal = normal.norm()                  # Make sure normal is normalized
        if planePt:
            length = (temp-planePt).dot(normal) #/(normal*normal) # Find the length along the normal from the point 
            return temp - normal*length            # to plane intersecting the origin
        else:
            length = (temp).dot(normal) #/(normal*normal) # Find the length along the normal from the point 
            return temp - normal*length            # to plane intersecting the origin

    def __pow__(a,b):
        """ If two vectors are provided, returns the cross product.
            If a vector and a number are provided, returns the
            vector raised to a power specified by the number. """
        result = Vector(a.x,a.y,a.z)
        try:
            return result.cross(b)
        except:
            result.power(b)
            return result

    def __getitem__(self, index):
        """ Returns the value corresponding to a numerical index:
                0 -> x, 1 -> y, 2 -> z """
        if(index == 0):
            return self.x
        elif(index == 1):
            return self.y
        elif(index == 2):
            return self.z
        else:
            raise Exception("Index %d is out of bounds: Vector class only has valid indices 0-2"%index)

    def __setitem__(self, index, value):
        """ Sets the value corresponding to a numerical index:
                0 -> x, 1 -> y, 2 -> z """
        if(index == 0):
            self.x = value
        elif(index == 1):
            self.y = value
        elif(index == 2):
            self.z = value
        else:
            raise Exception("Index %d is out of bounds: Vector class only has valid indices 0-2"%index)

    def __len__(self):
        return 3
    
    def __repr__(self):
        """ So we can call print on a vector object """
        return "< %.3f, %.3f, %.3f >"%(self.x, self.y, self.z)
