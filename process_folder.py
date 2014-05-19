import os
import sys
from bs4 import BeautifulSoup as BS
from pyhOCR.parse import hOCR_file_to_page
from pyhOCR.analytics import generate_page_stats
from pyhOCR.objects import Text
import re
from PIL import Image
from scipy.cluster import vq
import numpy as np

directory = sys.argv[1]

def create_initial_text(source_dir):
    """ Takes a directory path and returns a Text object """
    num = re.compile('\d\d\d\d')
    for root, dirs, files in os.walk(source_dir):
        pages = []
        for f in files:
            # Create a page object from the file
            page = hOCR_file_to_page(root + f)
            # Find the page number in the file name
            page.number = int(num.search(f).group())
            pages.append(page)
        # Sort the pages into the correct order 
        sorted_pages = sorted(pages, key=lambda p: p.number)
        text = Text(sorted_pages) 
        return text
        
def normalise_vectors(vector_list):
    """ Takes a list of vectors and normalises all values 
        in those vectors between 0 and 1 """
    for i in range(0, len(vector_list[0])):
        max_value = max([vector[i] for vector in vector_list])
        for vector in vector_list:
            vector[i] = float(vector[i]) / max_value
    return vector_list

def text_statistics(text):
    """ Generates a list of page statistics vectors for a text """
    page_stats = []
    for page in text.pages:
        # Taking only the value from the value, label tuples. 
        page_stats.append(list(stat[1] for stat in generate_page_stats(page)))
    return page_stats

def cluster_pages(vector_spaces, no_of_clusters=5):
    """ Use k-means clustering  """
    scaled_vectors = vq.whiten(np.array(vector_spaces))
    centroids, labels = vq.kmeans2(scaled_vectors, no_of_clusters, minit='points')
    return labels

def page_centroids(vector_spaces, no_of_clusters=5):
    """ Use k-means clustering  """
    scaled_vectors = vq.whiten(np.array(vector_spaces))
    codebook, distortion = vq.kmeans(scaled_vectors, 5)
    return codebook

def relabel_types(labels):
    """ Modifies labels to ascend in order of appearance """
    mapping_dict = dict()
    i = 1
    for label in labels:
        if not mapping_dict.get(label):
            mapping_dict[label] = i
            i += 1
    return list([mapping_dict[label] for label in labels ])



text = create_initial_text(directory)
numbers = [page.number for page in text.pages]
for n, t in zip(numbers, relabel_types(cluster_pages(normalise_vectors(text_statistics(text))))):
    print(n, t )
