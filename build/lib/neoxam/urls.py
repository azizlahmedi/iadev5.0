# -*- coding: utf-8 -*-
from django.urls import path, include
from django.urls import re_path
from django.contrib import admin
from neoxam.factory_app import views as factory_views

import neoxam.adltrack.urls
import neoxam.backport.urls
import neoxam.commons.urls
import neoxam.eclipse.urls
import neoxam.factory_app.urls
import neoxam.gpatcher.urls
import neoxam.initial.urls
import neoxam.versioning.urls
import neoxam.webintake.urls

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^adltrack/', include(neoxam.adltrack.urls)),
    re_path(r'^factory/', include(neoxam.factory_app.urls)),
    re_path(r'^backport/', include(neoxam.backport.urls)),
    re_path(r'^gpatcher/', include(neoxam.gpatcher.urls)),
    re_path(r'^initial/', include(neoxam.initial.urls)),
    re_path(r'^webintake/', include(neoxam.webintake.urls)),
    re_path(r'^versioning/', include(neoxam.versioning.urls)),
    re_path(r'^eclipse/', include(neoxam.eclipse.urls)),
    re_path(r'^', include(neoxam.commons.urls)),
    
    
    
]
