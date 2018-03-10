# -*- coding: utf-8 -*-
#

from __future__ import unicode_literals

from django.conf.urls import url
from .. import views

app_name = 'devops'

urlpatterns = [
    url(r'^task/$', views.TaskListView.as_view(), name='task-list'),
    url(r'^task/create$', views.TaskCreateView.as_view(), name='task-create'),
    url(r'^task/(?P<pk>[0-9a-zA-Z\-]{36})/update/$', views.TaskUpdateView.as_view(), name='task-update'),
    url(r'^task/(?P<pk>[0-9a-zA-Z\-]{36})/detail/$', views.TaskDetailView.as_view(), name='task-detail'),
    url(r'^variable/$', views.VariableListView.as_view(), name='variable-list'),
    url(r'^variable/create$', views.VariableCreateView.as_view(), name='variable-create'),
    url(r'^variable/(?P<pk>[0-9]+)/update/$', views.VariableUpdateView.as_view(), name='variable-update'),
    url(r'^variable/(?P<pk>[0-9]+)/detail/$', views.VariableDetailView.as_view(), name='variable-detail'),
    url(r'^variable/(?P<pk>[0-9]+)/asset/$', views.VariableAssetView.as_view(), name='variable-asset'),
]
