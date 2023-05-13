#!/bin/sh +x

unset ORACLE_HOME
unset LD_LIBRARY_PATH
unset PYTHONHOME

LANG=en_US.UTF-8
export LANG
NLS_LANG=AMERICAN_AMERICA.AL32UTF8
export NLS_LANG

PYTHONIOENCODING=utf-8
export PYTHONIOENCODING

HERE="$( cd "$( dirname "$0" )" && pwd )"
TGZ=$(ls $HOME/repo/deliac-env-*.tar.gz | sort | tail -1)
if [ ! -f "$TGZ" ]; then
    echo "Missing deliac-env" && exit 1
fi
ENV=$HERE/env
cd $HERE

# Sometimes Bamboo agent do not find patchelf: force PATH
PATH=/usr/local/bin/:$PATH
export PATH

rm -rf $ENV
mkdir -p $ENV
( cd $ENV && gunzip -c $TGZ | tar xf - )
$ENV/bin/fix_path.sh
if [ $? != "0" ]
then
   echo "failed to fix"
   exit 1
fi

PATH=$ENV/bin:$PATH
export PATH
LD_LIBRARY_PATH=$ENV/lib:LD_LIBRARY_PATH
export LD_LIBRARY_PATH

for requirements in requirements.txt requirements-test.txt ../code-factory/requirements.txt ../delia-mlg/requirements.txt
do
  if test -e "$requirements"
  then
    ( export CFLAGS="-I$ENV/include -I$ENV/include/openssl" \
      && export LDFLAGS="-L$ENV/lib" \
      && pip3 install --trusted-host nx-artifacts -i http://nx-artifacts:8085/artifactory/api/pypi/pypi-proxy-delia-prod/simple -r $requirements )
  fi
done

for setup in ../code-factory/setup.py ../delia-mlg/setup.py
do
  if test -e "$setup"
  then
    python3 $setup develop
  fi
done

exec invoke $*
