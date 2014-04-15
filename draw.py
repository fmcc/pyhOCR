import svgwrite
from PIL import Image
import os
import re

# Some adapted colour schemes pulled from the ete2 package
COLOR_SCHEMES = {'accent': ['#7fc97f','#beaed4','#fdc086','#ffff99','#386cb0','#f0027f','#bf5b17','#666666'],
'brbg': ['#543005','#8c510a','#bf812d','#dfc27d','#f6e8c3','#c7eae5','#80cdc1','#35978f','#01665e','#003c30'],
'dark2': ['#1b9e77','#d95f02','#7570b3','#e7298a','#66a61e','#e6ab02','#a6761d','#666666'],
'paired': ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928'],
'pastel1': ['#fbb4ae','#b3cde3','#ccebc5','#decbe4','#fed9a6','#ffffcc','#e5d8bd','#fddaec','#f2f2f2'],
'pastel2': ['#b3e2cd','#fdcdac','#cbd5e8','#f4cae4','#e6f5c9','#fff2ae','#f1e2cc','#cccccc'],
'set1': ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#ffff33','#a65628','#f781bf','#999999'],
'set2': ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854','#ffd92f','#e5c494','#b3b3b3'],
'set3': ['#8dd3c7','#ffffb3','#bebada','#fb8072','#80b1d3','#fdb462','#b3de69','#fccde5','#d9d9d9','#bc80bd','#ccebc5', '#ffed6f'],
'spectral': ['#9e0142','#d53e4f','#f46d43','#fdae61','#fee08b','#ffffbf','#e6f598','#abdda4','#66c2a5','#3288bd','#5e4fa2'],
}

LABELS = [
'HEADER',
'TITLE',
'LINE_NO',
'APP_CRIT',
'FOOTER',
'LATIN',
'GREEK',
'0', 
'1',
'2',
'']

def produce_svg_file(page, original_file_path):
    """ Create a SVG visualisation of the contents of a hOCR file from the 'Tree' representation """
    colours = dict(zip(LABELS,COLOR_SCHEMES['set3']))
    
    base_path = os.path.join(os.path.dirname(original_file_path), '../')
    filename = os.path.join(base_path, 'svg',  re.sub('html','svg', os.path.basename(original_file_path)))
    # There may be nothing on the page
    if len(page.children) == 0 :
        svg_drawing = svgwrite.Drawing(filename=filename)
        return
    # We open the original jpg to get the size that the image should be.  
    jpg_name = re.sub('html','jpg', os.path.basename(original_file_path))
    img = Image.open(os.path.join(base_path, 'original_images', jpg_name))
    svg_drawing = svgwrite.Drawing(filename=filename, size=img.size)
 
    for area in page.children:
        svg_drawing.add(svg_drawing.rect((area.box.x0, area.box.y0), (area.width, area.height), fill=colours[str(area.label)]))
        for line in area.children:
            for word in line.children:
                svg_drawing.add(svg_drawing.rect((word.box.x0, word.box.y0), (word.width, word.height), fill=colours[word.label]))
                #svg_drawing.add(svg_drawing.text(word.text, insert = (word.box.x0, word.box.y1)))
    #for line in page.children:
    #    svg_drawing.add(svg_drawing.rect((line.box.x0, line.box.y0), (line.width, line.height), fill=colours[str(line.label)]))
    #svg_drawing.add(svg_drawing.rect(page.vertical_gap[0], page.vertical_gap[1], fill='green' ))
    
    svg_drawing.save()

