
from collections import OrderedDict as OD

from .control import Control
from .cache import CachedDict
from .server import proxy
from .columns import *
from .io import MyAIO
from .data import Obj

import tkinter as tk
import re, time, pdb

import asyncio

from . import Data, Obj

class Rpc(Control):
    def __init__(self, srv=proxy.get_local_srv(), title='RPC test'):
        Control.__init__(self, data=Data(), title=title)
        self.cd = CachedDict()
        self.center()
        self.lastsrv = None
        self.aio = True
        self.root.bind('<Activate>', self.activate_cb, '+')
        self.listupd_cb1()

    def init_layout(self):
        self.pady=5
        self.init_common_layout()
        self.init_custom_layout()

    def init_common_layout(self):
        self.paned = tk.PanedWindow(self.frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned.pack(fill=tk.BOTH, expand=1)

        self.f1 = tk.Frame(self.paned)
        self.paned.add(self.f1, sticky=tk.NSEW, padx=5)

        self.listupd_cb = lambda *args: asyncio.async(self.io_listupd.start())
        self.data.add_page('cmds')
        self.data.add('srv', wdgt='entry', label='Server', text=proxy.get_local_srv(), msg='press Enter to reload list')
        self.data.add('filter', wdgt='combo', label='Filter', state='readonly', value=['*'], text='*', click_cb=self.filter_click_cb, trace_cb=self.listupd_cb)
        self.f11 = self.init_frame(self.f1, self.data.cmds, cw0=0)
        self.f11.pack(fill=tk.BOTH, expand=0)
        self.data.cmds['srv'].w.bind('<Return>', self.listupd_cb)

        self.paned1 = tk.PanedWindow(self.f1, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.paned1.pack(fill=tk.BOTH, expand=1)

        self.argsupd_cb = lambda *args: asyncio.async(self.io_argsupd.start())
        f12 = tk.Frame(self.paned1)
        self.paned1.add(f12, sticky=tk.NSEW, pady=5)
        self.lb = tk.Listbox(f12)#, selectmode=tk.SINGLE)
        self.lb.bind('<<ListboxSelect>>', self.argsupd_cb)
        self.add_widget_with_scrolls(f12, self.lb)

        self.data.add_page('func')
        self.data.add('fcount', wdgt='entry', label='# of functions', state='readonly')
        f = self.init_frame(self.f1, self.data.cmds)
        f.pack(fill=tk.X, expand=0)
        self.data.select(0)

        self.f2 = tk.Frame(self.paned)
        self.paned.add(self.f2)

        self.txt = tk.Text(self.f2, wrap=tk.NONE, bg='white', state=tk.DISABLED)
        self.add_widget_with_scrolls(self.f2, self.txt)

        self.add_fb()
        self.add_button(self.fb, 'Close', self.root.destroy)
        self.wrap = self.add_checkbutton(self.fb, 'Wrap', self.wrap_words_cb)

    def init_custom_layout(self):
        self.f13 = tk.Frame(self.paned1)
        self.paned1.add(self.f13, sticky=tk.NSEW, pady=5)

        self.add_button(self.fb, 'Clear', self.clear_cb, side=tk.LEFT)
        self.add_button(self.fb, 'Call', lambda: asyncio.async(self.io.start()), side=tk.LEFT)

    def add_checkbutton(self, f, text, cb):
        var = tk.StringVar()
        var.set(0)
        var.trace_variable('w', lambda var, val, mode: cb())
        btn = tk.Checkbutton(f, text=text, variable=var)
        btn.pack(side=tk.RIGHT, padx=5, pady=5)
        return var

    def wrap_words_cb(self):
        if int(self.wrap.get()):
            self.txt.configure(wrap=tk.WORD)
        else:
            self.txt.configure(wrap=tk.NONE)

    def get_method(self):
        if getattr(self, 'mm', False):
            cursel = self.lb.curselection()
            if len(cursel) > 0:
                return self.lb.get(int(cursel[0]))
            if hasattr(self, 'fa') and hasattr(self, 'm'):
                return self.m

    def filter_click_cb(self, data):
        self.listupd_cb()
        if hasattr(self, 'mm'):
            x = set()
            for m in self.mm:
                a = m.split('.')[0]
                x.add(a + '.*')
            x = list(x)
            x.sort()
            x.insert(0, '*')
        else:
            x = ['*']
        v = self.data.find_v('filter')
        v.w.configure(values=x)

    def get_method_argsframe(self):
        srv = self.data.get_value('srv')
        m = self.get_method()
        cmds = self.cd.get(self.get_method_args, 'srv', srv, m, 'cmds')
        if cmds == None:
            return
        f = self.init_frame(self.f13, cmds, cw0=0)
        for v in cmds.values():
            w = v['w']
            w.bind('<Return>', lambda evt: asyncio.async(self.io.start()))
            if hasattr(self, 'cursors'):
                self.cursors[str(w)] = w.cget('cursor')
        return f

    def get_method_args(self):
        srv = self.data.get_value('srv')
        m = self.get_method()
        obj = self.cd.get(lambda: proxy.get_argspec(srv, m), 'srv', srv, m, 'argspec')
        if obj == None:
            return
        cmds = OD()
        loa = len(obj.args)
        for i in range(0, loa):
            a = obj.args[i]
            dflt = None
            if obj.defaults != None:
                lod = len(obj.defaults)
                if i >= loa - lod:
                    dflt = obj.defaults[i - loa + lod]
            if a != 'self':
                cmds[a] = Obj(wdgt='entry', label=a)
                if dflt != None:
                    cmds[a].text = dflt
        return cmds

    def get_args(self):
        srv = self.data.get_value('srv')
        m = self.get_method()
        cmds = self.cd.get(self.get_method_args, 'srv', srv, m, 'cmds')
        args = []
        if cmds:
            for v in cmds.values():
                args.append(v['t'].get())
        return args

    def select_method(self, m):
        if m not in self.mm:
            print('method not found', m)
            return False
        self.lb.selection_clear(0, self.lb.size())
        t = list(self.lb.get(0, self.lb.size()))
        if m not in t:
            self.data.set_value('filter', '*')
            self.listupd_cb1()
            self.root.update_idletasks()
            return self.select_method(m)
        i = t.index(m)
        self.lb.selection_set(i)
        self.lb.see(i)
        return True

    def txt_click_cb(self, srv, l):
        srv1 = self.data.get_value('srv')
        if srv != srv1:
            self.data.set_value('srv', srv)
            self.root.update_idletasks()
        l = l.replace('(', ',')
        l = l.replace(')', '')
        l = l.strip()
        cc = l.split(',')
        m = cc.pop(0)
        if not self.select_method(m):
            return
        #self.data.set_value('method', m)
        for i in range(0, len(cc)):
            cc[i] = cc[i].strip()
        self.argsupd_cb1()
        self.root.update_idletasks()
        cmds = self.cd.get(self.get_method_args, 'srv', srv, m, 'cmds')
        kk = list(cmds.keys())
        if len(cc) == len(kk):
            for i in range(0, len(cc)):
                k = kk[i]
                v = cmds[k]
                v['t'].set(cc[i])

    def clear_cb(self):
        self.text_clear(self.txt)
        self.lastsrv = None

    def init_io(self):
        self.io = MyAIO(self)
        self.io.add(self.rpc_cb1, self.rpc_cb2)
        self.io_listupd = MyAIO(self)
        self.io_listupd.add(self.listupd_cb1)
        self.io_argsupd = MyAIO(self)
        self.io_argsupd.add(self.argsupd_cb1)

    def rpc_cb1(self, m=None):
        srv = self.data.get_value('srv')
        if not m:
            m = self.get_method()
        args = self.get_args()
        self.qo.put(Obj(srv=srv, m=m, args=args, cmdid='tmp'))
        return True

    def rpc_cb2(self, cmdid, val):
        s = val
        m = self.get_method()
        srv = self.data.get_value('srv')
        args = self.get_args()
        if srv != self.lastsrv:
            self.lastsrv = srv
            self.text_append(self.txt, srv, newline=True, color='green')
        if type(s) == bool:
            s = 1 if s else 0
        if type(s) == int:
            s = '%d' % s
        if type(s) == float:
            s = '%f' % s
        if type(s) == list:
            s = ' '.join(s)
        if s:
            self.text_append(self.txt, '', newline=True)
            self.txt.see(tk.END)
            l = m + '(' + ', '.join(args) + ')'
            link = tk.Label(self.txt, text=l, cursor="hand1")
            link.bind("<1>", lambda *args, srv=srv, l=l: self.txt_click_cb(srv, l))
            self.txt.window_create(tk.END, window=link)
            self.text_append(self.txt, ' = ' + s, newline=False)
            if hasattr(self, 'cursors'):
                self.cursors[str(link)] = link.cget('cursor')
        else:
            self.text_append(self.txt, '%s: %s error' % (srv, m), newline=True, color='red')
            self.lastsrv = None

    def listupd_cb1(self):
        if hasattr(self, 'mm'):
            delattr(self, 'mm')
        srv = self.data.get_value('srv')
        fltr = self.data.get_value('filter')
        mm = proxy.get_methods(srv)
        if not mm:
            return False
        self.mm = mm
        self.lb.delete(0, tk.END)
        if self.mm:
            for l in self.mm:
                if re.match(fltr, l) != None if fltr != '*' else True:
                    self.lb.insert(tk.END, l)
        if hasattr(self, 'fa'):
            self.fa.pack_forget()
            delattr(self, 'fa')
        self.data.set_value('fcount', '%d' % self.lb.size())
        return False

    def argsupd_cb1(self):
        srv = self.data.get_value('srv')
        m = self.get_method()
        if hasattr(self, 'fa'):
            self.fa.pack_forget()
            delattr(self, 'fa')
        if m == None:
            return
        fa = self.cd.get(self.get_method_argsframe, 'srv', srv, m, 'frame')
        if fa == None:
            self.root.update_idletasks()
            self.text_append(self.txt, '%s: get signature %s failed' % (srv, m), newline=True, color='red')
            return
        self.fa = fa
        self.m = m
        self.fa.pack(fill=tk.BOTH, expand=0)
        self.root.update_idletasks()
        wa = self.fa.winfo_width()
        w = self.f13.winfo_width()
        if wa > w:
            self.paned.sash_place(0, wa + 1, 1)
        self.lb.see(self.lb.curselection()[0])

    def activate_cb(self, *args):
        print('activate')

