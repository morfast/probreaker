#!/usr/bin/python

import socket
import struct
import ctypes

import cnip

global Safe_IPs
 
 
def ip2int(ip):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip(ip):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))

def to_signed(x):
    return ctypes.c_int32(x).value

def init_safeip():
    global Safe_IPs
    res = {}
    for line in open("safeip.txt").readlines():
        ipval = int(line.strip())
        res[ipval] = 1
    Safe_IPs = res

def is_safeip(ip):
    global Safe_IPs
    ip_value = to_signed(ip2int(ip))
    if ip_value in Safe_IPs:
        return True
    if not cnip.iscn(ip):
        return True
    return False

def test_safeip():
    init_safeip()
    print is_safeip('222.161.205.144')
    print is_safeip('8.8.8.8')


# test_safeip()

