from bs4 import BeautifulSoup as BS
from .objects import *
import svgwrite
from PIL import Image
import itertools
import collections
import re
import os

def generate_tree(text_in):
    # This is not readable - rewrite. 
    return Page(
        [ Line(line, 
            [ Word(word) 
                for word in line.find_all( True, { 'class' : 'ocr_word' } ) 
            ] ) 
            for line in text_in.find_all( True, { 'class' , 'ocr_line' } ) 
        ] )
        
def reparse_tree(page):
    
    def merge_parallel_lines(page):
        """ Merge lines that are parallel in a single column layout to a single """ 
        defunct_lines = []
        for line_pair in itertools.combinations(page.children, 2):
            if line_pair[0].box.vertical_overlap(line_pair[1].box) and not line_pair[0].box.horizontal_overlap(line_pair[1].box):
                # add the children from one line to another
                line_pair[0].children.extend(line_pair[1].children)
                line_pair[0].recalculate_bounding_box()
                # add second line to those to be removed
                defunct_lines.append(line_pair[1])
        for line in defunct_lines:
            page.children.remove(line)
        page.recalculate_spaces()
        return page 

    def section_break_spaces(page, n):
        """ Return a list of all the spaces that are larger than n times the average line space"""
        space_avg = page.avg_line_spacing()
        section_break_spaces = []
        next_break = True
        for space in page.line_spaces:
            if next_break:
                # We need the space to be as wide as the widest space in the preceding area
                widest = space
                next_break = False
            if space.x0 < widest.x0 or space.x1 > widest.x1:
                widest = space
            if space.height > n*space_avg:
                # Generate a BoundingBox that's as wide as needed.
                section_break_spaces.append(BoundingBox([widest.x0,space.y0,widest.x1,space.y1]))
                next_break = True
        return section_break_spaces
    
    def area_boxes(page, breaks):
        """ Generate a list of text areas using the breaks """
        if len(breaks) == 0:
            # If there are no breaks on the page return the page size as an area.
            return [BoundingBox([page.box.x0, page.box.y0, page.box.x1, page.box.y0])]
        first_area = BoundingBox([page.box.x0, page.box.y0, breaks[0].x1, breaks[0].y0])
        last_area = BoundingBox([breaks[-1].x0, breaks[-1].y1, page.box.x1, page.box.y1])
        if len(breaks) == 1:
            # Return currently generated areas if there is only one break
            return [first_area, last_area]
        areas = [first_area]
        for i, brk in enumerate(breaks):
            next_break = i + 1
            if not next_break >= len(breaks):
                areas.append(BoundingBox([brk.x0, brk.y1, breaks[next_break].x1, breaks[next_break].y0]))
        areas.append(last_area)
        return areas
    
    def create_areas(page, area_boxes):
        """ Create a list of areas with lines contained within as their child elements """
        page_areas = []
        # Nicer, but does not work on some outlier cases.
        """
        end_of_iter = -1 # flag 
        lines = iter(page.children)
        areas = iter(area_boxes)
        def add_lines_to_area(area,line):
            #Recursive function to iterate over areas and lines in a single pass
            if area == end_of_iter:
                return
            area_lines = []
            while line != end_of_iter and line.is_inside(area):
                area_lines.append(line)
                line = next(lines, end_of_iter)
            page_areas.append(Area(area, area_lines))
            add_lines_to_area(next(areas, end_of_iter),line)
        add_lines_to_area(next(areas, end_of_iter),next(lines, end_of_iter))
        """
        # This is a bit nastier, but more reliable 
        for area in area_boxes:
            area_lines = []
            for line in page.children:
                if line.box.is_inside(area):
                    area_lines.append(line)
            page_areas.append(Area(area, area_lines))
        
        return Page(page_areas)  

    def label_areas(page):
        """ Attempt to label the areas of text as parts of a page """ 
        first_area = page.children[0]
        last_area = page.children[-1]
        rest_of_page = page.children
        # If the first area of the page is a single line, it's likely the header. 
        if first_area.is_single_line():
            first_area.label = 'HEADER'
            rest_of_page = rest_of_page[1:]
        if last_area.is_single_line():
            last_area.label = 'FOOTER'
            rest_of_page = rest_of_page[:-1]
        
        for area in rest_of_page:
            if area.is_single_line():
                area.label = 'TITLE'

        # Label the suspected line numbers
        start = page.avg_line_x('START')
        end = page.avg_line_x('END')
        for area in page.children:
            if area.label not in ['HEADER','TITLE']:
                for line in area.children:
                    for word in line.children:
                        if word.box.x1 < start or word.box.x0 > end:
                            word.label = 'LINE_NO'
        for area in page.children:
            area_count = collections.Counter()
            for line in area.children:
                area_count.update([word.label for word in line.children])
            print(area_count)
            print(area.avg_line_height)
        return page


    
    new_page = merge_parallel_lines(page)
    return label_areas(create_areas(new_page, area_boxes(new_page, section_break_spaces(new_page, 2))))

COLOUR = {
'HEADER': '#F7977A', #Pastel Red  
#'': '#F9AD81', #Pastel Red Orange   
'TITLE': '#FDC68A', #Pastel Yellow Orange
'LINE_NO': '#FFF79A', #Pastel Yellow
'APP_CRIT': '#C4DF9B', #Pastel Pea Green
#'': '#A2D39C', #Pastel Yellow Green
'FOOTER': '#82CA9D', #Pastel Green
#'': '#7BCDC8', #Pastel Green Cyan
'': '#6ECFF6', #Pastel Cyan
#'': '#7EA7D8', #Pastel Cyan Blue
'LATIN': '#8493CA', #Pastel Blue
#'': '#8882BE', #Pastel Blue Violet
#'': '#A187BE', #Pastel Violet
#'': '#BC8DBF', #Pastel Violet Magenta
'GREEK': '#F49AC2', #Pastel Magenta
#'': '#F6989D' #Pastel Magenta Red
}

def produce_svg_file(page, original_file_path):
    """ Create a SVG visualisation of the contents of a hOCR file from the 'Tree' representation """
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
 
    page = reparse_tree(page)
    for area in page.children:
        svg_drawing.add(svg_drawing.rect((area.box.x0, area.box.y0), (area.width, area.height), fill=COLOUR[area.label]))
        for line in area.children:
            #svg_drawing.add(svg_drawing.rect((line.box.x0, line.box.y0), (line.width, line.height), fill='#FF3399'))
            for word in line.children:
                svg_drawing.add(svg_drawing.rect((word.box.x0, word.box.y0), (word.width, word.height), fill=COLOUR[word.label]))
    
    #colours = {'Greek': 'red', 'Latin': 'blue', 'Number': 'green'}
    

    #svg_drawing.add(svg_drawing.line((start, page.box.y0), (start, page.box.y1), stroke='black', stroke_width=10)) 
    #svg_drawing.add(svg_drawing.line((end, page.box.y0), (end, page.box.y1), stroke='black', stroke_width=10)) 

    svg_drawing.save()




def parse(text):
    text_soup = BS(open(text).read())
    text_tree = generate_tree(text_soup)

    produce_svg_file(text_tree, text)
    #reparse_tree(text_tree)
    

