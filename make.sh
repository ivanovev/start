#!/bin/bash

if [ $# == 0 ]; then
    echo "wrong # of args"
    exit 1
fi

path=`pwd`
name=`basename $path`
tgz_file="/tmp/${name}.tgz"
deb_file="/tmp/${name}.deb"
smb="/mnt/smb4"
allsubmodules="hm misc ctl fio br alt sg test tmb nio8"
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
    tar --exclude-vcs --exclude=*.swp -cvzf $tgz_file .
}

clean()
{
    rm -f *.json *.txt
    for i in `find . -name __pycache__`; do rm -rf $i; done
}

try2copy()
{
    n=`mount | grep $smb | wc -l`
    btgz=`basename $tgz_file`
    if (($n == 1)); then
        cp $tgz_file $smb/start/$btgz
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

submodule_pull()
{
    for m in $allsubmodules; do
        (echo $m && cd $m && git pull)
    done
}

submodule()
{
    opt=$1
    shift
    if [ "$1" == "ssh" ]
    then
        shift
        url=$urlssh
    fi
    submodules=$@
    if [ "$1" == "all" ]; then submodules=$allsubmodules; fi
    #echo $opt $url $submodules
    case $opt in
    'add') submodule_add $submodules
        ;;
    'rm') submodule_rm $submodules
        ;;
    'pull') submodule_pull
        ;;
    *) echo 'invalid option: $1'
        return
        ;;
    esac
}

deb()
{
    echo "make deb"
    ver=`date +%Y%m%d`
    deb_dir="/tmp/hm_$ver"
    rm -rf $deb_dir
    mkdir $deb_dir
    mkdir $deb_dir/usr
    mkdir $deb_dir/usr/bin
    mkdir $deb_dir/usr/lib
    mkdir $deb_dir/usr/lib/python3
    mkdir $deb_dir/usr/lib/python3/dist-packages
    mkdir $deb_dir/usr/lib/python3/dist-packages/starthm
    mkdir $deb_dir/usr/share
    mkdir $deb_dir/usr/share/doc
    mkdir $deb_dir/usr/share/doc/starthm
    mkdir $deb_dir/usr/share/applications
    mkdir $deb_dir/DEBIAN
    cp hm/starthm.py $deb_dir/usr/bin/starthm
    echo '...' > $deb_dir/usr/share/doc/starthm/copyright
    echo '...' > $deb_dir/usr/share/doc/starthm/changelog.Debian
    chmod -R 755 $deb_dir/usr
    chmod -R 644 $deb_dir/usr/share/doc/starthm/copyright
    chmod -R 644 $deb_dir/usr/share/doc/starthm/changelog.Debian
    cp -r hm $deb_dir/usr/lib/python3/dist-packages/starthm
    cp -r util $deb_dir/usr/lib/python3/dist-packages/starthm
    gzip -9 $deb_dir/usr/share/doc/starthm/changelog.Debian
    cat control | sed "s/^Version: [^^]*$/Version: $ver/" > $deb_dir/DEBIAN/control
    cat hm/starthm.desktop | sed "s/^Version=[^^]*$/Version=$ver/" > $deb_dir/usr/share/applications/starthm.desktop
    chmod 644 $deb_dir/usr/share/applications/starthm.desktop
    rm -rf $deb_dir/usr/lib/python3/dist-packages/starthm/hm/.git
    rm -rf $deb_dir/usr/lib/python3/dist-packages/starthm/hm/LICENSE
    rm -rf $deb_dir/usr/lib/python3/dist-packages/starthm/hm/starthm.py
    rm -rf $deb_dir/usr/lib/python3/dist-packages/starthm/hm/starthm.desktop
    rm -rf $deb_dir/usr/lib/python3/dist-packages/starthm/util/.git
    #cp control $deb_dir/DEBIAN/control
    fakeroot dpkg-deb --build $deb_dir
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
'deb') clean
        deb
        ;;
'commit') clean
        update_version
        commit
        ;;
'pull') git pull
        $0 submodule pull
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

