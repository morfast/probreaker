#!/usr/bin/python -u

import scipy.cluster
import sys
import math
import multiprocessing
import argparse
from scipy.cluster.vq import vq,kmeans,whiten

def count_elem(lst):
    res = {}
    for elem in lst:
        if elem in res.keys():
            res[elem] += 1
        else:
            res[elem] = 1
    return res

def do_clustering(data):
    
    # hierarchical clustering
    dist_matrix = scipy.cluster.hierarchy.distance.pdist(data, 'euclidean')
    Z = scipy.cluster.hierarchy.linkage(dist_matrix, method='average')
    cluster = scipy.cluster.hierarchy.fcluster(Z, t=1.0)
    k = max(cluster)
    #print "result of hierarchy clustering:", k, "clusters"
    
    #print data
    #print wdata
    #wdata = whiten(data)
    wdata = data
    cr = scipy.cluster.vq.kmeans(wdata, k)[0]
    # cr is the centroid of the clusters
    #print "cr"
    #print cr
    #print cr[0]

    # assign each point to the nearest cluster
    label = vq(wdata, cr)
    #print "label"
    #print label[0]

    # count the ratio of each cluster
    ct = count_elem(list(label[0]))
    #print "ct"
    #print ct

    res = []
    for key in ct:
        res.append([(cr[key][0], cr[key][1]), ct[key]/float(len(data))*100])

    return sorted(res, key=lambda(x):x[1], reverse=True)

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def close_enough(p1, p2):
    distance_threshold = 15
    if p1[0] == 0.0 and p2[0] != 0.0  or p1[0] != 0.0 and p2[0] == 0.0:
        return False
    if p1[1] == 0.0 and p2[1] != 0.0  or p1[1] != 0.0 and p2[1] == 0.0:
        return False
    if distance(p1, p2) <= distance_threshold:
        return True
    else:
        return False
    

def is_similar_cluster(clstr1, clstr2):
    ratio_threshold = 50
    total_match_threshold = 2

    total_ratio1 = 0
    total_ratio2 = 0
    total_match = 0
    match_index1 = set()
    match_index2 = set()
    for index1,c1 in enumerate(clstr1[:10]):
        centroid1, ratio1 = c1
        for index2,c2 in enumerate(clstr2[:10]):
            centroid2, ratio2 = c2
            if close_enough(centroid1, centroid2):
                match_index1.add(index1)
                match_index2.add(index2)
                total_match += 1
                break

    for i in match_index1:
        total_ratio1 += clstr1[i][1]
    for i in match_index2:
        total_ratio2 += clstr2[i][1]

    if total_ratio1 >= ratio_threshold and total_ratio2 >= ratio_threshold and total_match >= total_match_threshold:
        print " ============ similar clusters found ================"
        print_cluster(clstr1)
        print " ===================================================="
        print_cluster(clstr2)
        print " ===================================================="
        print match_index1
        print match_index2
        print " ===================================================="
        return total_match, total_ratio1, total_ratio2
    else:
        return 0, 0, 0

