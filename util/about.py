
from collections import OrderedDict as OD
from .info import Info
from .version import get_version
from .misc import app_name, app_alldevdata
from .server import proxy
from .columns import *

class About(Info):
    def __init__(self, apps):
        self.apps = apps
        Info.__init__(self, title='About')

    def init_data(self):
        self.tree_add_lvl0(self.tree, ['Version', get_version()])
        self.tree_add_lvl0(self.tree, ['Local server', proxy.get_local_srv()])
        self.tree_add_lvl0(self.tree, ['Sources', 'https://github.com/ivanovev/start.git'])
        self.tree_add_lvl0(self.tree, ['Binaries', 'ftp://85.141.12.78/pub/start/%s/' % app_name(self.apps)])
        total = 0
        devdata = app_alldevdata(self.apps)
        for p in devdata:
            devtypes = p[c_type].value
            t1 = len(devtypes)
            total += t1
            self.tree_add_lvl0(self.tree, [p.name, '(%d)' % t1])
            for x in devtypes:
                self.tree_add_lvl1(self.tree, p.name, ['%d' % (devtypes.index(x)+1), x], expand=False)
        self.tree_add_lvl0(self.tree, ['total:', '%d' % total])
