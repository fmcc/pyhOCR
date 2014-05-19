import sys
import csv
from scipy.cluster import vq
import numpy as np

from sklearn import *

file_name = sys.argv[1]

with open(file_name,'r') as csv_in:
    csv_iter = csv.reader(csv_in, delimiter=',')
    rows = [[float(item) for item in row][1:] for row in csv_iter ]

scaled_vectors = vq.whiten(np.array(rows))
centroids, labels = vq.kmeans2(scaled_vectors, 7)

labels = []
for page in rows:
    labels.append(clusterer.predict(page))

page_no = []
page_type = []
for i, label in enumerate(labels, start=1):
    print(str(i) + ',' + str(label[0]))
    page_no.append(i)
    page_type.append(label)
