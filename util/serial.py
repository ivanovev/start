#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, serial, sys, pdb

def to_bytes(s):
    if s and type(s) == str:
        if s.find('0x') == 0:
            ss = s.split('_')
            s = bytes()
            for i in ss:
                i = i.replace('0x', '')
                s += bytes([int(i, 16)])
    if s and type(s) == str:
        s = s.encode('ascii')
    return s

def print_dbg(s):
    if not query_serial.verbose:
        return
    if s:
        s = to_bytes(s)
        print(s)
        print('_'.join(['0x%02X' % i for i in s]))
    else:
        print('empty_str')

def query_serial(port='COM1', bps='9600', nbits='8', parity='N', stopb='1', s='', endstr='', read=True, dtr=None, rts=None, readlen=None):
    """
    Функция посылает в последовательный порт %port% строку s и возвращает результат
    @param port - последовательный порт из списка возвращённого функцией %get_serials%
    @param bps - 1200, 9600 и т.п.
    @param nbits - как правило 8
    @param parity - N, E
    @param stopb - 1 или 2
    @param s - строка, которую надо отправить
    @param endstr - читать из порта пока не придёт %endstr%, если не пришло - то до таймаута
    @param read - 1 или 0, читать или не читать
    @param dtr - 1 или 0 или пустая строка
    @param rts - 1 или 0 или пустая строка
    @return строка из устройства или пустая строка
    """
    print_dbg(s)
    print_dbg(endstr)
    try:
        if port[:3] != 'COM':
            if port.find('/dev/') == -1:
                port = '/dev/' + port
        bps = int(bps)
        nbits = int(nbits)
        stopb = int(stopb)
        read = int(read)
        if type(dtr) == str:
            dtr = int(dtr)
        if type(rts) == str:
            rts = int(rts)
    except:
        return ''
    try:
        ser = serial.Serial(port, bps, nbits, parity, stopb, timeout=query_serial.timeout)
    except:
        print(sys.exc_info()[1])
        return ''
    if dtr != None: ser.setDTR(dtr)
    if rts != None: ser.setRTS(rts)
    if s and type(s) == str:
        ser.write(s.encode('ascii'))
    elif s and type(s) == bytes:
        ser.write(s)
    #ser.sendBreak()
    res = '' if type(s) == str else b''
    if read:
        while True:
            ch = ser.read()
            if len(ch) == 0:
                break
            if type(s) == str:
                res += chr(ch[0])
                res = res.replace(s, '')
            elif type(s) == bytes:
                res += ch
            if endstr:
                if res.find(endstr, 2) != -1:
                    break
            if readlen:
                if len(res) == readlen:
                    break
    else:
        if os.name == 'posix':
            ser.sendBreak()
    ser.close()
    print_dbg(res)
    return res
query_serial.timeout = 2
query_serial.verbose = 0

def get_serials():
    """
    Функция возвращает список последовательных портов, одной строкой, через пробел
    пример для windows: COM1 COM2 COM3 ...
    для GNU/*nix: ttyS* ttyMI* ttyUSB*
    """
    res = []
    for i in ['/dev/ttyS', '/dev/ttyMI', '/dev/ttyUSB', '/dev/ttyr', 'COM']:
        j = 0
        while True:
            try:
                p = '%s%d' % (i, j)
                j += 1
                ser = open(p)
                ser.close()
                if p[:5] == '/dev/': p = p[5:]
                res.append(p)
            except:
                if j >= 20:
                    break
                pass
    return ' '.join(res)

def serial_cmd(port='COM1', bps='9600', nbits='8', parity='N', stopb='1', s='', endstr=''):
    rethex = (s.find('0x') == 0)
    s = to_bytes(s)
    endstr = to_bytes(endstr)
    ret = query_serial(port, bps, nbits, parity, stopb, s, endstr)
    if type(ret) == bytes:
        if rethex:
            ret = '_'.join(['0x%02X' % i for i in ret])
        else:
            ret.decode('ascii')
    ret1 = ''
    for i in range(0, len(ret)):
        if ret[i].isprintable():
            ret1 += ret[i]
    return ret1

def serial_timeout(timeout=''):
    if timeout:
        query_serial.timeout = int(timeout)
    return '%d' % query_serial.timeout

def serial_verbose(verbose=''):
    if verbose:
        query_serial.verbose = 1 if int(verbose) else 0
    return '%d' % query_serial.verbose

def serial_list():
    return get_serials()

def serial_tostr(s):
    ret = ''
    if s.find('0x') == 0:
        ss = s.split('_')
        for i in ss:
            i = i.replace('0x', '')
            ch = chr(int(i, 16))
            if ch.isprintable():
                ret += ch
    return ret

if __name__ == '__main__':
    print(get_serials())

