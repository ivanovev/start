start
=====

Monitoring and control program for various devices.

1. How to start:  
    git clone .../start.git  
    ./make.sh submodule add [hm|misc|...]  
    python startall.py  

Note:
List of existing program extension modules is available on the project page at github.
Script make.sh simply adds submodule to the source tree, it's also possible to
download and add them manually. Here's a command that adds all submodules:
./make.sh submodule add all

2. Program requires python3.4 and some extra python modules. How to prepare python environment:
    virtualenv -p python3.4 py34env
    source py34env/bin/activate
    pip install -r start/requirements.txt --pre

