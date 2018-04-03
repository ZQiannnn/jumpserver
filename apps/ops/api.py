# ~*~ coding: utf-8 ~*~
import _thread
from concurrent.futures import ThreadPoolExecutor
import json
import multiprocessing

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.views import Response

from common.utils import get_object_or_none
from devops.models import Playbook
from users.permissions import IsValidUser
from .hands import IsSuperUser
from .models import Task, AdHoc, AdHocRunHistory
from .serializers import TaskSerializer, AdHocSerializer, AdHocRunHistorySerializer
from .tasks import run_ansible_task


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsValidUser,)


class TaskRun(generics.RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskViewSet
    permission_classes = (IsValidUser,)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        playbook = get_object_or_none(Playbook, id=task.latest_adhoc.id)
        if playbook and playbook.is_running:
            return Response('任务正在执行中，请查看作业中心...', status=status.HTTP_400_BAD_REQUEST)
        if playbook:
            run_ansible_task.delay(str(task.id), request.user.id, json.loads(request.GET.get('ids')))
            # _thread.start_new_thread(run_ansible_task,
            #                          (str(task.id), request.user.id, json.loads(request.GET.get('ids'))))

        else:
            run_ansible_task.delay(str(task.id), request.user.id)
        return Response({"msg": "start"})


class AdHocViewSet(viewsets.ModelViewSet):
    queryset = AdHoc.objects.all()
    serializer_class = AdHocSerializer
    permission_classes = (IsValidUser,)

    def get_queryset(self):
        task_id = self.request.query_params.get('task')
        if task_id:
            task = get_object_or_404(Task, id=task_id)
            self.queryset = self.queryset.filter(task=task)
        return self.queryset


class AdHocRunHistorySet(viewsets.ModelViewSet):
    queryset = AdHocRunHistory.objects.all()
    serializer_class = AdHocRunHistorySerializer
    permission_classes = (IsValidUser,)

    def get_queryset(self):
        task_id = self.request.query_params.get('task')
        adhoc_id = self.request.query_params.get('adhoc')
        if task_id:
            task = get_object_or_404(Task, id=task_id)
            adhocs = task.adhoc.all()
            self.queryset = self.queryset.filter(adhoc__in=adhocs).order_by('-date_start')

        if adhoc_id:
            adhoc = get_object_or_404(AdHoc, id=adhoc_id)
            self.queryset = self.queryset.filter(adhoc=adhoc).order_by('-date_start')
        return self.queryset
