
from .data import Data
from .server import proxy
from .misc import app_gui
from .tooltip import ToolTip
import tkinter as tk

c_name = 'name'
c_type = 'type'
c_server = 'server'
c_ip_addr = 'ip_addr'
c_altname = 'altname'
c_serial = 'serial'
c_addr = 'addr'
c_spi = 'spi'
c_gpio = 'gpio'
c_refin = 'refin'
cc = list(filter(lambda x: x.find('c_') == 0, dir()))
all_columns = [c[2:] for c in cc]

def get_columns(add=[]):
    return [c_name, c_type, c_server] + add

def serial_click_cb(k, data):
    srv = data.get_value(c_server)
    try:
        res = proxy.call_method(srv, 'srv.get_serials')
        s = res.split()
        v = data.find_v('serial')
        v.w.configure(values=s)
    except:
        pass

def setup_tooltip(v, msg):
    if v.w:
        if not v.tip:
            v.tip = ToolTip(v.w, msg=msg, follow=True, delay=0)
        else:
            v.tip.msgVar.set(msg)
            v.visible = 0

def dev_trace_cb(k, data):
    val = data.get_value('type')
    if not val:
        return
    columns = app_gui(None, val, 'columns')
    if columns == None:
        columns = list(data.cmds.keys())
    cmds = data.cmds
    if columns != None:
        i = 0
        l = ['lw', 'w']
        for k,v in cmds.items():
            if not k in columns:
                for j in l:
                    v[j].grid_forget()
            else:
                for j in l:
                    v[j].grid(column=l.index(j), row=i, sticky=tk.NSEW, pady=v.pady)
            i = i + 1
    tt = app_gui(None, val, 'tooltips')
    for k,v in cmds.items():
        if k in tt.keys() if tt else False:
            msg = tt[k]
            setup_tooltip(v, msg)
        else:
            if 'tip' in v:
                v['tip'].visible = -1

def get_devdata(name, columns, devtypes):
    data = Data(name)
    data.add(c_name, label=c_name, wdgt='entry', text='new')
    data.add(c_type, label=c_type, wdgt='combo', state='readonly', value=devtypes, trace_cb=dev_trace_cb)
    data.add(c_server, label=c_server, wdgt='entry', text=proxy.get_local_srv())
    if c_ip_addr in columns:
        data.add(c_ip_addr, label=c_ip_addr, wdgt='entry', text='192.168.0.1')
    if c_altname in columns:
        data.add(c_altname, label=c_altname, wdgt='entry', text='fir0')
    if c_serial in columns:
        data.add('serial', label='serial', wdgt='combo', value=['ttyUSB0', 'ttyS0'], click_cb=lambda k: serial_click_cb(k, data))
    if c_addr in columns:
        data.add('addr', label='addr', wdgt='entry')
    if c_spi in columns:
        data.add(c_spi, label='spi', wdgt='entry', text='0')
    if c_gpio in columns:
        data.add(c_gpio, label='gpio', wdgt='entry', text='0')
    if c_refin in columns:
        data.add(c_refin, label='refin', wdgt='entry', text='26', msg='REFin, MHz')
    return data

