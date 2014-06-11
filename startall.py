#!/usr/bin/env python3

import util.startup

def main():
    all_submodules = ['hm', 'misc', 'ctl', 'fio']
    util.startup.startup(*all_submodules)

if __name__ == '__main__':
    main()

