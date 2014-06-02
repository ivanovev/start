
from time import time
import pdb

class CachedItem(object):
    def __init__(self, value, duration):
        self.value = value
        self.duration = duration
        self.timeStamp = time()

class CachedDict(dict):
    def get(self, fn, *args, duration=0, forceupd=False):
        key = self.key(args)
        upd = True
        if key in self and not forceupd:
            v = self[key]
            if v.duration == 0:
                upd = False
            elif v.timeStamp + v.duration > time():
                upd = False
        if upd:
            if key in self:
                self.pop(key)
            try:
                obj = fn()
                if obj != None and obj != "":
                    self[key] = CachedItem(obj, duration)
            except:
                pass
        else:
            pass
        if key in self:
            return self[key].value

    def find(self, *args):
        key = self.key(args)
        if key in self:
            return self[key].value

    def key(self, *args):
        return '.'.join(list(*args))

