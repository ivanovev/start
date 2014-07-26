#!/usr/bin/env python3

import tkinter as tk
import tkinter.ttk as ttk

from collections import OrderedDict as OD
from math import ceil

from .control import Control
from .tooltip import ToolTip

import sys, pdb

class Monitor(Control):
    def __init__(self, data=None, dev=None):
        Control.__init__(self, data=data, dev=dev)

    def add_menu_dt(self):
        self.dt = tk.StringVar(value=15)
        self.menu = tk.Menu(self.root, tearoff=0)
        for i in [1, 2, 3, 5, 10, 15, 30, 60, 120]:
            self.menu.add_radiobutton(label='%ds'%i, variable=self.dt, value='%d'%i, command=lambda: self.mntr_io_start(self.io.start))
        self.root.bind("<ButtonRelease-3>", self.menu_cb)

    def init_layout(self):
        self.mode = 0
        self.name = self.data.dev['name']

        style = ttk.Style()
        style.configure('TButton', relief=tk.FLAT)
        #self.frame.configure(style='TFrame')
        #self.frame.configure(borderwidth=2, relief=tk.SUNKEN, style='TFrame')
        self.frame.configure(borderwidth=2, relief=tk.RAISED, style='TFrame')
        #print(style.theme_names())
        #style.theme_use('clam')
        #style.configure('TFrame', foreground="black", background="blue")
        #style.configure('TLabel', foreground="white", background="blue")

        self.f0 = tk.Frame(self.frame)
        self.f0.pack(fill=tk.X, expand=0)
        self.data.select(0)
        self.init_frame(self.f0, self.data.cmds, 0)
        self.data.cmds.f.pack(side=tk.RIGHT, fill=tk.BOTH, expand=0, padx=5)

        if len(self.data) > 1:
            for i in range(1, len(self.data)):
                self.data.select(i)
                self.init_frame(self.frame, self.data.cmds)
                self.data.cmds.f.pack(fill=tk.BOTH, expand=1, padx=5)

        width = 350
        #self.root.withdraw()
        self.root.overrideredirect(True)
        self.after_mntr = 0

        self.draw_pb(False)
        self.frame.pack_propagate(False)
        self.update_height()
        self.frame.configure(width=350)
        self.root.state('normal')
        self.root.lift()
        self.root.attributes('-topmost', 1)
        self.center()

        self.root.bind("<ButtonPress-1>", self.start_move_cb)
        self.root.bind("<ButtonRelease-1>", self.stop_move_cb)
        self.root.bind("<B1-Motion>", self.motion_cb)
        self.add_menu_dt()
        self.after_mntr = self.root.after_idle(self.io.start)

    def draw_pb(self, drawpb):
        if drawpb:
            self.label.pack_forget()
            self.pb.pack(side=tk.LEFT, fill=tk.X, expand=1, padx=5)
            self.pb['value'] = 0
        else:
            self.pb.pack_forget()
            self.label.pack(side=tk.LEFT, fill=tk.X, expand=1, padx=5)

    def get_h0(self):
        return self.close.winfo_height() - 2

    def update_height(self):
        self.root.update_idletasks()
        h0 = self.close.winfo_reqheight()
        h = h0
        if h < 16: h = 16
        if self.mode > 0:
            for i in range(1, len(self.data)):
                cmds = self.data[i]
                columns = cmds.columns if hasattr(cmds, 'columns') else 2
                h1 = h*(ceil(len(cmds)/columns))
                h = h + h1
        h = h + 4
        self.frame.configure(height=h)

    def mntr_cmdw(self, f1, k, cmds):
        v = cmds[k]
        send = v.send
        v.send = None
        if v.wdgt == 'entry':
            v.state = 'readonly'
        l, w = self.make_cmdw(f1, k, cmds)
        v.send = send
        if v.wdgt != 'alarm' and not v.width:
            w.configure(width=7)
        return l,w

    def init_frame(self, parent, cmds, n=1):
        f1 = ttk.Frame(parent)
        cn = cmds.columns if hasattr(cmds, 'columns') else 2 
        if n == 0:
            self.close = ttk.Button(self.f0, width=2, text='X', command=self.root.destroy)
            ToolTip(self.close, msg='Exit', follow=True, delay=0)
            self.close.pack(side='right')
            if len(self.data) > 1:
                self.expand = ttk.Button(self.f0, width=2, text='M', command=self.expand)
                ToolTip(self.expand, msg='Min/Max', follow=True, delay=0)
                self.expand.pack(side='right')
            #self.root.update_idletasks()
        else:
            for i in range(0, 2*cn):
                f1.columnconfigure(i, weight=1)

        j = 0
        for k,v in cmds.items():
            l, w = self.mntr_cmdw(f1, k, cmds)
            if n == 0:
                if l != None:
                    l.pack(side='left')
                if w != None:
                    w.pack(side='left', padx=3)#, fill=tk.Y)
                    v['w'] = w
            else:
                c = 2*(j % cn)
                r = int(j / cn)
                if c == 0:
                    f1.rowconfigure(r, weight=1, pad=2)
                if l:
                    l.configure(anchor=tk.CENTER)
                    l.grid(column=c, row=r, sticky=tk.NSEW)
                if w:
                    if not v.width:
                        w.configure(width=5)
                    w.grid(column=c+1, row=r, pady=2, sticky=tk.NSEW)
                j = j + 1

        if n == 0:
            self.label = ttk.Label(self.f0, text=self.name)
            ToolTip(self.label, msg=self.name, follow=True, delay=0)
            self.label.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=5)
            self.pb = ttk.Progressbar(self.f0, orient=tk.HORIZONTAL, maximum=10)
        cmds.f = f1
        return f1

    def menu_cb(self, evt):
        self.menu.tk_popup(evt.x_root, evt.y_root)

    def start_move_cb(self, evt):
        self.x = evt.x
        self.y = evt.y

    def stop_move_cb(self, evt):
        self.x = None
        self.y = None

    def motion_cb(self, evt):
        deltax = evt.x - self.x
        deltay = evt.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry("+%s+%s" % (x, y))

    def set_err_mode(self, *args):
        self.io.cur += len(self.data)
        for p in self.data:
            for k,v in p.items():
                if v.t:
                    v.t.set('')

    def expand(self):
        with self.qo.mutex:
            self.qo.queue.clear()
        self.mode = self.mode + 1
        if self.mode >= len(self.data):
            self.mode = 0
        if self.mode:
            self.data[self.mode].f.pack(fill=tk.X, expand=1, padx=5)
        else:
            for i in range(1, len(self.data)):
                self.data[i].f.pack_forget()
        cmds0 = self.data[0]
        if self.mode <= 1:
            for k, v in cmds0.items():
                if 'pack_forget' in v and 'w' in v:
                    if v['pack_forget']:
                        if self.mode:
                            v.w.pack_forget()
                        else:
                            v.w.pack(side='left', padx=3)
        self.update_height()
        self.root.update_idletasks()
        self.mntr_io_start(lambda: self.io.start(self.mode))

    def init_io(self):
        del self.io[:]
        for i in range(0, len(self.data)):
            self.io.add(lambda i=i: self.mntr_cb1(i), self.mntr_cb2, self.mntr_cb3, self.cmdio_thread)

    def mntr_io_start(self, io_start):
        if self.after_mntr:
            self.root.after_cancel(self.after_mntr)
        self.after_mntr = self.root.after_idle(lambda: io_start())

    def mntr_cb1(self, p=0):
        self.read = True
        if p > self.mode:
            return False
        if hasattr(self, 'after_upd'):
            return False
        self.root.update_idletasks()
        with self.qo.mutex:
            self.qo.queue.clear()
        if self.after_mntr:
            self.root.after_cancel(self.after_mntr)
            self.after_mntr = None
        if self.qo.qsize() == 0:
            if p == None:
                for i in range(0, len(self.mode) + 1):
                    self.data.select(i)
                    self.data.do_cmds(self.qo, True)
            else:
                self.data.select(p)
                self.data.do_cmds(self.qo, True)
        if hasattr(self, 'pb'):
            self.pb['maximum'] = self.qo.qsize()
            self.draw_pb(True)
        return True

    def mntr_cb2(self):
        line = self.qi.get_nowait()
        #print(line)
        self.ctrl_cb2(line)
        if line.find('step') == 0:
            return True
        cmd, val = line.split(' ', 1)
        if not val:
            self.set_err_mode()
            return False
        return True

    def mntr_cb3(self, *args):
        if hasattr(self, 'pb'):
            self.draw_pb(False)
        if self.io.cur >= self.mode:
            self.after_mntr = self.root.after(int(self.dt.get())*1000, lambda: self.io.start(0))
            return False
        return True

