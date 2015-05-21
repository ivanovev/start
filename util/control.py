#!/usr/bin/env python

from collections import OrderedDict as OD

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

from .tooltip import ToolTip
from . import UI, IO

class Control(UI, IO):
    def __init__(self, data=None, dev=None, parent=None, title=None, pady=0, center=False):
        IO.__init__(self)
        if parent == None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(parent)
            self.parent = parent
        self.root.withdraw()
        self.read = True
        self.pady = pady
        if data != None:
            self.data = data
            if dev != None:
                self.data.dev = dev
        if not hasattr(self, 'frame'):
            self.add_frame()
            self.add_fb()
        self.init_layout()
        self.init_menu()
        self.init_io()
        if dev:
            t1 = '%s.%s' % (dev['name'], dev['type'])
            self.name = '%s %s' % (title, t1) if title else t1
        elif title:
            self.name = title
        else:
            self.name = ''
        self.root.title(self.name)
        if center:
            self.center()

    def add_frame(self):
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=1, side=tk.TOP)

    def add_fb(self):
        if not hasattr(self, 'fb'):
            self.fb = tk.Frame(self.root)
            self.fb.pack(fill=tk.X, expand=0, side=tk.BOTTOM)

    def button_cb(self, k):
        btns = self.data.buttons
        cmd = btns[k]
        cmd(self)

    def rbutton_cb(self, k):
        cmds = self.data.cmds
        v1 = '0' if int(cmds[k].l.get()) else '1'
        for k,v in cmds.items():
            if v.l:
                v.l.set(v1)

    def key_to_name(self, k):
        k = k.replace('.', '_')
        name = k
        if type(name) == int: name = 'v%d' % name
        name = name.lower()
        return name

    def spin_configure(self, w, v1, v2, step, v=None):
        kw = {}
        if v1 < 0: kw['from_'] = v1
        else: kw['from'] = v1
        if v2 < 0: kw['to_'] = v2
        else: kw['to'] = v2
        kw['increment'] = step
        if v != None:
            kw['text'] = '%f' % v
        w.configure(**kw)
        if v != None:
            t = w['textvariable']
            #t.set(v)

    def make_cmdw(self, f1, k, cmds):
        l, w = None, None
        cmd = cmds[k]
        send = cmd.send
        if cmd.label:
            if send:
                if not cmd.l:
                    cmd.l = tk.StringVar(value=('1'))
                l = ttk.Checkbutton(f1, text=cmd.label, variable=cmd.l)
            else:
                l = ttk.Label(f1, text=cmd.label)
        if not cmd.wdgt:
            return l, w
        vv = []
        if cmd.value:
            vv = cmd.value
            if type(vv) == OD:
                vv = list(vv.keys())
            if type(vv) == list:
                m = max(vv, key=len)
                cmd.width = len(m) + 1
        if not cmd.t:
            cmd.t = tk.StringVar()
        if cmd.t.get() == '' and cmd.text != None:
            cmd.t.set(cmd.text)
        #if cmd.t.get() == '' and type(vv) == list and len(vv) > 0:
            #cmd.t.set(vv[0])
        if cmd.wdgt == 'combo':
            name = self.key_to_name(k)
            w = ttk.Combobox(f1, name=name, textvariable=cmd.t)
            w['value'] = vv
        elif cmd.wdgt == 'entry':
            w = tk.Entry(f1, textvariable=cmd.t)
            if cmd.width:
                w.configure(width=cmd.width)
        elif cmd.wdgt == 'check':
            w = ttk.Checkbutton(f1, text=cmd.name, variable=cmd.t)
        elif cmd.wdgt == 'radio':
            f = ttk.Frame(f1, borderwidth=1)
            cmd.radio = {}
            for k1 in vv:
                w1 = ttk.Radiobutton(f, text=k1, variable=cmd.t, value=k1)
                cmd.radio[k1] = w1
                w1.pack(anchor=tk.W)
                if 'disable' in cmd:
                    if k1 in cmd.disable:
                        w1.state(['disabled'])
            f['relief'] = 'sunken'
            f['padding'] = (1,1)
            w = f
        elif cmd.wdgt == 'spin':
            v1 = cmd.value['min']
            v2 = cmd.value['max']
            step = cmd.value['step']
            name = self.key_to_name(k)
            w = tk.Spinbox(f1, name=name, textvariable=cmd.t, width=12)
            self.spin_configure(w, v1, v2, step)
            if l != None:
                label = l['text']
                label += ' (%g..%g)' % (v1, v2)
                l['text'] = label
        elif cmd.wdgt == 'alarm':
            w = tk.Frame(f1, width=12, height=12, background='red')
        elif cmd.wdgt == 'button':
            w = tk.Button(f1, text=cmd.text)
            if cmd.click_cb:
                w.configure(command=cmd.click_cb)
        ttw = w if w else l
        if ttw:
            if cmd.msgFunc:
                ToolTip(ttw, msg=cmd.msg, msgFunc=cmd.msgFunc, follow=True, delay=0)
            elif cmd.msg:
                msg = cmd.msg.replace(';', '\n')
                ToolTip(ttw, msg=msg, follow=True, delay=0)
        if cmd.tip: cmd.pop('tip')
        if l:
            cmd.lw = l
            if cmd.send:
                l.bind('<Button-3>', lambda evt, k=k: self.rbutton_cb(k))
        if w:
            if cmd.state:
                w['state'] = cmd.state
            cmd.w = w
            if cmd.click_cb and cmd.wdgt != 'button':
                w.bind('<ButtonPress>', lambda evt: cmd.click_cb(self.data))
        self.data.trace_add(k, cmd)
        return l, w

    def init_frame(self, parent, cmds, rowconfigure=True, cw0=1):
        f1 = tk.Frame(parent, borderwidth=2)
        j = 0
        bl = False
        bw = False
        for k,v in cmds.items():
            l, w = self.make_cmdw(f1, k, cmds)
            if l == None and w == None:
                continue
            if l != None:
                l.grid(column=0, row=j, sticky=tk.N+tk.E+tk.W, ipadx=5, pady=self.pady)
                bl = True
            if w != None:
                column = 0 if v.columnspan else 1
                columnspan = v.columnspan if v.columnspan else 1
                w.grid(column=column, columnspan=columnspan, row=j, sticky=tk.N+tk.E+tk.W, ipadx=5, pady=self.pady)
                v.pady = self.pady
                bw = True
            if rowconfigure:
                f1.rowconfigure(j, weight=1)
            j = j + 1
        if bl: f1.columnconfigure(0, weight=cw0)
        if bw: f1.columnconfigure(1, weight=1)
        cmds.f = f1
        return f1

    def add_tab(self, cmds, rowconfigure=True):
        f1 = self.init_frame(self.tabs, cmds, rowconfigure=rowconfigure)
        self.tabs.add(f1, text=cmds.name, sticky=tk.NSEW)
        cmds.tabid = self.tabs.tabs()[-1]

    def init_menu(self):
        if hasattr(self, 'data'):
            if hasattr(self.data, 'menu'):
                self.add_menus(self.data.menu)

    def init_layout(self):
        if len(self.data) == 1:
            f1 = self.init_frame(self.frame, self.data.cmds)
            f1.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
        else:
            self.tabs = ttk.Notebook(self.frame)
            self.tabs.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
            for cmds in self.data:
                self.add_tab(cmds)
            self.data.bind_tab_cb(self.tabs)
        if hasattr(self.data, 'dev'):
            self.pb = ttk.Progressbar(self.frame, orient=tk.HORIZONTAL, maximum=10)
            self.pb.pack(fill=tk.X, expand=0, padx=5, pady=5)
        if self.data.buttons != None:
            self.add_fb()
            self.add_button(self.fb, 'Close', self.root.destroy)
            kk = reversed(list(self.data.buttons.keys()))
            for k in kk:
                self.add_button(self.fb, text=k, command=lambda k=k: self.button_cb(k))

    def add_button(self, frame, text, command, side=tk.RIGHT):
        b = tk.Button(frame, text=text, command=command)
        b.pack(side=side, padx=5, pady=5)

    def add_buttons_ok_cancel(self):
        self.add_fb()
        self.add_button(self.fb, 'Cancel', self.root.destroy)
        self.add_button(self.fb, 'Ok', self.ok_cb)

    def ok_cb(self):
        self.kw = {}
        for k,v in self.data.items():
            if v.w.winfo_ismapped():
                self.kw[k] = v.t.get()
        self.root.destroy()

    def add_buttons_read_write_close(self):
        self.add_fb()
        self.add_button(self.fb, 'Close', self.root.destroy)
        self.add_button(self.fb, 'Write', self.write_cb)
        self.add_button(self.fb, 'Read', self.read_cb)

    def read_cb(self, *args):
        self.read = True
        self.io.start()

    def write_cb(self, *args):
        self.read = False
        self.io.start()

    def init_io(self):
        self.io.add(self.ctrl_cb1, self.ctrl_cb2, self.ctrl_cb3, self.cmdio_thread)

    def ctrl_cb1(self, do_cmds=True):
        if do_cmds:
            self.data.do_cmds(self.qo, self.read)
        return self.tmp_cb1()

    def ctrl_cb2(self, line=''):
        if not line:
            line = self.qi.get_nowait()
        if hasattr(self, 'pb'):
            self.pb['value'] = self.pb['value'] + 1
        if line.find('step') != -1:
            return
        cmdid, val = line.split(' ', 1)
        if val and self.read:
            self.data.set_value(cmdid, val)
        else:
            return False
        return True

    def ctrl_cb3(self):
        if len(self.io.na):
            na = ','.join(self.io.na)
            messagebox.showerror(title='Error', message='Device is not available (%s)' % na, master=self.root)
            return False
        return True

