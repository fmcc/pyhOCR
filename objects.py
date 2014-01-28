class BoundingBox():
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
    def __init__(self, element):
        self.box = BoundingBox(element['title'])
        self.text = element.string 

    @property
    def width(self):
        return self.box.width 

    @property
    def height(self):
        return self.box.height 

class Word(hOCRObject):
    def __init__(self, element):
        self.box = BoundingBox(element['title'])
    
class Line(hOCRObject):
    def __init__(self, element):
        self.box = BoundingBox(element['title'])
    
class Area(hOCRObject):
    pass

