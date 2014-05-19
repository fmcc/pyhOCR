from bs4 import BeautifulSoup as BS
from .objects import *
from .draw import *
import numpy as np
import itertools
import collections
import os

def hOCR_file_to_page(hocr_page):
    """ Reads a hOCR page into a page object """
    hocr_soup = BS(open(hocr_page).read())
    page = generate_page(hocr_soup)
    return page

def hOCR_open(hocr_page):
    hocr_soup = BS(open(hocr_page).read())
    page = generate_tree(hocr_soup)
    return page
    #detect_columns(text_tree)
    text_tree = reparse_tree(text_tree)
    produce_svg_file(text_tree, text)

def generate_page(text_in):
    return Page(
        [ Line(line, 
            [ Word(word) 
                for word in line.find_all( True, { 'class' : 'ocr_word' } ) 
            ] ) 
            for line in text_in.find_all( True, { 'class' , 'ocr_line' } ) 
        ] )

def detect_page_type(page):
    pass

def detect_columns(page):
    print(len(page.children))
    parallel = set()
    not_parallel = set()
    mid_x_1 = []
    mid_x_2 = []
    for line_one, line_two in itertools.combinations(page.children, 2):
        if line_one.box.vertical_overlap(line_two.box) and not line_one.box.horizontal_overlap(line_two.box):
            line_one.label = 'GREEK'
            line_two.label = 'LATIN'
            parallel.add(line_one)
            parallel.add(line_two)
            
            if line_two.box.x1 < line_one.box.x0:
                line_one, line_two = line_two, line_one
            

            mid_x_1.append(min(line_two.box.x0,line_one.box.x1))
            mid_x_2.append(max(line_two.box.x0,line_one.box.x1))
        else:
            line_one.label = ''
            line_two.label = ''
            not_parallel.add(line_one)
            not_parallel.add(line_two)
    print(len(parallel), len(not_parallel))
    line_lengths = [line.box.width for line in page.children]
    
    x0 = max(mid_x_1) 
    y0 = min([line.box.y0 for line in page.children]) 
    y1 = max([line.box.y1 for line in page.children]) 
    x1 = min(mid_x_2) 
    page.vertical_gap = ((x0,y0),(x1,y1))
    #print(max(line_lengths))
    #print(sum(line_lengths)/len(line_lengths))

def reparse_tree(page):
    
    def merge_parallel_lines(page):
        """ Merge lines that are parallel in a single column layout to a single """ 
        defunct_lines = []
        for line_one, line_two in itertools.combinations(page.children, 2):
            if line_one.box.vertical_overlap(line_two.box) and not line_one.box.horizontal_overlap(line_two.box):
                # add the children from one line to another
                line_one.children.extend(line_two.children)
                line_one.recalculate_bounding_box()
                # add second line to those to be removed
                defunct_lines.append(line_two)
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

    def group_by_line_heights(areas):
        """  """
        sorted_areas = sorted(areas, key=lambda a: a.box.y0)
        temp_label = 0
        sorted_areas[0].label = temp_label
        for i, area in enumerate(sorted_areas):
            next_area_index = i + 1
            if not next_area_index >= len(sorted_areas):
                next_area = sorted_areas[next_area_index]
                difference = area.avg_line_height - next_area.avg_line_height
                if difference > 2*area.line_std_dev and difference > 2*next_area.line_std_dev:
                    temp_label += 1
                    next_area.label = temp_label
                else:
                    next_area.label = temp_label

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
        remaining_areas = [area for area in page.children if area.label not in ['HEADER','TITLE']]
        group_by_line_heights(remaining_areas)
        for area in remaining_areas:
            for line in area.children:
                for word in line.children:
                    if word.box.x1 < start or word.box.x0 > end:
                        word.label = 'LINE_NO'

            area_count = collections.Counter()
            for line in area.children:
                area_count.update([word.label for word in line.children])
        return page


    
    new_page = merge_parallel_lines(page)
    return label_areas(create_areas(new_page, area_boxes(new_page, section_break_spaces(new_page, 2))))





