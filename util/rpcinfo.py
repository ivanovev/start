
from .rpc import Rpc
from .server import MyServer, proxy

class Rpcinfo(Rpc):
    def __init__(self, do_modal=True):
        Rpc.__init__(self, title='RPC Info')

    def init_custom_layout(self):
        pass

    def argsupd_cb1(self, *args):
        srv = self.data.get_value('srv')
        m = self.get_method()
        if not srv or not m:
            return
        doc = self.cd.get(lambda: MyServer.unhexlify(proxy.call_method(srv, 'system.methodHelp', m)), srv, m)
        if doc != None:
            self.text_append(self.txt, doc, clear=True)
        else:
            self.text_append(self.txt, 'Server %s not available' % srv, clear=True, color='red')

