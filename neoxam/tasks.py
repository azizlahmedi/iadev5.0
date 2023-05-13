# -*- coding: utf-8 -*-
import os

from delia_commons.tasks import ContextWrapper, prompt
from invoke import task


def create_tree(cw, root):
    paths = (
        'var/run',
        'var/log',
        'var/scm',
        'var/db',
        'var/www/static',
        'tmp',
    )
    for path in paths:
        cw.run('mkdir -p ' + os.path.join(root, path))


def setup(ctx):
    cw = ContextWrapper(ctx)
    create_tree(cw, 'data')
    cw.run('neoxam migrate --traceback --noinput')
    cw.run('neoxam loaddata repositories --traceback')
    cw.run('neoxam createsuperuser --username=admin --email=olivier.mansion@neoxam.com', pty=True)


@task
def resetdb(ctx):
    answer = prompt('Do you really want to reset the database?', default='n', validate=r'^[yYnN]$')
    if answer in 'yY':
        reset_psql()
        setup(ctx)


@task
def reset_all(ctx):
    answer = prompt('Do you really want to reset the project?', default='n', validate=r'^[yYnN]$')
    if answer in 'yY':
        reset_psql(ctx)
        reset_rabbitmq(ctx)
        ctx.run('rm -rf data')
        setup(ctx)


@task
def reset_psql(ctx):
    cw = ContextWrapper(ctx)
    queries = [
        'DROP DATABASE IF EXISTS neoxam_db',
        'DROP DATABASE IF EXISTS test_neoxam_db',
        'DROP USER IF EXISTS neoxam_user',
        'CREATE USER neoxam_user WITH PASSWORD \'neoxam_passwd\'',
        'CREATE DATABASE neoxam_db WITH ENCODING=\'UTF8\' LC_COLLATE=\'en_US.UTF-8\' LC_CTYPE=\'en_US.UTF-8\' TEMPLATE=template0',
        'GRANT ALL PRIVILEGES ON DATABASE neoxam_db TO neoxam_user',
        # Test
        'ALTER USER neoxam_user CREATEDB',
    ]
    for query in queries:
        cw.run('sudo su - postgres -c "psql -d postgres -c \\"%s\\""' % query)


@task
def reset_rabbitmq(ctx):
    cw = ContextWrapper(ctx)
    cw.run('sudo rabbitmqctl delete_user neoxam_user', warn=True)
    cw.run('sudo rabbitmqctl delete_vhost neoxam_vhost', warn=True)
    cw.run('sudo rabbitmqctl add_user neoxam_user neoxam_passwd')
    cw.run('sudo rabbitmqctl set_user_tags neoxam_user administrator')
    cw.run('sudo rabbitmqctl add_vhost neoxam_vhost')
    cw.run('sudo rabbitmqctl set_permissions -p neoxam_vhost neoxam_user ".*" ".*" ".*"')


@task
def flake8(ctx):
    cw = ContextWrapper(ctx)
    cw.run('flake8 --max-line-length=120 --exclude=*/*/migrations/* .')


@task
def bamboo(ctx):
    root = 'data-test'
    cw = ContextWrapper(ctx)
    cw.run('python3 setup.py develop')
    cw.run('rm -rf ' + root)
    create_tree(cw, root)
    cw.run('DJANGO_CONFIGURATION=Test neoxam migrate --traceback --noinput')
    cw.run('DJANGO_CONFIGURATION=Test neoxam migrate --traceback --noinput --database versioning')
    cw.run('rm -f junit.xml')
    cw.run('DJANGO_CONFIGURATION=Test pytest --junit-xml=junit.xml neoxam/*/tests')
