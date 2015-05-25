
import pylab
from matplotlib.dates import DateFormatter, MinuteLocator, HourLocator
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

from argparse import ArgumentParser
from collections import OrderedDict as OD
from datetime import datetime, timedelta
from itertools import chain

import asyncio
import tkinter as tk
import tkinter.ttk as ttk

from ..control import Control
from ..monitor import Monitor
from ..columns import c_server
from ..server import proxy
from ..myio import MyAIO
from ..data import Obj

from .plotdata import PlotData
from .setup import get_cmdsx

import sys, pdb

class Plot(Monitor):
    def __init__(self, mode, apps=None, args=None, data=None):
        if not data:
            data = PlotData()
            data.from_args(mode, apps, args)
            self.parse_savefig(args)
        self.mode = mode
        Monitor.__init__(self, data=data)
        self.root.title('Plot f(x)' if mode == 'fx' else 'Plot f(t)')
        self.fileext = 'csv'
        self.stop = False
        self.aio = True
        self.io_start = lambda *args: asyncio.async(self.io.start())
        self.root.bind('<<mainloop>>', self.io_start)

    def add_menu_view(self):
        menu_view = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(menu=menu_view, label='View')
        self.grid = tk.StringVar(value=1)
        menu_view.add_checkbutton(label='Grid', variable=self.grid, command=self.redraw_all)
        menu_view.add_separator()
        cmds = self.data['y']
        for k,v in cmds.items():
            v.view = tk.StringVar(value=1)
            menu_view.add_checkbutton(label=v.label, variable=v.view, command=self.redraw_all)

    def add_menu_edit(self):
        if self.mode == 'ft':
            menu_edit = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(menu=menu_edit, label='Edit')
            menu_edit.add_command(label='Span', command=self.edit_span)

    def edit_span(self):
        data = get_cmdsx('ft')
        for i in ['span', 'dt']:
            data.set_value(i, self.data.get_value(i))
            data.set_value('%sunits' % i, self.data.get_value('%sunits' % i))
        dlg = Control(data=data, parent=self.root, title='Edit time span', pady=5)
        dlg.add_buttons_ok_cancel()
        dlg.do_modal()
        if not hasattr(dlg, 'kw'):
            return
        for i in ['span', 'dt']:
            self.data.set_value(i, dlg.kw[i])
            self.data.set_value('%sunits' % i, dlg.kw['%sunits' % i])
        self.update_formatter()

    def update_formatter(self):
        if self.mode == 'ft':
            span = self.data.get_seconds('span')
            mm = span/60
            if mm < 120:
                interval = 1
                if mm > 20:
                    interval = int(mm/10)
                self.xformatter = DateFormatter('%H:%M')
                self.xlocator = MinuteLocator(interval=interval)
            else:
                self.xformatter = DateFormatter('%H')
                self.xlocator = HourLocator()
        else:
            self.xformatter = ScalarFormatter(useOffset=False)
        self.yformatter = ScalarFormatter(useOffset=False)

    def init_layout(self):
        self.add_menu_file(file_open=False, file_save=False, file_saveas=False, file_export=True)
        self.add_menu_edit()
        self.add_menu_view()
        self.root.protocol('WM_DELETE_WINDOW', self.exit_cb)
        self.fig = Figure(figsize=(5,4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
        self.add_fb()
        fl = tk.Frame(self.fb)
        fl.grid(column=0, row=0, sticky=tk.NSEW)
        toolbar = NavigationToolbar2TkAgg(self.canvas, fl)
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        fr = tk.Frame(self.fb)
        fr.grid(column=1, row=0, sticky=tk.E)
        self.pause = tk.StringVar(value=0)
        cb = ttk.Checkbutton(fr, text='Pause', variable=self.pause, command=self.redraw_all)
        cb.pack(side=tk.RIGHT, expand=0)
        self.fb.columnconfigure(0, weight=1)
        self.fb.columnconfigure(1, weight=1)

        self.xlim = self.get_xlim()
        cmds = self.data['y']
        self.update_formatter()
        i = 0
        l = len(cmds)
        for k,v in cmds.items():
            v.t = tk.StringVar()
            v.l = tk.StringVar(value=1)
            i = i + 1
            v.sp = l*100 + 10 + i
            v.ax = self.fig.add_subplot(v.sp)
            v.xx = [[]]
            v.yy = [[]]
            if i == 9: break
            self.ax_init(v)
            if self.mode == 'ft':
                v.ax.plot_date(pylab.date2num([]), [], 'b')

    def ax_init(self, v):
        v.ax.set_title(v.label)
        x1, x2 = self.get_xlim()
        if self.mode == 'ft':
            v.ax.set_xlim(x1, x2)
            v.ax.xaxis.set_major_locator(self.xlocator)
            v.ax.xaxis.set_major_formatter(self.xformatter)
            v.ax.yaxis.set_major_formatter(self.yformatter)
        if self.mode == 'fx':
            v.ax.set_xlim((min(x1, x2), max(x1, x2)))
            v.ax.xaxis.set_major_formatter(self.xformatter)
            v.ax.yaxis.set_major_formatter(self.yformatter)
        if int(self.grid.get()):
            v.ax.grid()

    def get_xlim(self):
        self.data.select(self.mode)
        if self.mode == 'fx':
            x1 = float(self.data.get_value('min'))
            x2 = float(self.data.get_value('max'))
            x11 = min(x1, x2)
            x22 = max(x1, x2)
            return [x1, x2] if getattr(self, 'sign', True) else [x2, x1]
        elif self.mode == 'ft':
            span = self.data.get_seconds('span')
            t2 = datetime.now()
            dT = timedelta(0, span)
            t1 = t2 - dT
            return pylab.date2num([t1, t2])

    def set_err_mode(self):
        if self.mode == 'fx':
            self.stop = True

    def exit_cb(self, *args):
        self.stop = True
        self.root.withdraw()
        if getattr(self, 'plot_upd', False):
            self.root.after_cancel(self.plot_upd)
            self.plot_upd = None
        self.root.after(1000, self.root.quit)

    def init_io(self):
        self.io = MyAIO(self)
        self.io.add(self.plot_cb1, self.plot_cb2, self.plot_cb3, proxy.io_cb)

    def next_prev_x(self, nextx=True):
        step = float(self.data.get_value('step'))
        if getattr(self, 'sign', True):
            self.step = step
        else:
            self.step = -step
        x1, x2 = self.get_xlim()
        if not hasattr(self, 'x'):
            return min(x1, x2) if getattr(self, 'sign', True) else max(x1, x2)
        if nextx:
            if self.x == x2:
                return
        else:
            if self.x == x1:
                return
        x = self.x
        if nextx:
            x += self.step
            if self.step > 0:
                if x > x2:
                    x = x2
            else:
                if x < x2:
                    x = x2
        else:
            x -= self.step
            if self.step > 0:
                if x < x1:
                    x = x1
            else:
                if x > x1:
                    x = x1
        return x

    def plot_cb1(self):
        if self.stop:
            return False
        if self.mode == 'fx':
            self.data.select('fx')
            x = self.next_prev_x()
            if x == None:
                return False
            self.x = x
            self.data.select('x')
            k,v = list(self.data.cmds.items())[0]
            #print(k, self.x, v.dev)
            self.data.set_value(k, '%g' % self.x)
            for obj in self.data.iter_cmds2():
                self.io.qo.put(obj)
            dt = self.data.get_seconds('dt')
            self.io.qo.put(Obj(m='sleep', args=dt))
        elif self.mode == 'ft':
            self.xlim = self.get_xlim()
            self.x = self.xlim[1]
        self.data.select('y')
        for obj in self.data.iter_cmds2():
            self.io.qo.put(obj)
        return True

    def plot_cb2(self, obj, val):
        if self.stop:
            return False
        self.data.set_value(obj.cmdid, val, iter_next=False)
        return True

    def plot_cb3(self, io_start_after_idle=True):
        if self.stop:
            return False
        x = self.x
        cmds = self.data['y']
        kk = list(cmds.keys())
        fig = self.fig
        xlim = self.xlim
        pause = int(self.pause.get())
        for k,v in cmds.items():
            if not v.send:
                continue
            val = v['t'].get()
            v['t'].set('')
            if not val and self.mode != 'ft':
                #print('end_cb return')
                return False
            xx = v['xx'][-1]
            yy = v['yy'][-1]
            if val == '' and len(xx) != 0:
                v['xx'].append([])
                v['yy'].append([])
            if val != '':
                yy.append(float(val))
                xx.append(x)
            x0 = v['xx'][0]
            y0 = v['yy'][0]
            if len(x0):
                xx0 = x0[0]
                if xx0 < xlim[0]:
                    x0.pop(0)
                    y0.pop(0)
            if len(x0) == 0 and len(v['xx']) > 1:
                v['xx'].pop(0)
                v['yy'].pop(0)
        self.redraw_all()
        if self.mode == 'ft':
            dt = self.data.get_milliseconds('dt')
            self.plot_upd = self.root.after(dt, self.io_start)
            return False
        elif self.mode == 'fx':
            self.data.select('fx')
            x1, x2 = self.get_xlim()
            x = self.x + self.step/2
            if x < x1 or x > x2:
                if getattr(self, 'savefig', False):
                    self.savefig_and_exit()
                return False
            if io_start_after_idle:
                self.root.after_idle(self.io_start)
            return False

    def redraw_all(self):
        pause = int(self.pause.get())
        if pause:
            return
        xlim = self.get_xlim()
        cmds = self.data['y']
        num = 0
        for k,v in cmds.items():
            view = int(v.view.get())
            if not view:
                v.ax.set_visible(False)
                continue
            else:
                v.ax.set_visible(True)
                num = num + 1
        numi = 1
        for k,v in cmds.items():
            view = int(v.view.get())
            if not view:
                continue
            v.ax.clear()
            v.ax.change_geometry(num, 1, numi)
            numi = numi + 1
            for i in range(0, len(v['xx'])):
                xi = v['xx'][i]
                yi = v['yy'][i]
                if self.mode == 'fx':
                    v.ax.plot(xi, yi, 'b')
                    v.ax.plot(xi, yi, 'o')
                else:
                    v.ax.plot_date(xi, yi, 'b')
            self.ax_init(v)
        pylab.draw()
        self.fig.canvas.draw()

    def filesave(self, fname):
        if self.mode == 'fx':
            f = open(fname, 'w')
            cmds = self.data['y']
            vv = [v for v in cmds.values()]
            xx = list(chain(*vv[0]['xx']))
            yy = [list(chain(*v['yy'])) for v in vv]
            for i in range(0, len(xx)):
                yyi = [k[i] for k in yy]
                f.write(','.join(['%.5f' % j for j in [xx[i]] + yyi]) + '\n')
            f.close()

    def parse_savefig(self, args):
        parser = ArgumentParser()
        parser.add_argument('--savefig', nargs='*', default=[], help='save figure')
        args, extra_args = parser.parse_known_args()
        self.savefig = args.savefig
        print(self.savefig)

    def savefig_and_exit(self):
        for i in self.savefig:
            self.fig.savefig(i)
        sys.exit(0)

