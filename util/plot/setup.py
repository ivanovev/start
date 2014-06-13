
import tkinter as tk
import tkinter.ttk as ttk

from collections import OrderedDict as OD
from copy import deepcopy

from util.control import Control
from util.server import proxy
from util import CachedDict

from .browse import Browse
from .plotdata import PlotData, get_cmdsx

import util
import sys, pdb

class Setup(Control):
    def __init__(self, parent=None, mode='', apps=None, args=None):
        self.apps = apps
        self.args = args
        self.cd = CachedDict()
        self.mode = mode
        self.trees = {}
        self.src = {}
        self.columns = ['name', 'value']
        title = 'Plot setup F(%s)' % mode[1:]
        Control.__init__(self, data=PlotData(), parent=parent, title=title)

    def init_common_layout(self):
        self.paned = tk.PanedWindow(self.frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned.pack(fill=tk.BOTH, expand=1)

        self.fl = tk.Frame(self.paned)
        self.paned.add(self.fl, sticky=tk.NSEW, padx=5)

        self.fr = tk.Frame(self.paned, relief=tk.GROOVE, borderwidth=2)
        self.paned.add(self.fr, sticky=tk.NSEW, padx=5)

        self.fy = tk.Frame(self.fr, relief=tk.GROOVE, borderwidth=2)
        self.fy.pack(fill=tk.BOTH, side=tk.TOP, expand=1)
        self.ylb = tk.Listbox(self.fy)
        self.add_widget_with_scrolls(self.fy, self.ylb)
        self.cmdsy = OD()

        self.fx = tk.Frame(self.fr, relief=tk.GROOVE, borderwidth=2)
        self.fx.pack(fill=tk.X, side=tk.BOTTOM, expand=1)

        self.add_buttons_ok_cancel()
        self.add_button(self.fb, 'Add', self.add_cb, side=tk.LEFT)
        self.add_button(self.fb, 'Delete', self.delete_cb, side=tk.LEFT)

    def init_xlayout(self):
        self.data.update(get_cmdsx(self.mode))
        self.data.select(self.mode)
        fx1 = self.init_frame(self.fx, self.data.cmds)
        fx1.pack(fill=tk.BOTH, expand=1)

    def init_layout(self):
        self.init_common_layout()
        self.init_tabs()
        self.init_xlayout()

    def ok_cb(self):
        pr = self.data.to_args(self.mode)
        self.root.destroy()
        print(pr)
        if pr != None:
            proxy.start_process(*pr)

    def add_cb(self):
        ax = self.ax
        tree = self.trees[ax]
        item = self.tree_data(tree)
        if item == None:
            return
        parent = self.tree_parent_data(tree)
        if parent == None:
            return
        c0 = self.columns[0]
        c1 = self.columns[1]
        kp = parent[c0]
        ki = item[c0]
        v = self.src[ax][kp][ki]
        k = '_'.join([kp, ki, item[c1]])
        k = k.replace(' ', '')
        self.data.select(ax)
        if ax == 'x':
            self.data.set_value('xlabel', k)
            spn = v.value
            for k1,v1 in spn.items():
                self.data.set_value(k1, v1)
            self.data.cmds.clear()
        elif ax == 'y':
            if k in self.data.cmds:
                return
            self.ylb.insert(tk.END, k)
        self.data.add(k, **v)
        print(list(self.data.cmds.keys()))

    def delete_cb(self):
        ysel = self.ylb.curselection()
        if len(ysel) == 0:
            return
        ysel = int(ysel[0])
        y = self.ylb.get(ysel)
        self.data.select('y')
        self.data.cmds.pop(y)
        self.ylb.delete(ysel, ysel)
        print(list(self.data.cmds.keys()))

    def init_tabs(self):
        self.tabs = ttk.Notebook(self.fl)
        self.tabs.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
        self.add_treetab('y')
        if self.mode == 'fx':
            self.add_treetab('x')
        self.tabs.bind('<<NotebookTabChanged>>', lambda evt: self.ax_update_cb(evt))
        self.ax_update_cb()

    def ax_update_cb(self, *args):
        n = self.tabs.tabs().index(self.tabs.select())
        self.ax = 'x' if n else 'y'

    def add_treetab(self, ax):
        f1 = tk.Frame(self.tabs)
        tablabel = 3*' '+ax+3*' '
        tablabel = tablabel.upper()
        self.tabs.add(f1, text=tablabel, sticky=tk.NSEW)

        tree = ttk.Treeview(f1, columns=self.columns)
        self.tree_init(tree)
        self.add_widget_with_scrolls(f1, tree)
        self.trees[ax] = tree
        self.populate_tree(tree, ax)

    def populate_tree(self, tree, ax):
        if ax == 'y':
            self.dd = self.parent.get_devices('mntr')
        elif ax == 'x':
            self.dd = self.parent.get_devices('ctrl')
        self.src[ax] = PlotData()
        self.data.add_page(ax, send=False)
        for k,v in self.dd.items():
            if k in self.src[ax]:
                print('duplicate item:', k)
                continue
            self.tree_add_lvl0(tree, [k])
            vv = v['getter'](v)
            data = PlotData(vv)
            data.merge()
            data.update_label()
            for k1,v1 in data.cmds.items():
                v1.dev = v
                self.tree_add_lvl1(tree, k, [k1, v1.label], expand=False)
            self.src[ax].add_page(k, data.cmds)

