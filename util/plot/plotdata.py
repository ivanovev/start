
from argparse import ArgumentParser
from collections import OrderedDict as OD

from .. import Data, all_columns, c_type, msg_trace_cb
import sys
import util
import pdb

def get_cmdsx(mode):
    data = Data(name=mode, send=False)
    if mode == 'fx':
        data.add('xlabel', wdgt='entry', label='XLabel', state='readonly', trace_cb=msg_trace_cb)
        data.add('min', wdgt='spin', label='Min', value={'min':0, 'max':1, 'step':0.1}, text='0')
        data.add('max', wdgt='spin', label='Max', value={'min':0, 'max':1, 'step':0.1}, text='1')
        data.add('step', wdgt='entry', label='Step', text='0.1')
    elif mode == 'ft':
        data.add('span', wdgt='entry', label='Time span', text='5')
        data.add('spanunits', wdgt='combo', value=['s', 'm', 'h'], state='readonly', text='m')
    data.add('dt', wdgt='entry', label='Time delta', text='1')
    data.add('dtunits', wdgt='combo', value=['ms', 's', 'm', 'h'], state='readonly', text='s')
    return data

class PlotData(Data):
    def __init__(self, data=None):
        Data.__init__(self)
        if data:
            for p in data:
                self.append(p)
            self.select(0)

    def merge(self):
        self.add_page('all')
        cmdsa = self.cmds
        for i in range(0, len(self) - 1):
            cmdsi = self[0]
            for k,v in cmdsi.items():
                v.page = cmdsi.name
                v.cmd = k
                k1 = '%s.%s' % (cmdsi.name, k)
                cmdsa[k1] = v
            self.pop(0)
        self.select(0)

    def filter_cmds(self, cmdtype):
        for cmds in self:
            for k,v in cmds.items():
                if not v.send:
                    cmds.pop(k)
                    continue
                if v.wdgt != cmdtype:
                    cmds.pop(k)
                    continue

    def update_label(self, k = None):
        cmds = self.cmds
        if k == None:
            for k,v in cmds.items():
                self.update_label(k)
            return
        v = cmds[k]
        if v.wdgt == None:
            return
        if not v.label:
            if v.msg:
                v.label = v.msg
            else:
                cmds.pop(k)
                return
        if v.wdgt == 'alarm':
            v.label += '(alarm)'

    def to_args(self, mode):
        pr = []
        pr.append(sys.argv[0])
        pr.extend(['--mode', 'plot_' + mode])
        for cmds in self:
            n = cmds.name
            if len(cmds) == 0:
                return
            if len(n) == 1:
                j = 0
                for k,v in cmds.items():
                    pr.extend(['--%s_%d_page' % (n, j), v.page])
                    pr.extend(['--%s_%d_cmd' % (n, j), v.cmd])
                    pr.extend(['--%s_%d_label' % (n, j), k])
                    dev = v['dev']
                    for k1,v1 in dev.items():
                        if type(v1) == str:
                            pr.extend(['--%s_%d_%s' % (n, j, k1), v1])
                    j = j + 1
            elif len(n) == 2:
                for k,v in cmds.items():
                    pr.extend(['--%s_%s' % (n, k), v.t.get()])
        return pr

    def from_args(self, mode, apps, args):
        self.add_page('x', send=True)
        self.add_page('y', send=True)
        self.update(get_cmdsx(mode))
        columns = all_columns + ['devdata']
        parser = ArgumentParser()
        for l in [['x', 1], ['y', 10]]:
            m, n = l
            for j in range(0, n):
                parser.add_argument('--%s_%d_page' % (m, j), type=str)
                parser.add_argument('--%s_%d_cmd' % (m, j), type=str)
                parser.add_argument('--%s_%d_label' % (m, j), type=str)
                for c in columns:
                    parser.add_argument('--%s_%d_%s' % (m, j, c), type=str)
        self.select(mode)
        for k,v in self.cmds.items():
            parser.add_argument('--%s_%s' % (mode, k), type=str)
        args,extras = parser.parse_known_args(args=args)
        for k,v in self.cmds.items():
            v.text = getattr(args, '%s_%s' % (mode, k))
        def load_param(m, n):
            cmds = self.cmds
            i = '%s_%d' % (m,n)
            page = getattr(args, '%s_page' % i)
            cmd = getattr(args, '%s_cmd' % i)
            label = getattr(args, '%s_label' % i)
            if page == None or cmd == None or label == None:
                return
            v = self.add(label, page=page, cmd=cmd, label=label)
            dev = {}
            for c in columns:
                a = getattr(args, '%s_%s' % (i, c))
                if a != None:
                    dev[c] = a
            getter = util.app_gui(apps, dev[c_type], 'get_%s' % ('ctrl' if m == 'x' else 'mntr'))
            vv = getter(dev)
            vi = vv[page][cmd]
            v.update(vi)
            v.dev = dev
            v.label = label
            return True
        for l in [['x', 1], ['y', 10]]:
            m, n = l
            self.select(m)
            for j in range(0, n):
                if load_param(m, j) == None:
                    break

    def get_seconds(self, k):
        n = float(self.get_value(k))
        u = self.get_value('%sunits' % k)
        if u == 'ms':
            return n/1000
        if u == 's':
            return n
        n *= 60
        if u == 'm':
            return n
        n *= 60
        if u == 'h':
            return n
        assert True

    def get_milliseconds(self, k):
        return int(self.get_seconds(k)*1000)

