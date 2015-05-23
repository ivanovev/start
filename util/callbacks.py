
from .tooltip import ToolTip
from .columns import *
from .server import proxy
from .misc import app_gui

import tkinter as tk

def alarm_trace_cb(k, data):
    v = data.find_v(k)
    val = v.t.get()
    if int(val, 16) == 0 if len(val) > 0 else False:
        v.w.configure(background=('green3'))
    else:
        v.w.configure(background=('red'))

def msg_trace_cb(k, data):
    v = data.find_v(k)
    msg = data.get_value(k)
    setup_tooltip(v, msg)

def telnet_io_cb(dev, cmd):
    return '%s.telnet %s %s' % (dev[c_type], dev[c_ip_addr], cmd)

def util_io_cb(dev, cmd, prefix='util'):
    cc = cmd.split()
    cc[0] = '%s.%s' % (prefix, cc[0])
    if c_ip_addr in dev:
        cc.insert(1, dev[c_ip_addr])
    return ' '.join(cc)

def dev_io_cb(dev, cmd, devtype=''):
    cc = cmd.split()
    if not devtype:
        devtype = dev[c_type]
    cc[0] = '%s.%s' % (devtype, cc[0])
    if c_ip_addr in dev:
        cc.insert(1, dev[c_ip_addr])
    return ' '.join(cc)

def dev_serial_io_cb(dev, cmd):
    cc = cmd.split()
    cc[0] = '%s.%s' % (dev['type'], cc[0])
    if c_serial in dev:
        cc.insert(1, dev[c_serial])
    return ' '.join(cc)

def cmd_serial_io_cb(dev, cmd):
    cc = cmd.split()
    cc.insert(0, '%s.cmd' % dev[c_type])
    if c_serial in dev:
        cc.insert(1, dev[c_serial])
    if c_addr in dev:
        cc.insert(2, dev[c_addr])
    return ' '.join(cc)

