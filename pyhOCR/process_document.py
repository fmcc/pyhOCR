from .parse import *
import sys

hocr_file = sys.argv[1]
svg_file = sys.argv[2]

with open(hocr_file, 'r') as hocr_in:
    parse(hocr_in.read(), svg_file, 
