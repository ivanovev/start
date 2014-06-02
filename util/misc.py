#!/usr/bin/env python

from collections import OrderedDict as OD
from types import FunctionType, ModuleType
from inspect import getargspec
from .data import Data

import os, sys, subprocess
import __main__
import pdb

def ping(ip, retries = -1):
    ret = 0
    if os.name == 'posix':
        if retries == -1: retries = 1
        ret = subprocess.call("fping -c1 -t200 %s" % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
    if os.name == 'nt':
        if retries == -1: retries = 0
        ret = subprocess.call("ping -n 1 -w 200 %s" % ip, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ret = True if ret == 0 else False
    if ret:
        return ret
    if retries > 0:
        return ping(ip, retries - 1)
    return ret

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
    return apps[0].__name__

def app_call_ret(ret):
    if ret:
        argspec = getargspec(ret)
        if len(argspec.args) == 0:
            ret = ret()
        return ret

def app_iter(apps, mname='', fname='', maxdepth=2):
    if not hasattr(app_iter, 'apps'):
        app_iter.apps = apps
    if apps == None and hasattr(app_iter, 'apps'):
        apps = app_iter.apps
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
    for m,f in app_iter(apps, 'tools', 'menus', maxdepth=1):
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
    for m,f in app_iter(apps):
        nm = m.__name__
        if nm.find('srv') == -1:
            continue
        nm = nm.split('.')[-1]
        if f.__name__.find(nm) == -1:
            continue
        k = f.__name__.replace('_', '.', 1)
        extras[k] = f
    return extras

def app_devdata(apps):
    devdata = Data()
    for m,f in app_iter(apps, '', 'devdata', maxdepth=0):
        d = f()
        devdata.update(d)
    devdata.select(0)
    return devdata

def app_gui(apps, mname, fname):
    for m,f in app_iter(apps, mname, fname):
        return app_call_ret(f)

def app_devtypes(m):
    t = [k for k,v in m.__dict__.items() if type(v) == ModuleType if k.isupper()]
    t.sort()
    return t

