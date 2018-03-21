# ~*~ coding: utf-8 ~*~

import json
import time

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from separatedvaluesfield.models import TextSeparatedValuesField

from assets.models import *
from assets.models.user import AssetUser
from common.utils import get_signer, get_logger
from ops.models import Task, AdHoc, AdHocRunHistory
from users.models import User
from .ansible import PlayBookRunner, get_default_options
from .ansible.inventory import PlaybookInventory

logger = get_logger(__file__)
signer = get_signer()

__all__ = ["AnsibleRole", "PlayBookTask", "Playbook", "Variable"]


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
    system_user = models.ForeignKey(SystemUser, null=True, blank=True, verbose_name=_('System User'),
                                    related_name='task')

    def check_password(self, password_raw_):
        if self.password is None or self.password == "":
            return True
        else:
            return password_raw_ == self.password

    def run(self, current_user=None, ids=None, record=True):
        if self.latest_adhoc:
            return Playbook.objects.get(id=self.latest_adhoc.id).run(current_user=current_user, ids=ids, record=record)
        else:
            return {'error': 'No adhoc'}

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        return self.id == other.id


class Playbook(AdHoc):
    playbook_path = models.CharField(max_length=1000, verbose_name=_('Playbook Path'), blank=True, null=True)
    is_running = models.BooleanField(default=False, verbose_name=_('Is running'))

    @property
    def inventory(self):
        if self.become:
            become_info = {
                'become': {
                    self.become
                }
            }
        else:
            become_info = None
        inventory = PlaybookInventory(
            task=self.playbook_task, run_as_admin=self.run_as_admin,
            run_as=self.run_as, become_info=become_info, current_user=self.current_user, ids=self.ids
        )
        return inventory

    @property
    def playbook_task(self):
        return PlayBookTask.objects.get(id=self.task.id)

    def run(self, current_user=None, ids=None, record=True):
        self.ids = ids
        self.current_user = User.objects.get(id=current_user)
        if record:
            result, summary = self._run_and_record()
            return result, summary
        else:
            result, summary = self._run_only()

            return result, summary

    def _run_and_record(self):
        history = AdHocRunHistory(adhoc=self, task=self.task)
        time_start = time.time()
        try:
            result, summary = self._run_only()
            history.is_finished = True
            if len(summary.get('dark')) != 0:
                history.is_success = False
            else:
                history.is_success = True
            result = str(json.dumps(result, indent=4, ensure_ascii=False))
            history.result = result
            history.summary = summary
            return result, summary
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {}, {"dark": {"all": {"msg": str(e)}}, "contacted": []}
        finally:
            history.date_finished = timezone.now()
            history.timedelta = time.time() - time_start
            history.save()

    def _clean_result(self, output):
        """
                :return: {
                    "contacted": ['hostname',],
                    "dark": {'hostname':{'task1':{'msg':''}}},
                }
                """
        result = {'contacted': [], 'dark': {}}
        for host, stat in output['stats'].items():
            if stat['unreachable'] == 0 and stat['failures'] == 0:
                result['contacted'].append(host)

        for task in output['plays'][0]['tasks']:
            for host, detail in task.get('hosts', {}).items():
                if detail.get('status') == 'failed' or detail.get('status') == 'unreachable':
                    if host in result['contacted']:
                        logger.info("ignore host:" + host + "  with:" + str(result['contacted']))
                        print("ignore host:" + host + "  with:" + str(result['contacted']))
                        continue
                    if not result['dark'].get(host):
                        result['dark'][host] = {}
                    # 找到每个task对应的失败host与消息
                    host_data = result['dark'].get(host)
                    msg = detail.get('msg', '')
                    if msg == "All items completed":
                        for res in detail['results']:
                            msg = res['item'] + "===" + res['msg']
                    total = detail.get('stderr') if detail.get('stderr') else detail.get('stdout')
                    host_data[task['task'].get('name', '')] = {
                        'msg': '%s => %s' % (msg, total)}
        logger.info(result)
        print(result)
        return result

    def _run_only(self):
        options = get_default_options()
        options = options._replace(playbook_path=self.playbook_path)
        options = options._replace(tags=self.playbook_task.tags if self.playbook_task.tags else [])
        runner = PlayBookRunner(self.inventory, options)
        try:
            result, output = runner.run()
            summary = self._clean_result(output)
            self.is_running = False
            self.save()
            return result, summary
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("Failed run adhoc {}, {}".format(self.task.name, e))
            self.is_running = False
            self.save()
            return {}, {"dark": {"playbook": {"msg": str(e)}}, "contacted": []}
            pass

    def __str__(self):
        return "{} of {}".format(self.task.name, self.short_id)

    def __eq__(self, other):
        instance = other
        if not isinstance(self, other.__class__):
            return False
        if not isinstance(other, self.__class__):
            instance = Playbook.objects.get(id=other.id)
        fields_check = []
        for field in self.__class__._meta.fields:
            if field.name not in ['id', 'date_created', 'adhoc_ptr']:
                fields_check.append(field)
        for field in fields_check:
            if getattr(self, field.name) != getattr(instance, field.name):
                return False
        return True


class Variable(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    desc = models.TextField(null=True, blank=True, verbose_name=_('Description'))
    vars = JSONField(null=True, blank=True, default={}, verbose_name=_('Vars'))
    assets = models.ManyToManyField(Asset, verbose_name=_('Assets'), related_name='variable', blank=True)
    groups = models.ManyToManyField(Node, verbose_name=_('Nodes'), related_name='variable', blank=True)
