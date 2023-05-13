#!/bin/sh +x

# =============================================================================
# PARAMETERS
# -----------------------------------------------------------------------------
COMPILER_VERSION=$1
if [ -z "$COMPILER_VERSION" ]
then
  echo "Usage:"
  echo "    deploy.sh <compiler_version>"
  exit 1
fi

# =============================================================================
# ENVIRONMENT
# -----------------------------------------------------------------------------
unset ORACLE_HOME
unset LD_LIBRARY_PATH
unset PYTHONHOME

LANG=en_US.UTF-8
export LANG
NLS_LANG=AMERICAN_AMERICA.AL32UTF8
export NLS_LANG

PYTHONIOENCODING=utf-8
export PYTHONIOENCODING

PATH=/neoxam/bin:$PATH
export PATH

# =============================================================================
# SUPPORT INSTALLATION
# -----------------------------------------------------------------------------

SUPPORT_HOMES=/neoxam/var/env
SUPPORT_VERSION=`date +'%Y%m%d%H%m'`
SUPPORT_HOME=$SUPPORT_HOMES/$SUPPORT_VERSION
BASENAME=deliac-env-$COMPILER_VERSION-linux-x86_64.tar.gz
URL=http://nx-artifacts:8085/artifactory/gp3-binaries/deliac-env/$COMPILER_VERSION/$BASENAME

rm -rf $SUPPORT_HOME
mkdir -p $SUPPORT_HOME
cd $SUPPORT_HOME
wget $URL
if [ $? != "0" ]
then
   echo "download failed"
   exit 1
fi
gunzip -c $BASENAME | tar xf -
rm -f $BASENAME

$SUPPORT_HOME/bin/fix_path.sh
if [ $? != "0" ]
then
   echo "failed to fix"
   exit 1
fi

# =============================================================================
# SUPPORT ENVIRONMENT
# -----------------------------------------------------------------------------

. /neoxam/etc/envvars

# =============================================================================
# SOURCES
# -----------------------------------------------------------------------------

SOURCES=/neoxam/src

cd $SOURCES
for project in code-factory delia-mlg dev-tools dashing adl_codegen Monkey
do
    ( cd $project && git pull )
done

# =============================================================================
# DEPENDENCE
# -----------------------------------------------------------------------------

export CFLAGS="-I$SUPPORT_HOME/include -I$ENV/include/openssl" \
&& export LDFLAGS="-L$SUPPORT_HOME/lib" \
&& pip3 install --trusted-host nx-artifacts -i http://nx-artifacts:8085/artifactory/api/pypi/pypi-proxy-delia-prod/simple \
-r $SOURCES/code-factory/requirements.txt \
-r $SOURCES/delia-mlg/requirements.txt \
-r $SOURCES/dev-tools/requirements.txt
if [ $? != "0" ]
then
   echo "install failed"
   exit 1
fi


for project in code-factory delia-mlg dev-tools
do
  cd $SOURCES/$project
  python3 setup.py clean -a
  python3 setup.py develop
done

# =============================================================================
# DEPLOYMENT
# -----------------------------------------------------------------------------

crontab -r

/neoxam/bin/supervisorctl shutdown
sleep 60
killall -u neoxam /neoxam/var/lib/ruby/2.3.0/bin/ruby

rm -rf $SUPPORT_HOMES/current
ln -sf $SUPPORT_HOME $SUPPORT_HOMES/current

neoxam migrate --noinput --traceback
neoxam collectstatic --clear --noinput --traceback

crontab /neoxam/etc/crontab.dat

