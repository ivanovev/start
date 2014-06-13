#!/bin/bash

if [ $# == 0 ]; then
    echo "wrong # of args"
    exit 1
fi

path=`pwd`
name=`basename $path`
out="/tmp/${name}.tgz"
smb="/mnt/smb3"
allsubmodules="hm misc ctl fio br alt"
urlhttps="https://github.com/ivanovev/"
urlssh="git@github.com:ivanovev/"
url=$urlhttps

update_version()
{
    fver="util/version.py"
    ver=`date +%F`
    echo "new version: $ver"
    cat $fver | sed "s:^VER = [^^]*$:VER = \'$ver\':" > $fver.new
    mv $fver.new $fver
}

tgz()
{
    tar --exclude-vcs --exclude=*.swp -cvzf $out .
}

clean()
{
    rm -f *.json *.txt
    for i in `find . -name __pycache__`; do rm -rf $i; done
}

try2copy()
{
    n=`mount | grep $smb | wc -l`
    bout=`basename $out`
    if (($n == 1)); then
        cp $out $smb/start/$bout
    fi
}

commit()
{
    n=`find . -name *swp | wc -l`
    if [ $n -ne 0 ]; then
        echo 'close all vim instances, plz...'
        exit 1
    fi
    read -p "Commit message: " -e msg
    submodules=$(for i in $(git submodule foreach --quiet pwd); do basename $i; done)
    for i in $submodules
    do
        echo $i
        (cd $i && git add ./* && git commit -m "$msg" && git push)
        git rm -f --cached $i
    done
    if [ -f .gitmodules ]
    then
        git rm --cached .gitmodules
    fi
    git add freeze.bat LICENSE make.sh README.md startall.py util && git commit -m "$msg" && git push
    for i in $submodules
    do
        git add $i
    done
    if [ -f .gitmodules ]
    then
        git add .gitmodules
    fi
}

submodule_add()
{
    #url="https://github.com/ivanovev/"
    #case $1 in
    #'ssh') shift
    #    url="git@github.com:ivanovev/"
    #    ;;
    #esac
    echo "adding submodules: $@"
    for m in $@; do
        echo $m
        git submodule add -b master ${url}$m.git
    done
}

submodule_rm()
{
    for m in $@; do
        echo $m
        git submodule deinit -f $m
        git rm -f $m
        git rm -f --cached $m
        rm -rf .git/modules/$m
        rm -rf $m
    done
}

submodule()
{
    echo $@
    opt=$1
    shift
    if [ "$1" == "ssh" ]
    then
        shift
        url=$urlssh
    fi
    submodules=$@
    if [ "$1" == "all" ]; then submodules=$allsubmodules; fi
    echo $opt $url $submodules
    case $opt in
    'add') submodule_add $submodules
        ;;
    'rm') submodule_rm $submodules
        ;;
    *) echo 'invalid option: $1'
        return
        ;;
    esac
}

case $1 in
'ver')  update_version
        ;;
'clean') clean
        ;;
'tgz')  clean
        update_version
        echo '*' > acl.txt
        tgz
        try2copy
        ;;
'commit') clean
        update_version
        commit
        ;;
'pull') git pull --recurse-submodules=yes
        ;;
'doc')  doxygen $2/config.dox
        tar -C /tmp -cvzf /tmp/${2}_doc.tgz html
        ;;
'stats') find . -name '*.py' -print0 | xargs -0 cat | egrep -v '^[ \t]*$' | wc
        ;;
'submodule') shift
        submodule $@
        ;;
*)      echo 'invalid option'
        ;;
esac

