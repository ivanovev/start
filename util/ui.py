
import os, types
import tkinter as tk
from tkinter import filedialog
from collections import OrderedDict as OD
import pdb

def sel_dec(f):
    def tmp(*args, **kwargs):
        w = args[1]
        id1 = args[2] if len(args) >= 3 else None
        if id1 == None:
            id1 = w.selection()
            if len(id1) == 0:
                return
            id1 = id1[0]
        args = list(args)
        if len(args) >= 3:
            args[2] = id1
        else:
            args.append(id1)
        return f(*tuple(args), **kwargs)
    return tmp

class UI:
    def __init__(self, fileext='txt', filename=None):
        self.fileext = fileext
        if filename:
            if self.fileopen(filename):
                self.update_title(filename)

    def add_menus(self, items, menubar=None, menu_cb=None):
        if items == None:
            return
        if menubar == None:
            if hasattr(self, 'menubar'):
                menubar = self.menubar
            else:
                self.menubar = tk.Menu(self.root)
                menubar = self.menubar
                self.root['menu'] = menubar
        for k,v in items.items():
            if type(v) in [dict, OD]:
                p1 = tk.Menu(menubar, tearoff=0)
                menubar.add_cascade(menu=p1, label=k)
                self.add_menus(v, p1, menu_cb)
                v['m'] = p1
            elif v == None:
                menubar.add_separator()
            elif type(k) in [tuple]:
                sv = tk.StringVar(value=k[0])
                for i in k:
                    menubar.add_radiobutton(label=i, variable=sv, value=i, command=lambda v=v,i=i: v(self,i))
            elif type(v) in [types.FunctionType, types.MethodType]:
                if menu_cb == None:
                    f = lambda v=v: v(self)
                else:
                    f = lambda v=v: menu_cb(v)
                menubar.add_command(label=k, command=f)
        return items

    def get_menu_file(self):
        m = OD()
        mf = OD()
        mf['Open'] = self.fileopen_cb
        mf['Save'] = self.filesave_cb
        mf['Save As'] = self.filesaveas_cb
        mf['Export'] = self.filesaveas_cb
        mf['separator'] = None
        mf['Exit'] = self.exit_cb
        m['File'] = mf
        return m

    def add_menu_file(self, file_open=True, file_save=True, file_saveas=True, file_export=False, file_exit=True):
        menu = self.get_menu_file()
        mf = menu['File']
        if not file_open:
            mf.pop('Open')
        if not file_save:
            mf.pop('Save')
        if not file_saveas:
            mf.pop('Save As')
        if not file_export:
            mf.pop('Export')
        if not file_exit:
            mf.pop('separator')
            mf.pop('Exit')
        return self.add_menus(menu)

    def get_initialfile(self, read=True):
        if self.fileext != '*':
            return 'data.' + self.fileext
        else:
            return 'data'

    def get_filetypes(self):
        ext = self.fileext
        if ext != '*':
            filetypes = [(ext + ' files', '.' + ext), ('all files', '*')]
        else:
            filetypes = [('all files', '*')]
        return filetypes

    def update_title(self, fname):
        self.filename = fname
        self.root.title(self.name + ' (' + fname + ')')

    def fileopen_cb(self, *args):
        default = self.get_initialfile(True)
        filetypes = self.get_filetypes()
        fname = filedialog.askopenfilename(title='Open', filetypes=filetypes, initialfile=default)
        if len(fname) == 0:
            return
        if hasattr(self, 'fileopen'):
            self.fileopen(fname, *args)
            self.update_title(fname)

    def filesave_cb(self, *args):
        if hasattr(self, 'filename'):
            self.filesave(self.filename)
        else:
            self.filesaveas_cb()

    def filesaveas_cb(self, *args):
        if hasattr(self, 'filename'):
            default = os.path.basename(self.filename)
        else:
            default = self.get_initialfile(False)
        if default == None:
            return
        filetypes = self.get_filetypes()
        fname = filedialog.asksaveasfilename(title='Save As', filetypes=filetypes, initialfile=default)
        if len(fname) == 0:
            return
        if hasattr(self, 'filesave'):
            self.update_title(fname)
            self.filesave(fname)

    def exit_cb(self, *args):
        self.root.withdraw()
        if hasattr(self, 'parent'):
            if self.parent != None:
                self.parent.update_idletasks()
        self.root.destroy()

    def center(self, show=True):
        W = self.root.winfo_screenwidth()
        H = self.root.winfo_screenheight()
        #self.root.update_idletasks()
        self.root.update()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        x = W/2 - width/2
        y = H/2 - height/2
        self.root.geometry("+%d+%d" % (x, y))
        if show:
            self.root.deiconify()
            #self.root.state('normal')

    def do_modal(self):
        #self.root.focus_set()
        #self.root.grab_set()
        self.root.transient(self.parent)
        self.center()
        self.root.wait_window(self.root)

    def add_widget_with_scrolls(self, f1, w1, horiz=True, vert=True, column=0, row=0):
        w1.grid(column=column, row=row, sticky=tk.NSEW)
        f1.columnconfigure(column, weight=1)
        f1.rowconfigure(row, weight=1)

        if horiz:
            scrx = tk.Scrollbar(f1, orient=tk.HORIZONTAL, command=w1.xview)
            w1.config(xscrollcommand=scrx.set)
            scrx.grid(column=column, row=row+1, sticky=tk.W+tk.E)
            f1.rowconfigure(row+1, weight=0)

        if vert:
            scry = tk.Scrollbar(f1, orient=tk.VERTICAL, command=w1.yview)
            w1.config(yscrollcommand=scry.set)
            scry.grid(column=column+1, row=row, sticky=tk.N+tk.S)
            f1.columnconfigure(column+1, weight=0)

    def text_append(self, w, l, newline=False, clear=False, color=None, see=True):
        state = w.cget('state')
        w.config(state=tk.NORMAL)
        if clear:
            w.delete(1.0, tk.END)
        if newline:
            txtempty = self.text_line_count(w) == 1
            if not txtempty:
                w.insert(tk.END, '\n')
        i1 = w.index(tk.INSERT)
        w.insert(tk.END, l)
        i2 = w.index(tk.INSERT)
        if color != None:
            w.tag_add(l, i1, i2)
            w.tag_config(l, background=color)
        if see:
            w.see(tk.END)
        w.config(state=state)

    def text_line_count(self, w):
        ii = w.index('end-1c').split('.')
        i0 = int(ii[0])
        if i0 > 1:
            return i0
        i1 = int(ii[1])
        if i1 > 0 and i0 == 1:
            return 2
        return 1
        #return int(w.index('end-1c').split('.')[0])

    def text_clear(self, w):
        state = w.cget('state')
        w.config(state=tk.NORMAL)
        w.delete(1.0, tk.END)
        w.config(state=state)

    def tree_init(self, w, anchorcenter=None):
        w.column('#0', stretch=0, width=24, minwidth=0)
        for i in self.columns:
            w.heading(i, text=i)
            w.column(i, width=100)
            if self.columns.index(i) == 0 and not anchorcenter:
                w.column(i, stretch=0)
            if self.columns.index(i) > 0 and anchorcenter:
                w.column(i, anchor='center')

    def tree_add_lvl0(self, w, od, tags=(), expand=False):
        c0 = None
        if type(od) == OD:
            c0 = list(od.values())[0]
        elif type(od) in [list, tuple]:
            c0 = od[0]
        if c0:
            id1 = w.insert('', 'end', tags=tags)
            self.tree_update_item(w, id1, od)
            if expand:
                w.item(id1, open=tk.TRUE)

    def tree_add_lvl1(self, w, lvl0, item, expand=True):
        lvl0id = self.tree_find_lvl0id(w, lvl0)
        lvl1id = w.insert(lvl0id, 'end', tags=('evt'))
        if expand:
            w.see(lvl1id)
            w.selection_set(lvl1id)
        self.tree_update_item(w, lvl1id, item)

    def tree_update_item(self, w, itemid, item):
        if type(item) in [dict, OD]:
            for i in self.columns:
                w.set(itemid, i, item[i] if i in item else '')
        elif type(item) in [list, tuple]:
            for i in range(0, len(item)):
                w.set(itemid, self.columns[i], item[i])

    def tree_find_lvl0id(self, w, name):
        c0 = self.columns[0]
        ids = w.get_children()
        for i in ids:
            if w.set(i, c0) == name:
                return i

    @sel_dec
    def tree_data(self, w, id1=None):
        lvl = self.tree_item_lvl(w, id1)
        c0 = self.columns[0]
        l = w.item(id1)
        for i in self.columns:
            s = w.set(id1, i)
            if len(s) > 0:
                l[i] = s
        keys = set.intersection(set(self.columns), set(l.keys()))
        if lvl == 0:
            keys.add('open')
        data = {i:l[i] for i in keys}
        return data

    @sel_dec
    def tree_parent_data(self, w, id1=None):
        parent = w.parent(id1)
        if parent == '': return
        return self.tree_data(w, parent)

    @sel_dec
    def tree_item_lvl(self, w, id1=None):
        ids0 = w.get_children()
        ret = 0 if id1 in ids0 else 1
        return ret

