# -*- coding: utf-8 -*-
from django.conf import settings
from django.urls import re_path
from django.conf.urls import  include
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns

from neoxam.adltrack import api, views

commit_list = api.CommitViewSet.as_view({
    'get': 'list',
})
commit_detail = api.CommitViewSet.as_view({
    'get': 'retrieve',
})
commit_version_list = api.ProcedureVersionViewSet.as_view({
    'get': 'list',
})

procedure_list = api.ProcedureViewSet.as_view({
    'get': 'list',
})
procedure_detail = api.ProcedureViewSet.as_view({
    'get': 'retrieve',
})
procedure_version_detail = api.ProcedureVersionViewSet.as_view({
    'get': 'list',
})
compilation_last_revision_detail = api.CompilationLastRevisionViewSet.as_view({
    'get': 'retrieve',
})

api_urlpatterns = format_suffix_patterns([
    re_path(r'^commits/$', commit_list, name='commit-list'),
    re_path(r'^commits/(?P<revision>[0-9]+)/$', commit_detail, name='commit-detail'),
    re_path(r'^commits/(?P<revision>[0-9]+)/versions/$', commit_version_list, name='commit-version-list'),
    re_path(r'^procedures/$', procedure_list, name='procedure-list'),
    re_path(r'^procedures/(?P<version>[0-9]+)/(?P<name>[a-z0-9\.]+)/$', procedure_detail, name='procedure-detail'),
    re_path(r'^procedures/(?P<version>[0-9]+)/(?P<name>[a-z0-9\.]+)/versions/$', procedure_version_detail,
        name='procedure-version-detail'),
    re_path(r'^compilation-last-revision/(?P<version>[0-9]+)/(?P<name>[a-z0-9\.]+)/?$', compilation_last_revision_detail,
        name='compilation-last-revision-detail'),
    re_path(r'^get-file/(?P<filename>.+)/?$', views.handle_sendfile, name='get-file')
])

urlpatterns = [
    re_path(r'^api/v1/', include(api_urlpatterns)),
    re_path(r'^$', views.handle_home, name='adltrack-home'),
    re_path(r'^commits/$', views.handle_commits, name='adltrack-commits'),
    re_path(r'^commits/(?P<revision>[0-9]+)/$', views.handle_commit, name='adltrack-commit'),
    re_path(r'^procedures/$', views.handle_procedures, name='adltrack-procedures'),
    re_path(r'^procedures-analysis/?$', views.handle_procedures_analysis, name='adltrack-procedures-analysis'),
    re_path(r'^procedures/(?P<version>[0-9]+)/(?P<name>[a-z0-9\.]+)/$', views.handle_procedure, name='adltrack-procedure'),
    re_path(r'^procedure-versions/(?P<version>[0-9]+)/(?P<name>[a-z0-9\.]+)/(?P<revision>[0-9]+)/$',
        views.handle_procedure_version, name='adltrack-procedure-version'),
    re_path(r'^tops/$', views.handle_tops, name='adltrack-tops'),
]
