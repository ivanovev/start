
import os, pdb
import tkinter as tk
import tkinter.ttk as ttk
import binascii, hashlib
from collections import OrderedDict as OD
from threading import Thread
from .control import Control
from .data import Data
from .socketio import recv_data, send_data
from .callbacks import telnet_io_cb
from .columns import *

class DataIO(Control):
    def __init__(self, data, dev, title='Data IO'):
        Control.__init__(self, data=data, dev=dev, title=title, pady=3)
        self.fileext = 'bin'
        self.filemode = 'rb'
        if hasattr(self, 'pb'):
            self.pb['maximum'] = 100

    def add_tx_cmds(self, data, txmd5):
        data.add_page('TX')
        data.add('ip_addr', label='IP address', wdgt='entry', text=data.dev['ip_addr'])
        data.add('browse', label='File path', wdgt='button', text='Browse', click_cb=self.fileopen_cb)
        data.add('fname', wdgt='entry', columnspan=2)
        data.add('fsz', label='File size', wdgt='entry', state='readonly')
        data.add('fszhex', label='File size (hex)', wdgt='entry', state='readonly')
        if txmd5:
            data.add('md5label', label='MD5 sum')
            data.add('md5', wdgt='entry', state='readonly', columnspan=2)
            data.add('crc32label', label='CRC32 sum')
            data.add('crc32', wdgt='entry', state='readonly', columnspan=2)
        data.add('send', wdgt='button', text='Write', click_cb=self.write_cb)

    def add_rx_cmds(self, data):
        data.add_page('RX')
        data.add('ip_addr', label='IP address', wdgt='entry', text=data.dev['ip_addr'])
        data.add('browse', label='File', wdgt='button', text='Browse', click_cb=self.filesaveas_cb)
        data.add('fname', wdgt='entry', columnspan=2)
        data.add('fsz', label='File size', wdgt='entry', msg='1-1024k, 1-32M', text='1')
        data.add('fszunits', wdgt='combo', state='readonly', value=['k', 'M'], text='M')
        data.add('recv', wdgt='button', text='Read', click_cb=self.read_cb)

    def fileopen(self, fname):
        self.data.set_value('fname', fname)
        return self.update_fsz_md5(fname)

    def filesave(self, fname):
        self.data.set_value('fname', fname)

    def read_file(self, fname=None):
        f = open(fname, self.filemode)
        data = f.read()
        f.close()
        return data

    def get_data(self):
        fname = self.data.get_value('fname')
        if fname:
            return self.read_file(fname)

    def update_fsz_md5(self, fname=None):
        try:
            fsz = 0
            if fname:
                fsz = os.path.getsize(fname)
            data = self.get_data()
            if not fsz:
                fsz = len(data)
            if data:
                if type(data) == str:
                    data = data.encode('ascii')
                if 'md5' in self.data:
                    m = hashlib.md5()
                    m.update(data)
                    self.data.set_value('md5', m.hexdigest())
                if 'crc32' in self.data:
                    crc = binascii.crc32(data)
                    self.data.set_value('crc32', '0x%08X' % crc)
                self.data.set_value('fsz', '%d' % fsz)
                self.data.set_value('fszhex', '0x%.6X' % fsz)
                return True
        except:
            return False

    def dataio_thread(self):
        ip_addr = self.data.get_value('ip_addr')
        fname = self.data.get_value('fname')
        self.fsz = self.dataio_get_fsz()
        port = 8888
        if self.read:
            self.io_func = recv_data
            if dev[c_type] == 'SAM7X':
                port = 8889
        else:
            self.io_func = send_data
        if not self.fsz:
            return
        self.io_func(ip_addr, port, fname, self.fsz)
        self.io_func.t.join()

    def dataio_get_fsz(self):
        fsz = self.data.get_value('fsz')
        fsz = int(fsz)
        if self.read:
            fszunits = self.data.get_value('fszunits')
            if fszunits == 'k':
                if fsz >= 1024:
                    fsz = 1024
                fsz *= 1024
            if fszunits == 'M':
                if fsz >= 32:
                    fsz = 32
                fsz *= 1024*1024
        return fsz

    def update_progress(self):
        if hasattr(self, 'io_func'):
            if hasattr(self.io_func, 'progress'):
                self.pb['value'] = self.io_func.progress

    def efc_cb1(self, evt='fw'):
        dev = self.data.dev
        dev['ip_addr'] = self.data.get_value('ip_addr')
        if self.read:
            if dev[c_type] == 'SAM7X':
                return self.tmp_cb1(telnet_io_cb(dev, 'efc tx'), key='fsz')
            elif dev[c_type].find('STM32') == 0:
                return self.tmp_cb1(telnet_io_cb(dev, 'flash tx1'), key='fsz')
        else:
            if self.data.find_v('fname'):
                fname = self.data.get_value('fname')
                if not self.fileopen(fname) if fname else False:
                    print('fileopen false', fname)
                    return False
            fsz = self.data.get_value('fsz')
            if dev[c_type] == 'SAM7X':
                md5 = self.data.get_value('md5')
                return self.tmp_cb1(telnet_io_cb(dev, 'efc rx %s %s %s' % (fsz, evt, md5)), key='fsz')
            elif dev[c_type].find('STM32') == 0:
                crc = self.data.get_value('crc32')
                return self.tmp_cb1(telnet_io_cb(dev, 'flash rx1 %s %s' % (fsz, evt)), key='fsz')

    def data_cb1(self, read=True):
        self.filemode = 'rb' if read else 'wb'
        self.pb['maximum'] = 100
        return True

    def data_cb2(self):
        self.update_progress()
        return False

