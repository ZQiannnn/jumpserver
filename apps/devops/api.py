# ~*~ coding: utf-8 ~*~

import os
from collections import OrderedDict

import _thread
import yaml
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets, generics, mixins
from rest_framework.response import Response

from .hands import IsSuperUser, IsValidUser
from .serializers import *
from .tasks import ansible_install_role
from .utils import create_update_task_playbook
from ops.tasks import run_ansible_task
from common.utils import get_object_or_none


class TaskListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
        对Ansible的task list的 展示 API操作
    """
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskReadSerializer
    permission_classes = (IsValidUser,)


class TaskOperationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    """
        对Ansible的task提供的 操作 API操作
    """
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsSuperUser,)

    def update(self, request, *args, **kwargs):
        response = super(TaskOperationViewSet, self).update(request, *args, **kwargs)
        task = self.get_object()
        self.playbook(task.id, request)
        return response

    def create(self, request, *args, **kwargs):
        response = super(TaskOperationViewSet, self).create(request, *args, **kwargs)
        task = PlayBookTask.objects.get(id=response.data['id'])
        task.created_by = request.user.name
        task.save()
        self.playbook(response.data['id'], request)
        return response

    def playbook(self, task_id, request):
        """ 组织任务的playbook 文件"""
        task = PlayBookTask.objects.get(id=task_id)
        playbook = {'hosts': 'all'}

        #: role
        role = OrderedDict()
        role.update({'roles': [{'role': task.ansible_role.name}]})
        playbook.update(role)

        playbook_yml = [playbook]
        if not os.path.exists('../playbooks'):
            os.makedirs('../playbooks')
        with open("../playbooks/task_%s.yml" % task.id, "w") as f:
            yaml.dump(playbook_yml, f)

        """ 创建task的playbook """
        create_update_task_playbook(task, request.user)


class AnsibleRoleViewSet(viewsets.ModelViewSet):
    """
        对AnsibleRole提供的API操作
    """
    queryset = AnsibleRole.objects.all()
    serializer_class = AnsibleRoleSerializer
    permission_classes = (IsSuperUser,)


class InstallRoleView(generics.CreateAPIView):
    """
        ansible-galaxy 安装 role
    """
    queryset = AnsibleRole.objects.all()
    serializer_class = AnsibleRoleSerializer
    permission_classes = (IsSuperUser,)
    result = None

    def perform_create(self, serializer):
        #: 新建role安装文件夹
        roles_path = os.path.join(settings.PROJECT_DIR, 'playbooks', 'roles')
        #: 获取role name

        #: 执行role 安装操作
        self.result, msg = ansible_install_role(self.request.data['name'], roles_path)
        #: 去掉参数中的版本
        name = str(self.request.data['name']).split(',')[0]
        #: 当执行成功且Role不存在时才保存
        if self.result and not self.get_queryset().filter(name=name).exists():
            serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        #: 安装失败返回错误
        return Response(serializer.data, status=status.HTTP_201_CREATED if self.result else status.HTTP_400_BAD_REQUEST,
                        headers=headers)


class InstallZipRoleView(generics.CreateAPIView):
    """
        ansible-galaxy 安装 role
    """
    queryset = AnsibleRole.objects.all()
    serializer_class = AnsibleRoleSerializer
    permission_classes = (IsSuperUser,)

    def create(self, request, *args, **kwargs):
        file = request.FILES['file_data']
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        #: 保存
        path = default_storage.save(os.path.join(settings.MEDIA_ROOT, 'tmp', '{}.zip'.format(file.name)),
                                    ContentFile(file.read()))
        #: 解压
        import zipfile
        f = zipfile.ZipFile(path, 'r')
        for file in f.namelist():
            f.extract(file, os.path.join(settings.PROJECT_DIR, 'playbooks', 'roles'))

        #: 删除
        default_storage.delete(path)

        #: 保存实例
        if not self.get_queryset().filter(name=request.data['name']).exists():
            serializer.save()
        headers = self.get_success_headers(serializer.data)
        #: 返回
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TaskUpdateGroupApi(generics.RetrieveUpdateAPIView):
    """Task update it's group api"""
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskUpdateGroupSerializer
    permission_classes = (IsSuperUser,)

    def update(self, request, *args, **kwargs):
        response = super(TaskUpdateGroupApi, self).update(request, *args, **kwargs)
        create_update_task_playbook(self.get_object())
        return response


