
import asyncio, queue
from collections import OrderedDict as OD
from datetime import datetime
from time import sleep
from .data import Obj
from .columns import *

@asyncio.coroutine
def async(it, *args):
    return (yield from asyncio.get_event_loop().run_in_executor(None, it, *args))

def time_dec(f):
    def tmp(*args, **kwargs):
        t1 = datetime.now()
        ret = f(*args, **kwargs)
        t2 = datetime.now()
        dt = t2 - t1
        dt = dt.seconds + float(dt.microseconds)/10e6
        print('duration: %.3f' % dt)
        return ret
    return tmp

class MyAIO(list):
    def __init__(self, wnd=None):
        self.qi = queue.Queue()
        self.qo = queue.Queue()
        self.wnd = wnd
        self.na = []
        self.read = True

    def add(self, cb1, cb2, cb3, io_cb):
        self.append((cb1, cb2, cb3, io_cb))

    def get_ip_addr(self, obj):
        if type(obj) == Obj:
            dev = getattr(obj, 'dev')
            if dev:
                if c_ip_addr in dev:
                    return dev[c_ip_addr]

    @asyncio.coroutine
    def start(self, index=0, do_cb1=True):
        self.na = []
        cb1, cb2, cb3, io_cb = self[index]
        if not cb1() if do_cb1 else False:
            return
        t1 = datetime.now()
        if self.wnd.visible() if self.wnd else False:
            self.wnd.set_cursor('watch')
            if hasattr(self.wnd, 'pb'):
                self.wnd.pb['maximum'] = self.qo.qsize()
                self.wnd.pb['value'] = 0
        while True:
            try:
                obj = self.qo.get(True, .1)
            except queue.Empty:
                break
            ip_addr = self.get_ip_addr(obj)
            if ip_addr in self.na:
                continue
            val = yield from async(io_cb, obj)
            if not val and ip_addr:
                self.na.append(ip_addr)
            if self.wnd.visible() if self.wnd else False:
                if hasattr(self.wnd, 'pb'):
                    self.wnd.pb['value'] = self.wnd.pb['value'] + 1
            if not cb2(obj, val):
                break
        if self.wnd.visible() if self.wnd else False:
            self.wnd.set_cursor('')
        t2 = datetime.now()
        dt = t2 - t1
        dt = dt.seconds + float(dt.microseconds)/10e6
        print('duration: %.3f' % dt)
        val = cb3()
        index += 1
        if self.wnd.visible() if self.wnd else False:
            if val and index < len(self):
                self.wnd.root.after_idle(lambda: asyncio.async(self.start(index)))
        if self.wnd.visible() if self.wnd else False:
            if hasattr(self.wnd, 'pb'):
                self.wnd.pb['value'] = 0

