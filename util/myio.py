
import asyncio, queue
from collections import OrderedDict as OD
from datetime import datetime
from time import sleep

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

class MyIO(list):
    def __init__(self, wnd, *args):
        self.cur = 0
        self.wnd = wnd
        self.ioval = OD()
        self.na = []
        if len(args) == 4:
            self.add(args)

    def add(self, cb1, cb2, cb3, thread_func):
        self.append((cb1, cb2, cb3, thread_func))

    def start_io_func(self):
        self.t = Thread(target=self.thread_func)
        self.t.start()

    def start(self, index=0, do_cb1=True):
        if index >= len(self):
            return False
        self.cur = index
        self.cb1, self.cb2, self.cb3, self.thread_func = self[index]
        if not do_cb1:
            if hasattr(self.wnd, 'pb'):
                self.wnd.pb['maximum'] = self.wnd.qo.qsize()
        if self.cb1() if do_cb1 else True:
            if hasattr(self.wnd, 'pb'):
                self.wnd.pb['value'] = 0
            self.na = []
            self.start_io_func()
            self.wnd.root.config(cursor='watch')
            self.wnd.update_wnd()
            return True

    def nextio(self):
        if hasattr(self.wnd, 'pb'):
            self.wnd.pb['value'] = 0
        if not self.cb3():
            self.wnd.root.config(cursor='')
            return
        self.cur = self.cur + 1
        if not self.start(self.cur):
            self.wnd.root.config(cursor='')
            self.cur = 0

class MyAIO(list):
    def __init__(self, wnd=None):
        self.qi = queue.Queue()
        self.qo = queue.Queue()
        self.wnd = wnd
        self.na = []
        self.read = True

    def add(self, cb1, cb2, cb3, io_cb):
        self.append((cb1, cb2, cb3, io_cb))

    @asyncio.coroutine
    def start(self, index=0, do_cb1=True):
        print('start')
        self.na = []
        cb1, cb2, cb3, io_cb = self[index]
        if not cb1() if do_cb1 else False:
            return
        t1 = datetime.now()
        if self.wnd:
            self.wnd.set_cursor('watch')
            if hasattr(self.wnd, 'pb'):
                self.wnd.pb['maximum'] = self.qo.qsize()
                self.wnd.pb['value'] = 0
        while True:
            try:
                obj = self.qo.get(True, .1)
            except queue.Empty:
                break
            val = yield from async(io_cb, obj)
            if self.wnd:
                if hasattr(self.wnd, 'pb'):
                    self.wnd.pb['value'] = self.wnd.pb['value'] + 1
            if not cb2(obj, val):
                break
        if self.wnd:
            self.wnd.set_cursor('')
        t2 = datetime.now()
        dt = t2 - t1
        dt = dt.seconds + float(dt.microseconds)/10e6
        print('duration: %.3f' % dt)
        val = cb3()
        index += 1
        if self.wnd:
            if val and index < len(self):
                self.wnd.root.after_idle(lambda: asyncio.async(self.start(index)))
        if self.wnd:
            if hasattr(self.wnd, 'pb'):
                self.wnd.pb['value'] = 0

