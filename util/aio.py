
from .io import MyIO
import asyncio

class MyAIO(MyIO):
    def __init__(self, wnd, *args):
        MyIO.__init__(self, wnd, *args)

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

