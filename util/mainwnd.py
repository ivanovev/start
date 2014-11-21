#!/usr/bin/env python3

import tkinter as tk
import tkinter.ttk as ttk
import json
import sys

from collections import OrderedDict as OD

from . import CachedDict, Data, app_name, app_gui, app_tools, app_devdata
from .control import Control
from .columns import *
from .server import proxy
from .ui import UI

import pdb

def watch_dec(f):
    def tmp(*args, **kwargs):
        wnd = args[0]
        if hasattr(wnd, 'root'):
            wnd = wnd.root
        wnd.config(cursor='watch')
        wnd.update_idletasks()
        try:
            ret = f(*args, **kwargs)
        except:
            ret = None
        wnd.config(cursor='')
        wnd.update_idletasks()
        return ret
    return tmp

class Mainwnd(tk.Tk, UI):
    def __init__(self, apps, filename=None):
        tk.Tk.__init__(self)
        self.root = self
        self.withdraw()
        Mainwnd.mw = self
        self.apps = apps
        self.name = app_name(apps)
        self.devdata = app_devdata(apps)
        self.columns = get_columns()
        for p in self.devdata:
            for k in p.keys():
                if k not in self.columns:
                    self.columns.append(k)
        self.cd = CachedDict()

        self.init_layout()

        UI.__init__(self, 'json', filename)
        self.center()

    def init_layout(self):
        self.title(self.name)
        self.frame = tk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=1)

        items = self.add_menu_file()
        menu_file = items['File']['m']
        def exit_all():
            proxy.stop()
            self.exit_cb()
        menu_file.add_command(label='Exit & stop srv', command=exit_all)

        menu_add = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(menu=menu_add, label='Add')

        if self.devdata:
            for i in self.devdata:
                cat = i.name
                f = lambda cat=cat: self.new_dev(cat)
                menu_add.add_command(label=cat, command=f)

        try:
            menu_tools = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(menu=menu_tools, label='Tools')
            from .plot import plot_menus
            self.add_menus(plot_menus(), menu_tools)
            m = app_tools(self.apps)
            if m:
                self.add_menus(m, menu_tools)
        except:
            pass

        if True:
            self.menu_srv = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(menu=self.menu_srv, label='Server')
            self.menu_srv_status = tk.Menu(self.menu_srv, tearoff=0)
            self.menu_srv.add_cascade(menu=self.menu_srv_status, label='Status')
            self.startsrv = tk.StringVar()
            self.menu_srv_status.add_checkbutton(label='Start/Stop', variable=self.startsrv, command=self.start_stop_server)
            self.menu_srv_status.add_separator()
            self.echo = tk.StringVar()
            self.menu_srv_status.add_checkbutton(label='Echo', variable=self.echo, command=self.set_server_echo)
            self.idle = tk.StringVar()
            self.menu_srv_status.add_checkbutton(label='Idle', variable=self.idle, command=self.set_server_idle)
            self.verbose = tk.StringVar()
            self.menu_srv_status.add_checkbutton(label='Verbose', variable=self.verbose, command=self.set_server_verbose)
            self.menu_srv.add_separator()
            self.menu_srv.add_command(label='ACL', command=lambda: process_cb('acl'))
            self.menu_srv.add_separator()
            self.menu_srv.add_command(label='RPC', command=lambda: process_cb('rpc'))
            self.after(1500, lambda: self.update_server_status(dflt=False))

        menu_help = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(menu=menu_help, label='Help')
        menu_help.add_command(label='RPC Info', command=lambda: process_cb('rpcinfo'))
        menu_help.add_separator()
        menu_help.add_command(label='About', command=lambda: process_cb('about'))

        self.tree = ttk.Treeview(self.frame, columns=self.columns)
        self.tree_init(self.tree, True)
        self.add_widget_with_scrolls(self.frame, self.tree, horiz=False)
        if self.devdata:
            for i in self.devdata:
                self.add_cat(i.name)
        self.tree.tag_bind('evt', '<ButtonPress-3>', self.rbutton_press_cb)
        self.tree.tag_bind('evt', '<ButtonRelease-3>', self.rbutton_release_cb)
        self.tree.tag_configure('color', background='lightgray')

    def start_stop_server(self):
        srvstatus = int(self.startsrv.get())
        if srvstatus:
            proxy.start_server_process()
        else:
            proxy.stop()
        self.update_server_status(srvstatus)

    def update_server_status(self, srvstatus=None, dflt=True, retries=5):
        if srvstatus == None:
            srvstatus = proxy.alive()
            if not srvstatus and retries >= 0:
                retries -= 1
                self.after(1000, lambda: self.update_server_status(dflt=False, retries=retries))
        newstate = tk.NORMAL if srvstatus else tk.DISABLED
        #self.menu_srv.entryconfig(4, state=newstate)
        self.menu_srv_status.entryconfig(2, state=newstate)
        self.menu_srv_status.entryconfig(3, state=newstate)
        self.menu_srv_status.entryconfig(4, state=newstate)
        if srvstatus:
            self.startsrv.set('1')
            if dflt:
                self.echo.set('0')
                self.idle.set('0')
                self.verbose.set('1')
            else:
                self.echo.set(proxy.echo())
                self.idle.set(proxy.idle())
                self.verbose.set(proxy.verbose())
            if not hasattr(self, 'backends'):
                backends = proxy.backends()
                if backends:
                    self.backends = backends.split()
                    if len(self.backends):
                        b1 = proxy.backend()
                        mb = tk.Menu(self.menu_srv, tearoff=0)
                        self.menu_srv.add_separator()
                        self.menu_srv.add_cascade(menu=mb, label='Backend')
                        self.be = tk.StringVar(value=b1)
                        for b in self.backends:
                            mb.add_radiobutton(label=b, variable=self.be, value=b, command=lambda b=b: proxy.backend(b))
        else:
            self.startsrv.set('0')

    def set_server_echo(self):
        proxy.echo(self.echo.get())

    def set_server_idle(self):
        proxy.idle(self.idle.get())

    def set_server_verbose(self):
        proxy.verbose(self.verbose.get())

    def rbutton_press_cb(self, *args):
        evt = args[0]
        itemid = self.tree.identify_row(evt.y)
        if itemid == None: return
        self.tree.selection_set(itemid)
        parent = self.tree.parent(itemid)
        if parent == '':
            return
        self.update_idletasks()
    
    def rbutton_release_cb(self, *args):
        evt = args[0]
        dev = self.itemdata()
        if 'open' in dev: return
        m = tk.Menu(self, tearoff=0)
        menus = self.get_menu(dev)
        self.add_menus(menus, m, menu_cb=lambda f: f(self.itemdata()))
        m.add_separator()
        m.add_command(label='Edit', command=self.edit_dev_cb)
        m.add_command(label='Delete', command=self.delete_dev)
        m.tk_popup(evt.x_root, evt.y_root)

    def popup_menu_cb(self, f=None):
        if f != None:
            f(self, self.itemdata())

    def add_cat(self, cat, catopen=False):
        od = OD([(self.columns[0], cat)])
        self.tree_add_lvl0(self.tree, [cat], tags=('evt', 'color'), expand=catopen)

    def add_dev(self, item, expand=True):
        self.tree_add_lvl1(self.tree, item['cat'], item, expand)

    def update_dev(self, itemid, dev):
        self.tree_update_item(self.tree, itemid, dev)

    def dev_dlg(self, cat, dev=None):
        devdata = app_devdata(self.apps, cat)
        data = Data(name=cat, cmds=devdata.cmds)
        dlg = Control(data=data, parent=self, title=('Edit' if dev else 'Add') + ' ' + cat, pady=5)
        if dev:
            cmds = data.cmds
            for k,v in dev.items():
                if k in cmds:
                    cmds[k]['t'].set(v)
        dlg.add_buttons_ok_cancel()
        dlg.do_modal()
        if not hasattr(dlg, 'kw'):
            return
        if len(dlg.kw.keys()) == 0:
            return
        if len(dlg.kw['name']) == 0:
            return
        dlg.kw['cat'] = cat
        return dlg.kw

    def edit_dev_cb(self):
        itemid = self.tree.selection()
        if itemid == '': return
        parent = self.tree.parent(itemid)
        if parent == '': return
        parentdata = self.itemdata(parent)
        dev = self.dev_dlg(parentdata['name'], self.itemdata(itemid))
        if dev != None:
            self.update_dev(itemid, dev)

    def delete_dev(self):
        itemid = self.tree.selection()
        if itemid == '': return
        self.tree.delete(itemid)

    def new_dev(self, cat):
        dev = self.dev_dlg(cat)
        if dev != None:
            self.add_dev(dev)

    def fileopen(self, fname):
        try:
            f = open(fname, 'r')
        except:
            return False
        self.tree_clear(self.tree)
        cat = None
        all_cats = [i.name for i in self.devdata]
        for i in f.readlines():
            item = json.loads(i)
            if 'open' in item:
                cat = item['name']
                if cat not in all_cats:
                    cat = None
                    continue
                all_cats.pop(all_cats.index(cat))
                o = item['open']
                catopen = False
                if type(o) == int:
                    catopen = bool(o)
                #if type(o) == unicode:
                    #o = str(o)
                if type(o) == str:
                    if len(o) == 1: catopen = bool(int(o))
                    else: catopen = (o.lower() == 'true')
                self.add_cat(cat, catopen)
            elif cat != None:
                item['cat'] = cat
                self.add_dev(item, False)
        for c in all_cats:
            self.add_cat(c, False)
        f.close()
        return True

    def itemdata(self, id1=None):
        return self.tree_data(self.tree, id1)

    def filesave(self, fname):
        f = open(fname, 'w')
        self.iteritems(self.tree, lambda itemid: f.write(json.dumps(self.itemdata(itemid)) + '\n'), None)
        f.close()

    def get_initialfile(self, read=True):
        return get_default_filename(self.apps)

    @watch_dec
    def get_menu(self, dev):
        k = '.'.join([dev[c_name], dev[c_type]])
        getter = self.cd.get(lambda: app_gui(self.apps, dev[c_type], 'get_menu'), k, 'menu')
        if getter != None:
            try:
                return self.cd.get(lambda: getter(dev), k, 'menuobj')
            except:
                return

    def get_devices(self, mode='ctrl'):
        dd = OD()
        def dev_cb(itemid):
            dev = self.itemdata(itemid)
            if len(dev) >= 3:
                k = '.'.join([dev[c_name], dev[c_type]])
                getter = self.cd.get(lambda: app_gui(self.apps, dev[c_type], 'get_' + mode), k, mode)
                if getter != None:
                    dev['getter'] = getter
                    dd[k] = dev
        self.iteritems(self.tree, dev_cb)
        return dd

def process_cb(mode, dev=None):
    pr = []
    pr.append(sys.argv[0])
    pr.extend(['--mode', mode])
    if dev != None:
        for i in dev:
            if type(dev[i]) == str:
                pr.extend(['--' + i, dev[i]])
    proxy.start_process(*pr)

def monitor_cb(dev):
    process_cb('monitor', dev)

def control_cb(dev):
    process_cb('control', dev)

def get_default_filename(apps):
    return app_name(apps) + '.json'

