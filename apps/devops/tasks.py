# ~*~ coding: utf-8 ~*~
from celery import shared_task
import json
from assets import const
from django.utils.translation import ugettext as _


@shared_task
def ansible_install_role(role_name, roles_path):
    from ops.utils import update_or_create_ansible_task

    task_name = _('Install Ansible Role')

    hosts = ["localhost"]

    tasks = [{
        'name': 'Install Ansible Role {}'.format(role_name),
        'action': {
            'module': 'shell',
            'args': 'ansible-galaxy install --roles-path {} -f {}'.format(roles_path, role_name),
        }
    }]
    #: 新建一个任务列表  执行shell 任务

    task, created = update_or_create_ansible_task(
        task_name=task_name, hosts=hosts, tasks=tasks, pattern='localhost',
        options=const.TASK_OPTIONS, run_as_admin=True, created_by='System',
    )
    result = task.run()

    summary = result[1]

    if summary.get('dark'):
        return False, summary['dark']
    else:
        return True, ""

#
#
# @shared_task
# def ansible_task_execute(task_id, assets, system_user, task_name, tags, uuid):
#     summary, result = run_playbook(playbook_path='../playbooks/task_%d.yml' % task_id, assets=assets,
#                                    system_user=system_user, task_name=task_name, tags=tags, task_id=task_id,
#                                    record_id=uuid)
#     return summary
