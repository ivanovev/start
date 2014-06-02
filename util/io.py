
import queue
from collections import OrderedDict as OD
from time import sleep
from threading import Thread
from .server import proxy

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

    def start_thread(self):
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
            self.start_thread()
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

class IO:
    def __init__(self):
        self.qi = queue.Queue()
        self.qo = queue.Queue()
        self.io = MyIO(self)

    def cmdio_thread(self):
        while True:
            try:
                cmd = self.qo.get(True, .3)
            except queue.Empty:
                break
            #print(cmd)
            if cmd.find('sleep') != -1:
                dt = float(cmd.split(' ')[-1])
                sleep(dt)
                self.qi.put('step')
                continue
            cmdid,cmd = cmd.split(' ', 1)
            dev = self.data.get_dev(cmdid)
            k = '.'.join([dev['name'], dev['type']])
            if k in self.io.na:
                continue
            val = proxy.call(dev, cmd)
            if not val:
                self.io.na.append(k)
                val = ''
            s = '%s %s' % (cmdid, val)
            self.qi.put(s)

    def update_wnd(self):
        if not self.io.t.is_alive() and self.qi.qsize() == 0 and self.qo.qsize() == 0:
            if hasattr(self, 'after_upd'):
                delattr(self, 'after_upd')
            self.io.nextio()
            return
        try:
            while 1:
                if not self.io.cb2():
                    break
        except queue.Empty:
            pass
        self.after_upd = self.root.after(200, self.update_wnd)

    def tmp_cb1(self, *args, read=None, key='tmp'):
        if read != None:
            self.read = read
        self.io.ioval.clear()
        if key:
            for c in args:
                self.qo.put(key + ' ' + c)
        if self.qo.qsize() > 0:
            if hasattr(self, 'pb'):
                self.pb['maximum'] = self.qo.qsize()
        else:
            return False
        return True

    def tmp_cb2(self):
        line = self.qi.get_nowait()
        ll = line.split(' ', 1)
        if ll[-1]:
            self.io.ioval[ll[0]] = ll[-1]
        if hasattr(self, 'pb'):
            self.pb['value'] = self.pb['value'] + 1

    def tmp_cb3(self):
        return len(self.io.ioval) > 0

    def cmdio(self, *args, **kwargs):
        self.tmp_cb1(*args, read=False)
        self.io.start(do_cb1=False, **kwargs)
