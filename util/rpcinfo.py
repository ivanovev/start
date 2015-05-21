
from .rpc import Rpc
from .server import MyServer, proxy

class Rpcinfo(Rpc):
    def __init__(self, do_modal=True):
        Rpc.__init__(self, title='RPC Info')
        self.cdkey = 'hlp'
        self.cdkeym = 'system.methodHelp'

    def init_custom_layout(self):
        pass

    def argsupd_cb3(self):
        srv = self.data.get_value('srv')
        doc = proxy.cd.get(lambda: obj, srv, self.m, self.cdkey)
        if doc:
            self.text_append(self.txt, doc, clear=True)
        else:
            self.text_append(self.txt, 'Failed to get method help for %s from server %s' % (self.m, srv), clear=True, color='red')
        self.lb.config(state='normal')

