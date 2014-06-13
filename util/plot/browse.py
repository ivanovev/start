
import tkinter as tk
import tkinter.ttk as ttk

from collections import OrderedDict as OD

from ..control import Control
from .. import CachedDict, Data
from .plotdata import PlotData

import pdb

class Browse(Control):
    def __init__(self, parent, mw, mode='y', startindex=0):
        self.mode = mode
        self.startindex = startindex
        self.kw = OD()
        self.mw = mw
        self.cd = CachedDict()
        Control.__init__(self, parent=parent, title='select ' + mode)
        self.add_buttons_ok_cancel()
        self.center()

    def init_layout(self):
        if self.mode == 'y':
            self.dd = self.mw.get_devices('mntr')
        elif mode == 'x':
            self.dd = self.mw.get_devices('ctrl')
        self.devname = tk.StringVar()
        self.devname.trace_variable('w', self.dev_cb)
        combo = ttk.Combobox(self.frame, state='readonly', textvariable=self.devname)
        combo.pack()
        self.ff = ttk.Frame(self.frame)
        self.ff.pack(fill=tk.BOTH, expand=1)
        kk = list(self.dd.keys())
        combo['values'] = kk
        if len(kk) > 0:
            self.devname.set(kk[0])
            self.dev_cb()

    def dev_cb(self, *args):
        if hasattr(self, 'fa'):
            self.fa.pack_forget()
            delattr(self, 'fa')
        name = self.devname.get()
        dev = self.dd[name]
        fa = self.cd.get(lambda: self.get_dev_frame(dev), dev['name'], dev['type'], 'frame')
        if fa == None:
            return
        self.fa = fa
        self.fa.pack(fill=tk.BOTH, expand=1)

    def get_dev_frame(self, dev):
        self.data = self.cd.get(lambda: self.get_dev_data(dev), dev['name'], dev['type'], 'data')
        frame = self.init_frame(self.ff, self.data[0])
        return frame

    def get_dev_data(self, dev):
        vv = dev['getter'](dev)
        data = PlotData(vv)
        data.merge()
        data.update_label()
        if self.mode == 'y':
            for k,v in data.cmds.items():
                v.wdgt = 'plot'
                v.send = True
        elif self.mode == 'x':
            data.filter_cmds('spin')
            labels = OD([(v['label'], k) for k, v in data.cmds.items()])
            k0 = list(labels.keys())[0]
            data.add_page('xsel', c1)
            data.add('x', wdgt='radio', value=labels, text=k0, send=True)
        return data

    def ok_cb(self):
        name = self.devname.get()
        if name == '':
            return
        dev = self.dd[name]
        cmds = self.data.cmds
        if self.mode == 'y':
            for k,v in cmds.items():
                c = v['l'].get()
                if c == '1':
                    v['cmd'] = k
                    v['dev'] = dev
                    v['text'] = '.'.join([name, v['label']])
                    k = '%s_%d' % (self.mode, self.startindex + len(self.kw))
                    self.kw[k] = v
        elif self.mode == 'x':
            k = self.data.get_value('x')
            self.data.select(0)
            v = self.data.cmds[k]
            v['cmd'] = k
            v['dev'] = dev
            v['text'] = '.'.join([name, v['label']])
            v['t'] = tk.StringVar()
            v['l'] = tk.StringVar(value=1)
            v['send'] = True
            self.kw['x_0'] = v
        self.root.destroy()

