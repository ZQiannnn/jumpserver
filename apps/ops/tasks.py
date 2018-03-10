# coding: utf-8
from celery import shared_task, subtask

from common.utils import get_logger, get_object_or_none
from .models import Task
from devops.models import PlayBookTask,Playbook

logger = get_logger(__file__)


def rerun_task():
    pass


@shared_task
def run_ansible_task(task_id, current_user=None, callback=None, **kwargs):
    """
    :param task_id: is the tasks serialized data
    :param callback: callback function name
    :param current_user: 当前用户
    :return:
    """

    task = get_object_or_none(PlayBookTask, id=task_id)
    if task:
        playbook = get_object_or_none(Playbook, id=task.latest_adhoc.id)
        playbook.is_running = True
        playbook.save()
        result = task.run(current_user=current_user)
        if callback is not None:
            subtask(callback).delay(result, task_name=task.name)
        return result
    else:
        task = get_object_or_none(Task, id=task_id)
        if task:
            result = task.run()
            if callback is not None:
                subtask(callback).delay(result, task_name=task.name)
            return result
        else:
            logger.error("No task found")


@shared_task
def hello(name, callback=None):
    print("Hello {}".format(name))
    if callback is not None:
        subtask(callback).delay("Guahongwei")


@shared_task
def hello_callback(result):
    print(result)
    print("Hello callback")
