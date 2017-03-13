#!/bin/env python
#coding: utf-8
import socket
import struct
 
def ip2int( ip ):
    return struct.unpack('!L',socket.inet_aton(ip))[0]
 
def int2ip( ip ):
    return socket.inet_ntoa(struct.pack('I',socket.htonl(ip)))
 
if __name__ == '__main__':
    #亚洲区的ip分配记录
    fr = file("ip_apnic")
    #生成的数据文件
    fw = open("cn_net.py",'w')
    o = {}
    fw.write('iplist = [\n')
    #下面三个变量，只要为了效率，定位快一些
    n_cnip = 0
    start_index = 1
    lines = fr.readlines();

    last_first_seg = ""
    for lin in lines:
        #注释
        if lin[0] == '#':
            continue
        #用|分开的格式
        v = lin.split('|')
        #只考虑ipv4
        if v[2] != 'ipv4' :
            continue
        #不是大陆的不用考虑
        if v[1] == '*' :
            continue
        if v[1] != 'CN':
            continue
        #为了效率，取ip地址的第一段作为定位
        h = v[3].split(".")
        first_seg = h[0]
        if first_seg not in o:
            if not last_first_seg:
                o[first_seg] = [0,0]
            else:
                o[last_first_seg] = [start_index-1, n_cnip-1]
                start_index = n_cnip
        last_first_seg = first_seg
          
        #把ip转换成数字
        #cn的开始
        bgn_ip = ip2int( v[3] )
        #cn的结束
        end_ip = bgn_ip + int(v[4]) -1
        fw.write('(%d,%d),\n' % (bgn_ip,end_ip) )
        n_cnip = n_cnip+1
    o[first_seg] = [start_index-1, n_cnip-1]
    fw.write('(0,0)\n')
    fw.write(']\n\n')
 
    #最后在把用于快速定位的字典数据写到数据文件中
    fw.write('offset = ')
    fw.write(str(o))
