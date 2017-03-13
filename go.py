#!/usr/bin/python -u

from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import SGDClassifier
from sklearn import tree
from sklearn import svm
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.model_selection import train_test_split
from sklearn.cluster import AffinityPropagation

import sys
import numpy
import math
import argparse
import scipy.signal
import time 
import cPickle

import safeip

def basic_float_numerical_info(array):
    minval = min(array)
    maxval = max(array)
    midval = numpy.median(array)
    meanval = numpy.mean(array)
    stdval = numpy.std(array)

    return minval, maxval, midval, meanval, stdval

def modal_value(array, n):
    d = {}
    for v in array:
        if v in d.keys():
            d[v] += 1
        else:
            d[v] = 1
    sorted_pairs = sorted(d.iteritems(), key=lambda d:d[1], reverse = True)
    res = [x[0] for x in sorted_pairs[0:n]]
    times = [x[1] for x in sorted_pairs[0:n]]
    ratio = [x/float(len(array)) for x in times]
    length = len(res)
    if length < n:
        res += [0] * (n - length)
        ratio += [0] * (n - length)
    return res, ratio

def basic_int_info(array):
    pass


def add_feature_dict(d, key):
    if key in d:
        d[key] += 1

def get_dict_values(d):
    sorted_pairs = sorted(d.iteritems(), key=lambda d:d[0])
    return [x[1] for x in sorted_pairs]

def get_ratio(total_num, array):
    return [x/float(total_num) for x in array]

def get_timeinfo(atime_list):
    freq, power = scipy.signal.periodogram([float(x) for x in atime_list])
    max_freqs = sorted(zip(freq, power), key = lambda x:x[1], reverse=True)[:3]
    return [x[0] for x in max_freqs] + [x[1] for x in max_freqs]

def convert_time(timestr):
    # 2016-10-11 09:11:13 -> 9*60+11
    x = timestr.split()[1].split(':')
    h = x[0]
    m = x[1]
    return int(h) * 60 + int(m)

    

class Frigate_Data():
    def __init__(self):
        # original frigate log infomation
        # access time
        self._atime_ = [0] * 1440
        # destination IP
        self._dip_ = ""
        # source IP
        self._sip_ = set()
        # destination port
        self._dports_ = []
        # up traffic
        self._ups_ = []
        # down traffic
        self._downs_ = []
        # link duration
        self._durations_ = []
        # time of the handshake
        self._rtts_ = []
        # trasport layer protocols
        self._transport_protos_ = {'TCP':0, 'UDP':0, 'ICMP':0, }
        # application layer protocols
        self._app_protos_ = {'HTTP':0, }
        # http URLs
        self._n_url_ = 0
        # errno codes
        self._errnos_ = {0:0, 104:0, 62:0, 110:0, 111:0}

        # features
        self._features_ = []

        # type
        self._type_ = -1


    def print_original_logs(self):
        print " ====================== "
        print "destination IP: %s" % (self._dip_)
        print "destination port:", self._dports_
        print "up_traffic", self._ups_
        print "down_traffic", self._downs_
        print "duration", self._durations_
        print "rtt", self._rtts_
        print "trans_proto", self._transport_protos_
        print "application protocols", self._app_protos_
        print "url", self._n_url_
        print "errno", self._errnos_
        print " ====================== "

    def cal_features(self):
        mintime, maxtime = self._timespan_
        timespan = maxtime - mintime
        if timespan < 1:
            timespan = 1
        n = len(self._ups_)
        # dport
        modval, ratio = modal_value(self._dports_, 3)
        self._features_ += modval
        self._features_ += ratio
        # ups
        self._features_ += basic_float_numerical_info(self._ups_)
        modval, ratio = modal_value(self._ups_, 2)
        self._features_ += modval
        self._features_ += ratio
        # downs
        self._features_ += basic_float_numerical_info(self._downs_)
        modval, ratio = modal_value(self._downs_, 2)
        self._features_ += modval
        self._features_ += ratio
        # duration
        self._features_ += basic_float_numerical_info(self._durations_)
        # rtt
        self._features_ += basic_float_numerical_info(self._rtts_)
        # protocols
        self._features_ += get_ratio(n, get_dict_values(self._transport_protos_))
        self._features_ += get_ratio(n, get_dict_values(self._app_protos_))
        # error code
        self._features_ += get_ratio(n, get_dict_values(self._errnos_))
        # pv uv
        self._features_.append(n/float(timespan))
        self._features_.append(len(self._sip_)/float(timespan))
        # time info
        self._features_ += get_timeinfo(self._atime_)

    def print_features(self):
        print len(self._features_), self._features_

    def get_features(self):
        return self._features_

class parameters():
    def __init__(self):
        self._train_filenames_ = []
        self._data_filenames_ = []
        self._save_trainset_filename_ = ""
        self._load_trainset_filename_ = ""
        self._save_data_filename_ = ""
        self._load_data_filename_ = ""

        

