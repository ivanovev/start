start
=====

Monitoring and control program for various devices.

1. How-to start:  
    git clone .../start.git  
    ./make.sh submodule add [hm|misc|...]  
    python startall.py  

Note:
List of existing program extension modules is available on project page at github.
Script make.sh simply adds submodule to the source tree, it's also possible to
download and add modules manually. It's also possible to add all modules vith short command:  
./make.sh submodule add all

2. Requirements:  
    python3  
    matplotlib  
    numpy  
    pyserial  

