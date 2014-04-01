from collections import Counter
import numpy as np

class BoundingBox():
    def __init__(self, points):
        self.x0 = int(points[0])
        self.y0 = int(points[1])
        self.x1 = int(points[2])
        self.y1 = int(points[3])
    
    def __str__(self):
        return 'x0:%d y0:%d,  x1:%d y1:%d' %( self.x0, self.y0, self.x1, self.y1 )
    
    @property
    def width(self):
        return self.x1 - self.x0 

    @property
    def height(self):
        return self.y1 - self.y0 
    
    def is_inside(self, other_box):
        """ Determine if this object is within the provided bounding_box """
        if self.x0 >= other_box.x0 and \
           self.x1 <= other_box.x1 and \
           self.y0 >= other_box.y0 and \
           self.y1 <= other_box.y1:
               return True
        else:
            return False

    def vertical_overlap(self, other_box):
        """ Return the vertical overlap of this object and the provided bounding_box """
        return self._get_overlap((self.y0, self.y1),(other_box.y0, other_box.y1))

    def horizontal_overlap(self, other_box):
        """ Return the horizontal overlap of this object and the provided bounding_box """
        return self._get_overlap((self.x0, self.x1),(other_box.x0, other_box.x1))

    def _get_overlap(self, interval_one, interval_two):
        """ Private function to determine overlap of two intervals """
        return max(0, min(interval_one[1], interval_two[1]) - max(interval_one[0], interval_two[0]))

def derive_bounding_box(children):
    temp_box = []
    for child in children:
        if len(temp_box) == 0 :
            temp_box.append(child.box.x0)
            temp_box.append(child.box.y0)
            temp_box.append(child.box.x1)
            temp_box.append(child.box.y1)
        else:
            temp_box[0] = min( child.box.x0, temp_box[0] )
            temp_box[1] = min( child.box.y0, temp_box[1] )
            temp_box[2] = max( child.box.x1, temp_box[2] )
            temp_box[3] = max( child.box.y1, temp_box[3] )
    return BoundingBox(temp_box)

class hOCRObject():
    def __init__(self, element):
        self.box = BoundingBox(element['title'].split()[1:])
        self.text = element.string 

    @property
    def width(self):
        return self.box.width 

    @property
    def height(self):
        return self.box.height 

    def recalculate_bounding_box(self):
        self.box = derive_bounding_box(self.children)

class Word(hOCRObject):
    def __init__(self, element):
        if element.has_attr('xml:lang') or element.has_attr('lang'):
            self.content_type = 'GREEK'
        else:
            self.content_type = 'LATIN' 
        super().__init__(element)
        # I don't strictly want to use the element attributes to set label
        self.label = self.content_type

class Line(hOCRObject):
    def __init__(self, element, children):
        self.children = children
        super().__init__(element)
        # Some line dimensions don't seem to actually fit the contained words, so we'll just always do this.
        self.box = derive_bounding_box(self.children) 
    
    @property
    def avg_height(self):
        """ Calculate the average height of the child elements """
        heights = [c.height for c in self.children]
        return sum(heights)/len(heights)

    @property 
    def most_common_type(self):
        """ """
        return Counter([w.content_type for w in self.children]).most_common()[0][0]

class Area(hOCRObject):
    def __init__(self, box, children):
        self.box = box
        self.children = children
        self.label = ""
    
    def is_single_line(self):
        """ Returns true if area contains only one line. Test for titles et al. """
        if len(self.children) == 1:
            return True
        else:
            return False
    @property
    def avg_line_height(self):
        heights = [s.height for s in self.children]
        if heights:
            return sum(heights)/len(heights)

class Page(hOCRObject):
    def __init__(self, children):
        self.children = children
        if children:
            self.box = derive_bounding_box(children)
            self.line_spaces = self._generate_line_spaces()
        else:
            self.box = BoundingBox([0,0,0,0])

    def _generate_line_spaces(self):
        line_spaces = []
        for i, l in enumerate(self.children):
            next_line = i + 1
            if not next_line >= len(self.children):
                line_spaces.append(BoundingBox([self.box.x0, l.box.y1, self.box.x1, self.children[next_line].box.y0]))
        return line_spaces

    def avg_line_spacing(self):
        heights = [s.height for s in self.line_spaces]
        if heights:
            return sum(heights)/len(heights)

    def avg_line_x(self, extremity):   
        """ Get the median start or end point of a line
            0 = start, 1 = end """
        # I want to use this regardless of current page state
        if isinstance(self.children[0], Area):
            lines = []
            for area in self.children:
                lines.extend(area.children)
        if isinstance(self.children[0], Line):
            lines = self.children
        if extremity == 'START':
            x = [l.children[0].box.x0 for l in lines]
        if extremity == 'END':
            x = [l.children[-1].box.x1 for l in lines]
        return np.median(x)
    
    def recalculate_spaces(self):
        self.line_spaces = self._generate_line_spaces()


#'ocr_word': Word, 'ocr_line': Line, 'ocr_carea': Area
