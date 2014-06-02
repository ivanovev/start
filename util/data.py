
from collections import OrderedDict as OD
from types import FunctionType
import pdb

def find_from_table(t, x, val=True):
    t1 = None
    if val:
        t1 = t
    else:
        t1 = {}
        for k,v in t.items():
            t1[v] = k
    z = t1.keys()
    z = list(z)
    z.sort()
    if x < min(z):
        return t1[min(z)]
    if x > max(z):
        return t1[max(z)]
    for i in z:
        if x == i:
            return t1[i]
    x1 = min(z)
    x2 = max(z)
    for j in z:
        if x1 < j and j < x:
            x1 = j
        if x < j and j < x2:
            x2 = j
    return t1[x1] + (t1[x2] - t1[x1])*(x - x1)/(x2 - x1)

def find_key(d, val):
    ival = None
    for k,v in d.items():
        if v == val:
            return k
        if type(v) == int:
            try:
                if v == int(val):
                    return k
            except:
                pass
    if val in list(d.keys()):
        return val

class Obj(dict):
    def __getattribute__(self, k):
        if k in self:
            return self[k]
        try:
            return dict.__getattribute__(self, k)
        except:
            pass

    def __setattr__(self, k, v):
        self[k] = v

    def __deepcopy__(self, memo):
        return Obj(dict(self))