def read_frigate_log(logfilenames):
    res = {}
    total_lines = 0
    for logfilename in logfilenames:
        print logfilename
        min_time = 9999
        max_time = 0
        for line in open(logfilename):
            spline = line.strip().split("\t")
            # grab features
            atime = spline[1]
            atime_minute = convert_time(atime)
            if atime_minute < min_time:
                min_time = atime_minute
            if atime_minute > max_time:
                max_time = atime_minute
            trans_proto = spline[3]
            dipport = spline[6]
            dip, dport = dipport.split(':')
            sipport = spline[4]
            sip, sport = sipport.split(':')
            up_traffic = spline[7]
            down_traffic = spline[8]
            duration = spline[10]

            handshake_rtt = spline[13]
            app_proto = spline[16]
            http_url = spline[17]

            errro_code = spline[20]

            if dip in res.keys():
                # get the Frigate_Data object
                fdata = res[dip]
            else:
                fdata = Frigate_Data()
                res[dip] = fdata
                fdata._dip_ = dip

            # update the features
            assert(dip == fdata._dip_)
            add_feature_dict(fdata._transport_protos_, trans_proto)
            fdata._atime_[atime_minute] += 1
            fdata._dports_.append(int(dport))
            fdata._sip_.add(sip)
            fdata._ups_.append(float(up_traffic))
            fdata._downs_.append(float(down_traffic))
            fdata._durations_.append(float(duration))
            fdata._rtts_.append(float(handshake_rtt))
            add_feature_dict(fdata._app_protos_, app_proto)
            if http_url != "NULL":
                fdata._n_url_ += 1
            add_feature_dict(fdata._errnos_, int(errro_code))

            total_lines += 1
            if total_lines % 100000 == 0:
                print "%d lines read" % total_lines
        for key in res.keys():
            res[key]._timespan_ = [min_time, max_time]

    return res

def test():
    X = [[1,1,[0]], [2,2,[1]], [1,2,[1]], [11,11,[1]], [12,12,[1]],]
    Y = [0,0,0,1,1]
    
    gnb = GaussianNB()
    f = gnb.fit(X,Y)
    print f.predict([2,3])
    print f.predict([12,13])

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--train", action='store', nargs='*')
    parser.add_argument("-d", "--data", action='store', nargs='*')
    parser.add_argument("-l", "--lt", action='store', nargs='*')
    parser.add_argument("-L", "--st", action='store', nargs='*')
    parser.add_argument("-s", "--ld", action='store', nargs='*')
    parser.add_argument("-S", "--sd", action='store', nargs='*')
    parser.add_argument("-o", "--to", action='store', nargs='*')

    args =  parser.parse_args()

    if not args.train and not args.lt:
        sys.stderr.write("No traning set?\n")
        sys.exit(0)

    if args.train and args.lt:
        sys.stderr.write("double traning set?\n")
        sys.exit(0)

    if not args.data and not args.ld and not args.to:
        sys.stderr.write("No data?\n")
        sys.exit(0)

    if args.data and args.ld:
        sys.stderr.write("double data?\n")
        sys.exit(0)

    return args

def write_feature(fridata, tfile):
    tfile.write("-%d- %s " % (fridata._type_, fridata._dip_))
    tfile.write(" ".join(["%15.2f" % (float(x)) for x in fridata.get_features()]))
    tfile.write("\n")

def test_accuracy(data, target):
    data_train, data_test, target_train, target_test \
              = train_test_split(data, target)
    clf = GaussianNB()
    #clf = MLPClassifier()
    #clf = tree.DecisionTreeClassifier()
    #clf = SGDClassifier()
    #clf = SGDClassifier(loss="hinge", penalty="l2")
    #clf = svm.SVC()
    fit_res = clf.fit(data_train, target_train)
    return fit_res.score(data_test, target_test)

def group_by_cluster(time_label, ip_label, cluster_label):
    n_cluster = max(cluster_label) + 1
    groups = [[] for i in range(n_cluster)]
    for i,cl in enumerate(cluster_label):
        groups[cl].append((ip_label[i], time_label[i]))

    n_times = max(time_label) + 1

    allip = []
    for g in groups:
        tls = [i[1] for i in g]
        if len(set(tls)) >= n_times:
            ips = [i[0] for i in g]
            allip += ips
    resip = set(allip)
    f = open("resultip", "w")
    for ip in resip:
        f.write("%s\n" % ip)
    print "number of res ip", len(resip)

def main():
    if len(sys.argv) == 1:
        sys.exit()
    logfilenames = sys.argv[1:]
    safeip.init_safeip()

    X = []
    time_label = []
    ip_label = []
    safeip_cnt = 0
    for i,filename in enumerate(logfilenames):
        # read training file
        res = read_frigate_log([filename])
        for key in res:
            if safeip.is_safeip(key):
                safeip_cnt += 1
                continue
            #res[key].print_original_logs()
            res[key].cal_features()
            f = res[key].get_features()
            X.append(f)
            time_label.append(i)
            ip_label.append(key)

    print "number of IP:", len(X) + safeip_cnt
    print "number of safe IP:", safeip_cnt
    #print ap.labels_
    t0 = time.clock()
    print "start clustering ..."
    ap = AffinityPropagation()   
    ap.fit(X)   
    t1 = time.clock()
    print "number of IP:", len(ap.labels_) + safeip_cnt
    print "time of clustering: ", t1 - t0
    print "number of cluster:", len(set(ap.labels_))

    group_by_cluster(time_label, ip_label, ap.labels_)



main()

