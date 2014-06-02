#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

from .about import About
from .mainwnd import Mainwnd
from .monitor import Monitor
from .control import Control
from .rpcinfo import Rpcinfo
from .columns import *
from .acl import Acl
from .rpc import Rpc
from .data import Data
from .server import proxy
from . import app_name, app_gui, app_iter, get_default_filename
try:
    from .plot import Plot
except:
    pass

from argparse import ArgumentParser

import os, sys, pdb, types
import zipimport, zlib
import socketserver

sys.dont_write_bytecode = True

def parse_dev(apps, args):
    dev = {}
    for i in all_columns:
        if getattr(args, i) != None:
            dev[i] = getattr(args, i)
    if args.devdata != None:
        dev['devdata'] = args.devdata
    if len(dev) >= 3:
        return dev

def parse_mode(mode, apps, args, extra_args):
    if mode == 'gui':
        return Mainwnd(apps, args.fopen)
    if mode == 'about':
        return About(apps)
    if mode == 'acl':
        return Acl()
    if mode == 'rpc':
        return Rpc()
    if mode == 'rpcinfo':
        return Rpcinfo()
    if mode.find('plot') == 0:
        m0,m1 = mode.split('_')
        return Plot(mode=m1, apps=apps, args=extra_args)
    dev = parse_dev(apps, args)
    if mode == 'monitor':
        getter = app_gui(apps, dev[c_type], 'get_mntr')
        mntr = getter(dev)
        return Monitor(data=mntr, dev=dev)
    if mode == 'control':
        getter = app_gui(apps, dev[c_type], 'get_ctrl')
        ctrl = getter(dev)
        app = Control(data=ctrl, dev=dev)
        if not ctrl.buttons:
            app.add_buttons_read_write_close()
        return app
    if dev:
        startup_cb = app_gui(apps, dev[c_type], 'startup_cb')
        if startup_cb:
            app = startup_cb(apps, mode, dev)
            if app:
                return app
    for m,f in app_iter(apps, '', 'startup_cb'):
        app = f(apps, mode, dev)
        if app:
            return app

def startup(*args):
    apps = []
    for i in args:
        if type(i) == str:
            i = __import__(i, fromlist=[i])
        if type(i) == types.ModuleType:
            apps.append(i)
        else:
            exit(1)
    parser = ArgumentParser()
    mode=['gui', 'srv']
    parser.add_argument('--mode', nargs='*', default=mode, help='startup mode')
    name = get_default_filename(apps)
    parser.add_argument('--fopen', type=str, default=name, help='open filename, default %s' % name)
    parser.add_argument('--port', type=int, default=proxy.port, help='server port, default %d' % proxy.port)
    for i in all_columns:
        parser.add_argument('--%s' % i, type=str, help='device %s' % i)
    parser.add_argument('--devdata', type=str, help='device devdata')
    args, extra_args = parser.parse_known_args()
    if len(args.mode) == 0:
        return
    proxy.port = args.port
    srvexec = os.getenv('srvexec')
    mode = args.mode[0]
    if 'call' in args.mode:
        n = sys.argv.index(mode)
        args = sys.argv[n+1:]
        print('result:', proxy.call_server(*tuple(args), apps=apps))
        return
    srvalive = proxy.alive()
    if 'srv' in args.mode:
        if not srvalive:
            os.environ['srvexec'] = '1'
            if len(args.mode) == 1:
                proxy.start_server(apps)
            else:
                proxy.start_server_process()
        args.mode.pop(args.mode.index('srv'))
    if not srvexec and srvalive:
        proxy.start_process(*sys.argv)
        return
    for mode in args.mode:
        app = parse_mode(mode, apps, args, extra_args)
        if app:
            app.center()
            app.root.mainloop()
            break

