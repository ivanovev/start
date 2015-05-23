#!/usr/bin/env python

from collections import OrderedDict as OD
from types import FunctionType, ModuleType
from inspect import getargspec

from .columns import *
from .data import Data
from .server import proxy

import os, sys, subprocess
import __main__
import pdb

'''
def ping(ip, retries = -1):
    ret = 0
    if os.name == 'posix':
        if retries == -1: retries = 1
        ret = subprocess.call("fping -c1 -t500 %s" % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if os.name == 'nt':
        if retries == -1: retries = 0
        ret = subprocess.call("ping -n 1 -w 200 %s" % ip, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = True if ret == 0 else False
    if ret:
        return ret
    if retries > 0:
        return ping(ip, retries - 1)
    return ret
'''

def app_name(apps):
    if hasattr(__main__, '__file__'):
        name = __main__.__file__
        name = name.replace('start', '')
        name = name.replace('.py', '')
        return name
    if getattr(sys, 'frozen', False):
        # frozen
        name = os.path.basename(sys.executable)
        name = name.replace('start', '')
        name = name.replace('.exe', '')
        return name
    a = apps[0]
    if type(a) == str:
        return a
    elif type(a) == ModuleType:
        return a.__name__
    return ''

def app_call_ret(ret):
    if ret:
        argspec = getargspec(ret)
        if len(argspec.args) == 0:
            ret = ret()
        return ret

def iter_apps(apps, mname='', fname='', maxdepth=2):
    if not hasattr(iter_apps, 'apps'):
        iter_apps.apps = apps
    if apps == None and hasattr(iter_apps, 'apps'):
        apps = iter_apps.apps
    for a0 in apps:
        n0 = a0.__name__
        for n1 in dir(a0):
            a1 = getattr(a0, n1)
            if type(a1) == FunctionType:
                if mname and n0 != mname:
                    continue
                if fname and n1 != fname:
                    continue
                yield a0, a1
                continue
            if type(a1) != ModuleType:
                continue
            if maxdepth == 0:
                continue
            if n1 not in ['gui', 'srv', 'tools']:
                continue
            for n2 in dir(a1):
                a2 = getattr(a1, n2)
                if type(a2) == FunctionType:
                    if mname and n1 != mname:
                        continue
                    if fname and n2 != fname:
                        continue
                    yield a1, a2
                    continue
                if type(a2) != ModuleType:
                    continue
                if maxdepth == 1:
                    continue
                for n3 in dir(a2):
                    a3 = getattr(a2, n3)
                    if type(a3) != FunctionType:
                        continue
                    if mname and n2 != mname:
                        continue
                    if fname and n3 != fname:
                        continue
                    yield a2, a3
                    continue

def app_tools(apps):
    tools = OD()
    for m,f in iter_apps(apps, 'tools', 'menus', maxdepth=1):
        if len(tools):
            tools['separator%d' % len(tools)] = None
        f = app_call_ret(f)
        tools.update(f)
    kk = list(tools.keys())
    if len(kk):
        if tools[kk[-1]] == None:
            tools.pop(kk[-1])
    return tools

def app_srv(apps):
    extras = OD()
    for m,f in iter_apps(apps):
        nm = m.__name__
        if nm.find('srv') == -1:
            continue
        nm = nm.split('.')[-1]
        if f.__name__.find(nm) != 0:
            continue
        k = f.__name__.replace('_', '.', 1)
        extras[k] = f
    return extras

def app_alldevdata(apps, mname=''):
    devdata = Data()
    for m,f in iter_apps(apps, mname.lower(), 'devdata', maxdepth=0):
        d = f()
        devdata.update(d)
    devdata.select(0)
    return devdata

def app_gui(apps, mname, fname):
    for m,f in iter_apps(apps, mname, fname):
        return app_call_ret(f)

def app_devtypes(m):
    t = [k for k,v in m.__dict__.items() if type(v) == ModuleType if k.isupper()]
    t.sort()
    return t

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

def serial_click_cb(k, data):
    srv = data.get_value(c_server)
    try:
        res = proxy.call_method(srv, 'srv.get_serials')
        #print(srv, res)
        s = res.split()
        v = data.find_v('serial')
        v.w.configure(values=s)
    except:
        pass

def app_devdata(name, columns, devtypes):
    data = Data(name)
    data.add(c_name, label=c_name, wdgt='entry', text='new')
    data.add(c_type, label=c_type, wdgt='combo', state='readonly', text='', value=devtypes, trace_cb=dev_trace_cb)
    data.add(c_server, label=c_server, wdgt='entry', text=proxy.get_local_srv())
    if c_ip_addr in columns:
        data.add(c_ip_addr, label=c_ip_addr, wdgt='combo', value=['192.168.0.1', '127.0.0.1'], text='192.168.0.1')
    if c_altname in columns:
        data.add(c_altname, label=c_altname, wdgt='entry', text='fir0')
    if c_serial in columns:
        data.add('serial', label='serial', wdgt='combo', value=['ttyUSB0', 'ttyS0'], click_cb=lambda k: serial_click_cb(k, data))
    if c_addr in columns:
        data.add('addr', label='addr', wdgt='entry', text='0')
    if c_spi in columns:
        data.add(c_spi, label='spi', wdgt='entry', text='0')
    if c_gpio in columns:
        data.add(c_gpio, label='gpio', wdgt='entry', text='0')
    if c_refin in columns:
        data.add(c_refin, label='refin', wdgt='entry', text='26', msg='REFin, MHz')
    return data

