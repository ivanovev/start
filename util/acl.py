#!/usr/bin/env python

import tkinter as tk
import socket
from collections import OrderedDict as OD
from .control import Control
from . import server, Data

class Acl(Control):
    def __init__(self, parent=None):
        Control.__init__(self, parent=parent, title='Server ACL')

    def init_layout(self):
        f1 = tk.Frame(self.frame)
        f1.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
        self.lvar = tk.StringVar(value=tuple(server.MyServer.load_acl()))
        self.lb = tk.Listbox(f1, listvariable=self.lvar)
        self.add_widget_with_scrolls(f1, self.lb, horiz=False)

        self.add_fb()
        self.add_button(self.fb, 'Close', self.root.destroy)
        self.add_button(self.fb, 'Apply', self.apply_acl)
        self.add_button(self.fb, 'Remove', self.remove)
        self.add_button(self.fb, 'Add', self.add)
        self.center()

    def add(self):
        data = Data(name='add')
        ipaddrlist = socket.gethostbyaddr(socket.gethostname())[-1]
        ipaddrlist.insert(0, '*')
        ipaddrlist.insert(1, '127.0.0.1')
        data.add('ipaddr', label='ipaddr', wdgt='combo', value=ipaddrlist)
        dlg = Control(data=data, parent=self.root, title='Add IP addr')
        dlg.add_buttons_ok_cancel()
        dlg.do_modal()
        if not hasattr(dlg, 'kw'):
            return
        ipaddr = dlg.kw['ipaddr']
        if len(ipaddr) == 0:
            return
        self.lb.insert(tk.END, (ipaddr,))

    def remove(self):
        sel = self.lb.curselection()
        if len(sel) == 0:
            return
        sel = sel[0]
        self.lb.delete(int(sel))

    def apply_acl(self):
        data = self.lb.get(0, tk.END)
        l = []
        for i in data:
            if type(i) == tuple:
                i = i[0]
            l.append(i)
        server.MyServer.save_acl(l)
        server.proxy.reload_acl()

def edit_acl(parent=None):
    acl=Acl(parent)
    if parent == None:
        acl.root.mainloop()
    else:
        acl.do_modal()

if __name__ == "__main__":
    edit_acl()

