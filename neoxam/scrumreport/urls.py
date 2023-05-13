from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.Index.as_view(),
        name='index'),
    url(r'^load_data/$',
        views.LoadData.as_view(),
        name='load_data'),
    url(r'^login/$',
        views.Login.as_view(),
        name='login'),
    url(r'^logout/$',
        views.Logout.as_view(),
        name='logout'),
    url(r'^show_sprint/(?P<jira_id>[0-9]+)/$',
        views.ShowSprint.as_view(),
        name='show_sprint'),
    url(
        r'^current_scrum/',
        views.CurrentScrum.as_view(),
        name='current_scrum'),
]
