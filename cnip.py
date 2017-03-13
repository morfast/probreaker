#!/bin/python
#coding: utf-8
import socket
import struct
 
from cn_net import *
 
 
def ip2int( ip ):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip( ip ):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))
 
def iscn( ip ):
    '''检查的方法：
    1. 把ip地址的第一个段拿出来,如果不在offset中，则说明不是cn的地址
    2. 先把ip地址的第一个段拿出来，用于快速定位到iplist的开始位置，减少循环的次数
    3. 从开始位置，到结束位置查找，如果在里面，则是cn的ip '''
    int_ip = ip2int( ip )
    head = ip.split(".")[0]
 
    if head not in offset:
        return False
 
    for i in range(offset[head][0],offset[head][1]+1):
        if int_ip >= iplist[i][0] and int_ip <= iplist[i][1]:
            return True
    return False
 