class TaskStatusApi(generics.RetrieveAPIView):
    """Task update it's group api"""
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskUpdateGroupSerializer
    permission_classes = (IsSuperUser,)

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        playbook = get_object_or_none(Playbook, id=task.latest_adhoc.id)
        return Response({'is_running':playbook.is_running}, status=status.HTTP_200_OK)


class TaskUpdateAssetApi(generics.RetrieveUpdateAPIView):
    """Task update it's asset api"""
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskUpdateAssetSerializer
    permission_classes = (IsSuperUser,)

    def update(self, request, *args, **kwargs):
        response = super(TaskUpdateAssetApi, self).update(request, *args, **kwargs)
        create_update_task_playbook(self.get_object())
        return response


class TaskUpdateSystemUserApi(generics.RetrieveUpdateAPIView):
    """Task update it's system_user api"""
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskUpdateSystemUserSerializer
    permission_classes = (IsSuperUser,)

    def update(self, request, *args, **kwargs):
        response = super(TaskUpdateSystemUserApi, self).update(request, *args, **kwargs)
        create_update_task_playbook(self.get_object())
        return response


class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.all()
    serializer_class = VariableSerializer
    permission_classes = (IsSuperUser,)


class VariableVarsApi(generics.RetrieveAPIView):
    """
       Vars Read API
    """
    permission_classes = (IsSuperUser,)
    queryset = Variable.objects.all()

    def retrieve(self, request, *args, **kwargs):
        variable = self.get_object()
        result = []
        for key, value in variable.vars.items():
            result.append({"key": key, "value": value})
        return Response(result, status=status.HTTP_200_OK)


class VariableAddVarsApi(generics.UpdateAPIView):
    """
       Vars Add API
    """
    permission_classes = (IsSuperUser,)
    queryset = Variable.objects.all()
    serializer_class = VariableVarSerializer

    def put(self, request, *args, **kwargs):
        variable = self.get_object()
        variable.vars.update({request.data['key']: request.data['value'] + "-" + request.data.get('desc', '')})
        variable.save()
        return Response(variable.vars, status=status.HTTP_200_OK)


class VariableDeleteVarsApi(generics.DestroyAPIView):
    """
       Vars Add API
    """
    permission_classes = (IsSuperUser,)
    queryset = Variable.objects.all()
    serializer_class = VariableVarSerializer

    def delete(self, request, *args, **kwargs):
        variable = self.get_object()
        variable.vars.pop(request.data['key'])
        variable.save()
        return Response(variable.vars, status=status.HTTP_200_OK)


class VariableUpdateGroupApi(generics.UpdateAPIView):
    """Variable update it's group api"""
    queryset = Variable.objects.all()
    serializer_class = VariableUpdateGroupSerializer
    permission_classes = (IsSuperUser,)


class VariableUpdateAssetApi(generics.UpdateAPIView):
    """Variable update it's asset api"""
    queryset = Variable.objects.all()
    serializer_class = VariableUpdateAssetSerializer
    permission_classes = (IsSuperUser,)


class VariableGetAssetApi(generics.RetrieveAPIView):
    """Variable update it's asset api"""
    queryset = Variable.objects.all()
    serializer_class = AssetSerializer
    permission_classes = (IsSuperUser,)

    def retrieve(self, request, *args, **kwargs):
        serializer = AssetSerializer(self.get_object().assets.all(), many=True)
        return Response(serializer.data)


class VariableGetGroupApi(generics.RetrieveAPIView):
    """Variable update it's asset api"""
    queryset = Variable.objects.all()
    serializer_class = NodeSerializer
    permission_classes = (IsSuperUser,)

    def retrieve(self, request, *args, **kwargs):
        serializer = NodeSerializer(self.get_object().groups.all(), many=True)
        return Response(serializer.data)


class TaskWebhookApi(generics.GenericAPIView):
    """
       Task Execute API
    """
    permission_classes = (permissions.AllowAny,)
    queryset = PlayBookTask.objects.all()
    serializer_class = TaskWebhookSerializer

    def post(self, request, *args, **kwargs):
        task = self.get_object()

        password_raw = request.data['password']

        result = task.check_password(password_raw)  # check_password 返回值为一个Bool类型，验证密码的正确与否

        if not result:
            return Response("任务密码不匹配", status=status.HTTP_400_BAD_REQUEST)

        _thread.start_new_thread(run_ansible_task, (str(task.id), request.user.id,))

        return Response(status=status.HTTP_200_OK)
