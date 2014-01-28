from bs4 import BeautifulSoup as BS
import svgwrite

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

def parse(text, name):
    text_soup = BS(text)
    spans = text_soup.find_all('span',{'class':'ocr_line'})
    boxes = [BBox(s['title']) for s in spans]
    if not boxes:
        return
    max_x = max([b.x1 for b in boxes])
    max_y = max([b.y1 for b in boxes])
    svg_drawing = svgwrite.Drawing(filename=name, size=(max_x + 100, max_y+ 100))
    for b, s in zip(boxes, spans):
        colour = 'blue'
        if s.has_attr('xml:lang') or s.has_attr('lang'):
            colour = 'red'
        svg_drawing.add(svg_drawing.rect((b.x0, b.y0), (b.width, b.height), fill=colour))
    svg_drawing.save()
