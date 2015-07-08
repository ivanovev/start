#!/usr/bin/env python3

import util.startup

def main():
    all_submodules = ['hm', 'misc', 'ctl', 'br', 'fio', 'alt', 'sg', 'test', 'tmb']
    util.startup.startup(*all_submodules)

if __name__ == '__main__':
    main()

