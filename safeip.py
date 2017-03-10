#!/usr/bin/python

import socket
import struct
import ctypes
 
 
def ip2int(ip):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip(ip):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))

def to_signed(x):
    return ctypes.c_int32(x).value

def read_safe_ip():
    res = {}
    for line in open("safeip.txt").readlines():
        ipval = int(line.strip())
        res[ipval] = 1
    return res

def is_safe_ip(ip, safe_ips):
    ip_value = to_signed(ip2int(ip))
    if ip_value in safe_ips:
        return True
    return False

def test():
    safe_ips = read_safe_ip()
    print is_safe_ip('222.161.205.144', safe_ips)


test()

