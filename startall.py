#!/usr/bin/env python3

import util.startup

all_submodules = []

try:
    import hm
    all_submodules.append(hm)
except:
    pass

try:
    import misc
    all_submodules.append(misc)
except:
    pass

def main():
    util.startup.startup(*all_submodules)

if __name__ == '__main__':
    main()

