#!/usr/bin/env python

from telnetlib import Telnet

import os, re, sys, subprocess
import pdb

'''
import socket

# httplib boost 
realsocket=socket.socket 
def socketwrap(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0): 
   sockobj=realsocket(family, type, proto) 
   sockobj.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) 
   return sockobj 
socket.socket=socketwrap 
'''

def ping(ip, retries = -1):
    ret = 0
    if os.name == 'posix':
        if retries == -1: retries = 1
        ret = subprocess.call("fping -c1 -t200 %s" % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if os.name == 'nt':
        if retries == -1: retries = 0
        ret = subprocess.call("ping -n 1 -w 200 %s" % ip, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = True if ret == 0 else False
    if ret:
        return ret
    if retries > 0:
        return ping(ip, retries - 1)
    return ret

# Обратиться по протоколу telnet к устройству %ip_addr% и выполнить команду %cmd%
# @param ip_addr - ip-адрес устройства
# @param cmd - команда
# @return результат выполнения команды cmd
def telnet(ip_addr, cmd, *args):
    if len(args):
        cmd += ' ' + ' '.join(args)
    if not ping(ip_addr):
        print('Failed to ping %s' % ip_addr)
        return
    try:
        tn = Telnet(ip_addr)
        tn.read_until(b'#> ', 2)
        cmd += '\n'
        tn.write(cmd.encode('ascii'))
        s = tn.read_until(b'#> ', 2)
        tn.write(b'exit\n')
        tn.close()

        def splitstr(s, b):
            r = re.compile(b)
            ss = r.split(s)
            ss = list(filter(lambda x: len(x), ss))
            return ss
        s = s.decode('ascii')
        ss = splitstr(s, '[\[\] \t\n\r:]+')
        ss0 = ss[0]
        if ss0 in ['0', '1']:
            ss = splitstr(s, '[\t\n\r]+')
            ss1 = ss[0]
            ss1 = ss1.replace('[%s]' % ss0, '')
            ss1 = ss1.strip()
            return ss1
        ss = s.split('\n')
        print('Failed to parse', ss)
        return
    except:
        print('telnet error')
        #print(sys.exc_info())
        return

# Получить имя устройства по адресу %ip_addr% (префикс #xxx>)
# @param ip_addr - ip-адрес устройства
# @return имя устройства
def name(ip_addr):
    return telnet(ip_addr, 'name')

if __name__ == '__main__':
    print(telnet('192.168.0.1', 'name'))
