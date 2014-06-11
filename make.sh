#!/bin/bash

if [ $# == 0 ]; then
    echo "wrong # of args"
    exit 1
fi

path=`pwd`
name=`basename $path`
out="/tmp/${name}.tgz"
smb="/mnt/smb3"

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
    for i in `git submodule --quiet foreach pwd`
    do
        echo $i
        (cd $i && git add ./* && git commit -m "$msg" && cd ..)
    done
    for i in `git submodule --quiet foreach pwd`; do echo `basename $i` >> .gitignore; done
    echo .gitmodule >> .gitignore
    git add . && git commit -m "$msg"
    rm -f .gitignore
    #git add freeze.bat LICENSE make.sh README.md startall.py util && git commit -m "$msg"
    #git push --recurse-submodules=on-demand origin HEAD:master
    git push --recurse-submodules=on-demand
}

submodule_add()
{
    url="https://github.com/ivanovev/"
    case $1 in
    'ssh') shift
        url="git@github.com:ivanovev/"
        ;;
    esac
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
    done
}

submodule()
{
    echo $@
    case $1 in
    'add') shift
        submodule_add $@
        ;;
    'rm') shift
        submodule_rm $@
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

