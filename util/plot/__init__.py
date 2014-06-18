
import matplotlib.backends.tkagg
import matplotlib.backends.backend_tkagg

from collections import OrderedDict as OD
from .plot import Plot
from .setup import Setup

def plot_cb(mainwnd, *args):
    dlg = Setup(parent=mainwnd)
    dlg.do_modal()

def plotfx_cb(mainwnd, *args):
    dlg = Setup(parent=mainwnd, mode='fx')
    dlg.do_modal()

def plotft_cb(mainwnd, *args):
    dlg = Setup(parent=mainwnd, mode='ft')
    dlg.do_modal()

def plot_menus():
    menu_plot = OD()
    menu_plot['Plot'] = OD()
    menu_plot['Plot']['F(t)'] = plotft_cb
    menu_plot['Plot']['F(x)'] = plotfx_cb
    return menu_plot

