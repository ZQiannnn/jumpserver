# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, DetailView, RedirectView

from assets.models import *
from .forms import *
from .hands import *
from .models import *

logger = logging.getLogger(__name__)

"""   Task   """


class TaskListView(LoginRequiredMixin, TemplateView):
    template_name = 'devops/task_list.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Tasks'),
        }
        kwargs.update(context)
        return super(TaskListView, self).get_context_data(**kwargs)


class TaskCreateView(AdminUserRequiredMixin, TemplateView):
    template_name = 'devops/task_create.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Create Task'),
            'form': TaskForm,
        }
        kwargs.update(context)
        return super(TaskCreateView, self).get_context_data(**kwargs)


class TaskUpdateView(AdminUserRequiredMixin, TemplateView):
    template_name = 'devops/task_update.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Update Task'),
            'form': TaskForm,
            'id': kwargs['pk'],
        }
        kwargs.update(context)
        return super(TaskUpdateView, self).get_context_data(**kwargs)


class TaskDetailView(LoginRequiredMixin, DetailView):
    queryset = PlayBookTask.objects.all()
    context_object_name = 'task'
    template_name = 'devops/task_detail.html'

    def get_context_data(self, **kwargs):
        assets = self.object.assets.all()
        asset_groups = self.object.groups.all()
        system_user = self.object.system_user
        context = {
            'app': _('Ansible'),
            'action': _('Task Detail'),
            'assets': assets,
            'assets_remain': [asset for asset in Asset.objects.all()
                              if asset not in assets],
            'asset_groups': asset_groups,
            'asset_groups_remain': [asset_group for asset_group in Node.objects.all()
                                    if asset_group not in asset_groups],
            'system_user': system_user,
            'system_users_remain': SystemUser.objects.exclude(
                id=system_user.id) if system_user else SystemUser.objects.all(),
        }
        kwargs.update(context)
        return super(TaskDetailView, self).get_context_data(**kwargs)


"""   Variable     """


class VariableListView(AdminUserRequiredMixin, TemplateView):
    template_name = 'devops/variable_list.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Variables'),
        }
        kwargs.update(context)
        return super(VariableListView, self).get_context_data(**kwargs)


class VariableCreateView(AdminUserRequiredMixin, TemplateView):
    template_name = 'devops/variable_create.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Create Variable'),
            'form': VariableForm,
        }
        kwargs.update(context)
        return super(VariableCreateView, self).get_context_data(**kwargs)


class VariableUpdateView(AdminUserRequiredMixin, TemplateView):
    template_name = 'devops/variable_update.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Update Variable'),
            'form': VariableForm,
            'id': kwargs['pk'],
        }
        kwargs.update(context)
        return super(VariableUpdateView, self).get_context_data(**kwargs)


class VariableCloneView(AdminUserRequiredMixin, RedirectView):
    url = reverse_lazy('devops:variable-list')

    def get(self, request, *args, **kwargs):
        #: 克隆一个变量组
        old_var = Variable.objects.get(id=kwargs['pk'])
        new_var = Variable(name=old_var.name + "-copy", vars=old_var.vars, desc=old_var.desc + "-copy")
        new_var.save()
        return super(VariableCloneView, self).get(request, *args, **kwargs)


class VariableDetailView(AdminUserRequiredMixin, DetailView):
    queryset = Variable.objects.all()
    context_object_name = 'variable'
    template_name = 'devops/variable_detail.html'

    def get_context_data(self, **kwargs):
        context = {
            'app': _('Ansible'),
            'action': _('Variable Detail'),
        }
        kwargs.update(context)
        return super(VariableDetailView, self).get_context_data(**kwargs)


class VariableAssetView(AdminUserRequiredMixin, DetailView):
    queryset = Variable.objects.all()
    context_object_name = 'variable'
    template_name = 'devops/variable_asset.html'

    def get_context_data(self, **kwargs):
        assets = self.object.assets.all()
        asset_groups = self.object.groups.all()
        context = {
            'app': _('Ansible'),
            'action': _('Variable Detail'),
            #: 资产和资产组都不允许重复选择
            'assets_remain': [asset for asset in Asset.objects.all().filter(variable=None)
                              if asset not in assets],
            'asset_groups_remain': [asset_group for asset_group in Node.objects.all().filter(variable=None)
                                    if asset_group not in asset_groups],
        }
        kwargs.update(context)
        return super(VariableAssetView, self).get_context_data(**kwargs)
