

class BBox():
    def __init__(self, box_string):
        vals = box_string.split()[1:]
        self.x0 = int(vals[0])
        self.y0 = int(vals[1])
        self.x1 = int(vals[2])
        self.y1 = int(vals[3])
    
    @property
    def width(self):
        return self.x1 - self.x0 

    @property
    def height(self):
        return self.y1 - self.y0 

class hOCRObject():

    def __init(self):
        self.box = BBox()

    @property
    def width(self):
        return self.x1 - self.x0 

    @property
    def height(self):
        return self.y1 - self.y0 


class Word(hOCRObject):
    pass

    
class Line(hOCRObject):
    pass

    
class Area(hOCRObject):
    pass