class Data(list):
    def __init__(self, name=None, cmds=None, send=None, buttons=None, io_cb=None):
        list.__init__(self)
        self.cur = 0
        self.send = send
        self.buttons = buttons
        if name or cmds:
            self.add_page(name, cmds, send)
        if io_cb:
            self.io_cb = io_cb
    
    def add_page(self, name='', cmds=None, send=None, pos=None):
        c1 = cmds if cmds else OD()
        c1.name = name
        if send != None:
            c1.send = send
        if pos == None:
            self.append(c1)
        else:
            self.insert(pos, c1)
        self.select(len(self) - 1 if pos == None else pos)

    def update(self, newdata):
        for i in newdata:
            self.append(i)

    def remove_page(self, k=None):
        if k:
            self.select(k)
        self.pop(self.cur)
        self.select(self.cur if self.cur < len(self) else self.cur - 1)

    def add(self, k, **kwargs):
        cmds = self[self.cur]
        v = Obj(**kwargs)
        if v.send == None:
            if hasattr(cmds, 'send'):
                v.send = cmds.send
            elif hasattr(self, 'send'):
                v.send = self.send
        if hasattr(self, 'io_cb'):
            v.io_cb = self.io_cb
        cmds[k] = v
        return v

    def clear(self, k):
        i = self.find_by_name(k)
        old = self[i]
        self[i] = OD()
        self[i].name = old.name
        self.select(i)

    def __contains__(self, k):
        return self[k] != None

    def __getitem__(self, i):
        if type(i) == int:
            if i < len(self):
                return list.__getitem__(self, i)
        elif type(i) == str:
            i = self.find_by_name(i)
            if i != None:
                return self[i]

    def __str__(self):
        return '\n'.join(['%s:%s' % (j, str(i[j])) for i in self for j in i])

    def iterkw(self, prefix1, prefix2=None):
        if prefix2 == None:
            prefix = prefix1
        else:
            prefix = '%s.%s' % (prefix1, prefix2)
        if prefix in self:
            yield prefix, self[prefix]
            return
        for i in self:
            if i.name.find(prefix) == 0:
                yield i.name, i

    def find_by_name(self, name):
        for i in range(0, len(self)):
            if self[i].name == name:
                return i

    def bind_tab_cb(self, tabs, cb=None):
        def tab_cb(evt):
            self.select(evt.widget.tabs().index(evt.widget.select()))
            if cb != None:
                cb()
        tabs.bind('<<NotebookTabChanged>>', lambda evt: tab_cb(evt))

    def select(self, n):
        if type(n) == int:
            if 0 <= n and n <= len(self):
                self.cur = n
                self.cmds = self[self.cur]
        elif type(n) == str:
            n = self.find_by_name(n)
            return self.select(n)
        else:
            print('select error %d of %d' % (n, len(self)))
        return self

    def items(self):
        return self[self.cur].items()

    def keys(self):
        return self[self.cur].keys()

    def values(self):
        return self[self.cur].values()

    def get_value(self, k):
        if k in self.cmds:
            v = self.cmds[k]
        else:
            v = self.find_v(k)
        if not v:
            print('get_value: %s not found' % k)
            return
        if not v.t:
            if v.text != None:
                return str(v.text)
            return
        g = v.t.get()
        if g == '':
            return g
        if v.value and v.wdgt != 'spin':
            if type(v.value) in [dict, OD]:
                g = v.value[g]
        return g

    def get_attribute(self, k, a, init):
        v = self.find_v(k)
        if not v:
            print('get_attribute: %s not found' % k)
            return
        if hasattr(v, a):
            return getattr(v, a)
        if type(init) == FunctionType:
            va = init()
            setattr(v, a, va)
            return va

    def set_attribute(self, k, a, val):
        v = self.find_v(k)
        if not v:
            print('get_attribute: %s not found' % k)
            return
        setattr(v, a, val)

    def find_v(self, k):
        if k in self.cmds:
            return self.cmds[k]
        for p in self:
            if k in p:
                return p[k]
        if hasattr(self, k):
            return getattr(self, k)
        fbn = self.find_by_name(k)
        if fbn != None:
            return self[fbn]

    def trace_cb(self, k, v):
        if v.l:
            v.l.set('1')
        if v.trace_cb:
            v.trace_cb(k, self)

    def trace_add(self, k, v):
        if v.t and not v.cbname:
            v.cbname = v.t.trace_variable('w', lambda var, val, mode, k=k, v=v: self.trace_cb(k,v))

    def trace_delete(self, k, v):
        if v.cbname:
            v.t.trace_vdelete('w', v.cbname)
            v.pop('cbname')

    def set_value(self, k, s, set_send=True, skip_trace_cb=False):
        if k == 'tmp':
            return
        if s == '':
            return
        v = self.find_v(k)
        if not v:
            print('set_value: %s not found' % k)
            return
        if not v.t:
            v.text = s
            return
        s_orig = s
        if v.fmt_cb:
            s = v.fmt_cb(s, read=True)
        if v.value and v.wdgt != 'spin':
            kv = v.value
            if type(kv) in [dict, OD]:
                s = find_key(kv, s)
        if s == None:
            return
        trace = v.cbname
        if skip_trace_cb:
            self.trace_delete(k, v)
        v.t.set(s)
        if trace and skip_trace_cb:
            self.trace_add(k, v)
        if v.l and set_send:
            v.l.set(1)
        kk = list(self.cmds.keys())
        if k not in kk:
            return
        if kk.index(k) == len(self.cmds) - 1:
            return
        k = kk[kk.index(k) + 1]
        v = self.cmds[k]
        if not v.send and v.fmt_cb:
            self.set_value(k, s_orig)

    def get_dev(self, k):
        v = self.find_v(k)
        if v:
            if v.dev:
                return v.dev
        if hasattr(self, 'dev'):
            return self.dev

    def do_cmds(self, qo, read=True):
        cmds = self.cmds
        if not read:
            for k,v in cmds.items():
                if not v.send and v.fmt_cb:
                    val = self.get_value(k)
                    v.fmt_cb(val, read)
        for k,v in cmds.items():
            if not v.send:
                continue
            if v.l.get() != '1' if v.l else False:
                continue
            cmd = v.cmd if v.cmd else k
            val = None
            dev = self.get_dev(k)
            if not read:
                val = self.get_value(k)
                if val == '': continue
                if v.fmt_cb:
                    val = v.fmt_cb(val, read)
                if type(val) == int: val = str(val)
            if v.cmd_cb:
                cmd = v.cmd_cb(dev, cmd, val)
            elif val != None:
                cmd = ' '.join([cmd, val])
            if v.io_cb:
                cmd = v.io_cb(dev, cmd)
            cmd = ' '.join([k, cmd])
            if type(cmd) == str:
                qo.put(cmd)
            elif cmd == None and v.l:
                v.l.set(0)

    @staticmethod
    def spn(min_value, max_value, step=1):
        return {'min':min_value, 'max':max_value, 'step':step}

    def update_combo(self, v, labels, enable):
        for k1,v1 in v.radio.items():
            v1.state(['!disabled' if (enable if k1 in labels else not enable) else 'disabled'])

    def print_hex(self):
        self.select('hex')
        for k,v in self.cmds.items():
            text = v.text if v.text else '0' * int(self.sz/4)
            msg = v.msg if v.msg else ''
            s = '|'.join([k, text, msg])
            print(s)

    def print_bin(self):
        for p in self:
            if p.name[0] == 'R':
                nprev = ''
                for k,v in p.items():
                    if v.name == nprev:
                        continue
                    nprev = v.name
                    r,b = k.split('.')
                    grayed = '1' if v.state else ''
                    msg = v.msg[2:] if v.msg else ''
                    s = '|'.join([r,b, v.name, grayed, msg])
                    print(s)

