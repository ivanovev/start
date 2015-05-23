
from .tooltip import ToolTip
import tkinter as tk
import pdb

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

def setup_tooltip(v, msg):
    if v.w:
        if not v.tip:
            v.tip = ToolTip(v.w, msg=msg, follow=True, delay=0)
        else:
            v.tip.msgVar.set(msg)
            v.visible = 0

