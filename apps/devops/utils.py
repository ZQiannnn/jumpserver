# ~*~ coding: utf-8 ~*~

from __future__ import absolute_import, unicode_literals


from assets import const
from .models import Playbook
import os
import json
from django.utils import timezone


def create_update_task_playbook(task, user):
    # 共用task的adhoc字段用来存playbook
    playbook = task.latest_adhoc

    new_playbook = Playbook(task=task, pattern="all",
                            run_as_admin=task.system_user is None,
                            run_as=task.system_user.name if task.system_user else '', created_by=user.name,
                            date_created=timezone.now())
    new_playbook.options = const.TASK_OPTIONS

    tasks = list()

    tasks.append({"name": 'Ansible Role', "action": {"module": task.ansible_role.name}})
    tasks.append({"name": 'Ansible Tags', "action": {"module": json.dumps(task.tags if task.tags else ['all'])}})

    # 执行Asset列表
    assets = []
    for asset in task.assets.all():
        assets.append(asset.hostname)
    tasks.append({"name": 'Assets', "action": {"module": str(assets) if len(assets) > 0 else 'Empty'}})
    # 执行Group列表
    groups = []
    for node in task.groups.all():
        groups.append(node.value)
    tasks.append({"name": 'Groups', "action": {"module": str(groups) if len(groups) > 0 else 'Empty'}})
    # 执行的SystemUser
    tasks.append(
        {"name": 'System User', "action": {"module": task.system_user.name if task.system_user else 'Admin User'}})

    # 名称和描述
    new_playbook.tasks = tasks
    new_playbook.hosts = []
    new_playbook.playbook_path = os.path.abspath("../data/playbooks/task_%s.yml" % task.id)
    created = False
    if not playbook or playbook != new_playbook:
        print("Task create new playbook: {}".format(task.name))
        new_playbook.save()
        task.latest_adhoc = new_playbook
        created = True
    return task, created



