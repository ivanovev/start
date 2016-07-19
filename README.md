start
=====

Monitoring and control program.

1. How to start:  
```
    git clone .../start.git  
    cd start
    ./make.sh submodule add [hm|misc|...|all]
    python startall.py  
```

Note:
Program has support for external modules that add various devices.  
Script make.sh can be used to add various submodules.  
Here's a command that adds all submodules (available for the moment):  
```
./make.sh submodule add all
```

2. Program requires python3.5 and some extra python modules.  
How to prepare python environment:
```
    virtualenv -p python3 py3env
    source py3env/bin/activate
    pip install -r start/requirements
```

