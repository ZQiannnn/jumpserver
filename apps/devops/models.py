# ~*~ coding: utf-8 ~*~
import json

from django.contrib.auth.hashers import make_password, check_password
from django.db import models

from django.utils.translation import ugettext_lazy as _
from separatedvaluesfield.models import TextSeparatedValuesField
from assets.models import *
from assets.models.user import AssetUser
from ops.models import Task, AdHoc, AdHocRunHistory
from collections import OrderedDict
from jsonfield import JSONField


class AnsibleRole(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('Name'))

    def __str__(self):
        return str(self.name)


class PlayBookTask(Task):
    desc = models.TextField(null=True, blank=True, verbose_name=_('Description'))
    password = models.CharField(max_length=200, verbose_name=_('WebHook Password'), blank=True, null=True)

    ansible_role = models.ForeignKey(AnsibleRole, verbose_name=_('Ansible Role'), related_name='task')
    tags = TextSeparatedValuesField(verbose_name=_('Tags'), null=True, blank=True)
    assets = models.ManyToManyField(Asset, verbose_name=_('Assets'), related_name='task', blank=True)
    groups = models.ManyToManyField(Node, verbose_name=_('Asset Groups'), related_name='task', blank=True)
    run_as = models.CharField(max_length=500, verbose_name=_('Run As User Id'), blank=True, null=True)

    def check_password(self, password_raw_):
        if self.password is None or self.password == "":
            return True
        else:
            return password_raw_ == self.password


class Playbook(AdHoc):
    playbook_task = models.ForeignKey(PlayBookTask, related_name='playbook', on_delete=models.CASCADE)
    playbook_path = models.CharField(max_length=1024, default='', verbose_name=_('Playbook Path'))


class PlaybookRunHistory(AdHocRunHistory):
    """Playbook Task 执行记录 """
    playbook_task = models.ForeignKey(PlayBookTask, related_name='playbook_history', on_delete=models.SET_NULL, null=True)
    playbook = models.ForeignKey(Playbook, related_name='playbook_history', on_delete=models.SET_NULL, null=True)


class Variable(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    desc = models.TextField(null=True, blank=True, verbose_name=_('Description'))
    vars = JSONField(null=True, blank=True, default={}, verbose_name=_('Vars'))
    assets = models.ManyToManyField(Asset, verbose_name=_('Assets'), related_name='variable', blank=True)
    groups = models.ManyToManyField(Node, verbose_name=_('Nodes'), related_name='variable', blank=True)
