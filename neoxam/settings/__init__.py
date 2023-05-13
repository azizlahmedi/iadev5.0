# -*- coding: utf-8 -*-
import os



from configurations import Configuration


from neoxam.adltrack.configurations import ADLTrack
from neoxam.backport.configurations import Backport
from neoxam.champagne.configurations import Champagne
from neoxam.delivery.configurations import Delivery
from neoxam.eclipse.configurations import Eclipse
from neoxam.factory_app.configurations import Factory
from neoxam.gpatcher.configurations import Gpatcher
from neoxam.harry.configurations import Harry
from neoxam.initial.configurations import InitialCommit
from neoxam.settings import core, apps, deps
from neoxam.versioning.configurations import Versioning
from neoxam.webintake.configurations import Webintake


class Site(
    deps.CrispyForms,
    deps.RESTFramework,
    deps.Supervisor,
    apps.Locks,
    apps.UI,
    apps.Commons,
    apps.Elastic,
    Backport,
    apps.Backport,
    Gpatcher,
    ADLTrack,  # before celery
    apps.ADLTrack,
    Versioning,
    Harry,
    apps.Harry,
    Webintake,
    apps.Webintake,
    InitialCommit,
    apps.Versioning,
    apps.ScrumCards,
    apps.ScrumReport,
    Champagne,  # before celery
    apps.Champagne,
    Delivery,
    apps.Delivery,
    Eclipse,
    apps.Eclipse,
    Factory,  # before celery
    apps.Factory,
    apps.SCM,
    deps.Celery,
    deps.Sendfile,
    core.Core,  # core comes first
    Configuration,
):
    pass



class Development(Site):
    DEBUG = True
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print('hi')
    @property
    def ROOT(self):
        return os.path.join(self.BASE_DIR, 'data')

    @property
    def ALLOWED_HOSTS(self):
        allowed_host = []
        allowed_host.extend(super(Development, self).ALLOWED_HOSTS)
        allowed_host.append('127.0.0.1',)
        allowed_host.append('10.53.1.149',)
        return allowed_host

    INTERNAL_IPS = ['127.0.0.1', ]
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    SECRET_KEY = '#bdat+p!3toxgjx8lhag-r^z@%s&w1i$5l&%1@e_8!0lqjq$b^'
    DATABASE_DEFAULT_PASSWORD = 'neoxam_passwd'
    RABBITMQ_PASSWORD = 'neoxam_passwd'
    SENDFILE_BACKEND = 'sendfile.backends.development'

    @property
    def FACTORY_SETTINGS(self):
        return os.path.join(self.BASE_DIR, 'neoxam', 'factory_app', 'tests', 'factory.cfg')
    
    


class Test(Development):
    print('gg')
    CRESUS_DEFAULT_PLAN = None
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    
    VERSIONING_VALID_COMPILATION_PK = 0

    @property
    def ROOT(self):
        return os.path.join(self.BASE_DIR, 'data-test')

    @property
    def DATABASE_DEFAULT_HOST(self):
        if os.getenv('bamboo_buildKey', False):
            return '10.244.134.58'  # delia-db01
        return 'localhost'

    @property
    def DATABASES(self):
        databases = super(Test, self).DATABASES
        databases['versioning'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(self.ROOT, 'var', 'db', 'versioning.db'),
        }
        return databases


class Production(Site):
    ROOT = '/neoxam'
    DEBUG = False
    SENDFILE_BACKEND = 'sendfile.backends.nginx'

    EMAIL_HOST = 'kanoux.bams.corp'
    EMAIL_PORT = 25

    def STATIC_ROOT(self):
        return os.path.join(self.ROOT, 'var', 'www', 'static')

    DATABASE_DEFAULT_HOST = '10.215.39.197'  # iadev-tools

    @property
    def DATABASE_DEFAULT_PASSWORD(self):
        return self.decrypt('IjRjRkxYY1NuSk4tUyI:1aZDeJ:kkBBCGJ39Vg0r9_KxDN3F-sCeNA')

    RABBITMQ_HOST = '10.215.39.197'  # iadev-tools

    @property
    def RABBITMQ_PASSWORD(self):
        return self.decrypt('InlIeGc1eGFVeGhEZyI:1aZDgI:GJ4JYVOw_m2iDiM26IkHb0pzpZw')

    @property
    def JIRA_USERNAME(self):
        return self.decrypt('ImlhLWRldi1weXRob24i:1bw6Z2:7p6vWFDz6yjW40T4WKUhEXBCgqU')

    @property
    def JIRA_PASSWORD(self):
        return self.decrypt('ImNWLXIzUzNaLUJfUyI:1bw6Zf:FVahFtYUNO3lvg9d5Ga0IxmR8F0')

    @property
    def SVN_USERNAME(self):
        return self.decrypt('ImNpcyI:1bwpvd:otICqYqWM-2SOPSy0ULSDPDxbiE')

    @property
    def SVN_PASSWORD(self):
        return self.decrypt('Ik50aWMyMDA3Ig:1bwpw8:N09tndn_6DCf2DhhTncM2rTxU_U')

    @property
    def SECRET_KEY(self):
        with open(os.path.join(self.ROOT, 'etc', 'secret.key'), 'r', encoding='utf-8') as fd:
            return fd.readline().rstrip('\n\r')

    VERSIONING_ELASTICSEARCH_URL = 'http://iadev-tools:9200'

    ECLIPSE_ELASTICSEARCH_URL = VERSIONING_ELASTICSEARCH_URL
    ECLIPSE_PUBLISH_URL = 'http://iadev-tools/eclipse/downloads/'



