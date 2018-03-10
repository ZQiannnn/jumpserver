# ~*~ coding: utf-8 ~*~

from __future__ import absolute_import, unicode_literals

from assets import const
from .models import Playbook
import os
import json


def create_update_task_playbook(task):
    # 共用task的adhoc字段用来存playbook
    playbook = task.latest_adhoc
    new_playbook = Playbook(task=task, pattern="all",
                            run_as_admin=task.system_user is None,
                            run_as=task.system_user.name if task.system_user else '')
    new_playbook.options = const.TASK_OPTIONS
    new_playbook.tasks = [{"name": task.name, "action": {"module": "Ansible Role : " + task.ansible_role.name
                                                                   + ",Ansible Tags : " + json.dumps(task.tags)}}]
    new_playbook.hosts = []
    new_playbook.playbook_path = os.path.abspath("../playbooks/task_%s.yml" % task.id)
    created = False
    if not playbook or playbook != new_playbook:
        print("Task create new playbook: {}".format(task.name))
        new_playbook.save()
        task.latest_adhoc = new_playbook
        created = True
    return task, created

# def run_AdHoc(task_tuple, assets=None,
#               task_name='Ansible AdHoc runner',
#               task_id=None, pattern='all',
#               record=True, verbose=True):
#     """
#     改造为不输入assets时为本地执行
#     :param task_tuple:  (('module_name', 'module_args'), ('module_name', 'module_args'))
#     :param assets: [asset1, asset2]
#     :param task_name:
#     :param task_id:
#     :param pattern:
#     :param task_record:
#     :param verbose:
#     :return: summary: {'success': [], 'failed': [{'192.168.1.1': 'msg'}]}
#              result: {'contacted': {'hostname': [{''}, {''}], 'dark': []}
#     """
#     if not assets:
#         runner = AdHocRunner('/etc/ansible/hosts')
#         pattern = 'local'
#     else:
#         runner = AdHocRunner(assets)
#         if isinstance(assets[0], Asset):
#             assets = [asset._to_secret_json() for asset in assets]
#     if task_id is None:
#         task_id = str(uuid.uuid4())
#
#     if record:
#         if not Record.objects.filter(uuid=task_id):
#             task_record = Record(uuid=task_id,
#                                  name=task_name,
#                                  assets='localhost' if not assets else ','.join(str(asset['id']) for asset in assets),
#                                  module_args=task_tuple,
#                                  pattern=pattern)
#             task_record.save()
#         else:
#             task_record = Record.objects.get(uuid=task_id)
#             task_record.date_start = timezone.now()
#             task_record.date_finished = None
#             task_record.timedelta = None
#             task_record.is_finished = False
#             task_record.is_success = False
#             task_record.save()
#     ts_start = time.time()
#     if verbose:
#         logger.debug('Start runner {}'.format(task_name))
#     result = runner.run(task_tuple, pattern=pattern, task_name=task_name)
#     timedelta = round(time.time() - ts_start, 2)
#     summary = runner.clean_result()
#     if task_record:
#         task_record.date_finished = timezone.now()
#         task_record.is_finished = True
#         if verbose:
#             task_record.result = json.dumps(result, indent=4, sort_keys=True)
#         task_record.summary = json.dumps(summary)
#         task_record.timedelta = timedelta
#         if len(summary['failed']) == 0:
#             task_record.is_success = True
#         else:
#             task_record.is_success = False
#         task_record.save()
#     return summary, result
#
#
#
# def run_playbook(playbook_path, assets, system_user=None, task_name='Ansible PlayBook Runner',
#                  tags=None, verbose=True, task_id=None, record_id=None):
#     """
#     改造为不输入assets时为本地执行
#     :param record_id: uuid
#     :param task_id: task id
#     :param task_name: TaskName #count
#     :param system_user: become system user
#     :param playbook_path:  ../record_id.yml
#     :param assets: [{asset1}, {asset2}]
#     :param tags: [tagA,tagB]
#     :param verbose:
#     :return: summary: {'success': [], 'failed': [{'192.168.1.1': 'msg'}]}
#              result: {'contacted': {'hostname': [{''}, {''}], 'dark': []}
#     """
#     runner = PlayBookRunner(assets, playbook_path=playbook_path, tags=tags, become=True, become_user=system_user)
#
#     #: 开始执行记录
#     task_record = Record.objects.get(uuid=record_id)
#     task_record.date_start = timezone.now()
#     task_record.date_finished = None
#     task_record.timedelta = None
#     task_record.is_finished = False
#     task_record.is_success = False
#     task_record.save()
#
#     ts_start = time.time()
#     if verbose:
#         logger.debug('Start runner {}'.format(task_name))
#     result = runner.run()
#     timedelta = round(time.time() - ts_start, 2)
#     summary = runner.clean_result()
#
#     #: 任务结束记录
#     task_record.date_finished = timezone.now()
#     task_record.is_finished = True
#     if verbose:
#         task_record.result = str(json.dumps(result, indent=4, ensure_ascii=False))
#     task_record.summary = json.dumps(summary)
#     task_record.timedelta = timedelta
#     if len(summary['failed']) == 0:
#         task_record.is_success = True
#     else:
#         task_record.is_success = False
#     task_record.save()
#     return summary, result
