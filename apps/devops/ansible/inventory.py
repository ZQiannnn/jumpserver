# ~*~ coding: utf-8 ~*~
from ansible.inventory.host import Host
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from assets.utils import get_assets_by_hostname_list, get_system_user_by_name
from perms.utils import NodePermissionUtil
from assets.models import *

__all__ = [
    'BaseHost', 'BaseInventory'
]


class BaseHost(Host):
    def __init__(self, host_data):
        """
        初始化
        :param host_data:  {
            "hostname": "",
            "ip": "",
            "port": "",
            # behind is not must be required
            "username": "",
            "password": "",
            "private_key": "",
            "become": {
                "method": "",
                "user": "",
                "pass": "",
            }
            "groups": [],
            "vars": {},
        }
        """
        self.host_data = host_data
        hostname = host_data.get('hostname') or host_data.get('ip')
        port = host_data.get('port') or 22
        super().__init__(hostname, port)
        self.__set_required_variables()
        self.__set_extra_variables()

    def __set_required_variables(self):
        host_data = self.host_data
        self.set_variable('ansible_host', host_data['ip'])
        self.set_variable('ansible_port', host_data['port'])

        if host_data.get('username'):
            self.set_variable('ansible_user', host_data['username'])

        # 添加密码和秘钥
        if host_data.get('password'):
            self.set_variable('ansible_ssh_pass', host_data['password'])
        if host_data.get('private_key'):
            self.set_variable('ansible_ssh_private_key_file', host_data['private_key'])

        # 添加become支持
        become = host_data.get("become", False)
        if become:
            self.set_variable("ansible_become", True)
            self.set_variable("ansible_become_method", become.get('method', 'sudo'))
            self.set_variable("ansible_become_user", become.get('user', 'root'))
            self.set_variable("ansible_become_pass", become.get('pass', ''))
        else:
            self.set_variable("ansible_become", False)

    def __set_extra_variables(self):
        for k, v in self.host_data.get('vars', {}).items():
            self.set_variable(k, v)

    def __repr__(self):
        return self.name


class BaseInventory(InventoryManager):
    """
    提供生成Ansible inventory对象的方法
    """
    loader_class = DataLoader
    variable_manager_class = VariableManager
    host_manager_class = BaseHost

    def __init__(self, host_list=None):
        """
        用于生成动态构建Ansible Inventory. super().__init__ 会自动调用
        host_list: [{
            "hostname": "",
            "ip": "",
            "port": "",
            "username": "",
            "password": "",
            "private_key": "",
            "become": {
                "method": "",
                "user": "",
                "pass": "",
            },
            "groups": [],
            "vars": {},
          },
        ]
        :param host_list:
        """
        if host_list is None:
            host_list = []
        self.host_list = host_list
        assert isinstance(host_list, list)
        self.loader = self.loader_class()
        self.variable_manager = self.variable_manager_class()
        super().__init__(self.loader)

    def get_groups(self):
        return self._inventory.groups

    def get_group(self, name):
        return self._inventory.groups.get(name, None)

    def parse_sources(self, cache=False):
        group_all = self.get_group('all')
        ungrouped = self.get_group('ungrouped')

        for host_data in self.host_list:

            host = self.host_manager_class(host_data=host_data)
            self.hosts[host_data['hostname']] = host

            groups_data = host_data.get('groups')
            if groups_data:
                for group_name in groups_data:
                    group = self.get_group(group_name)

                    if group is None:
                        self.add_group(group_name)
                        group = self.get_group(group_name)

                    group.add_host(host)
            else:
                ungrouped.add_host(host)
            group_all.add_host(host)

    def get_matched_hosts(self, pattern):
        return self.get_hosts(pattern)


class PlaybookInventory(BaseInventory):
    """
    JMS Inventory is the manager with jumpserver assets, so you can
    write you own manager, construct you inventory
    """

    def __init__(self, task, run_as_admin=False, run_as=None, become_info=None):
        self.task = task
        self.using_admin = run_as_admin
        self.run_as = run_as
        self.become_info = become_info

        assets = self.get_jms_assets()
        if run_as_admin:
            host_list = [asset._to_secret_json() for asset in assets]
        else:
            host_list = [asset.to_json() for asset in assets]
            if run_as:
                run_user_info = self.get_run_user_info()
                for host in host_list:
                    host.update(run_user_info)
            if become_info:
                for host in host_list:
                    host.update(become_info)
        self.host_list = host_list
        self.set_all_variables()
        super().__init__(host_list=host_list)
        print(self.host_list)

    def get_jms_assets(self):
        assets = []
        assets.extend(list(self.task.assets.all()))
        for group in self.task.groups.all():
            assets.extend(group.get_all_active_assets())
        from jumpserver import middleware
        user = middleware.get_current_user()

        if not user.is_superuser:
            #: 普通用户取授权过的assets
            granted_assets = NodePermissionUtil.get_user_assets(user=user)
            #: 取交集
            assets = set(assets).intersection(set(granted_assets))
        return assets

    def get_run_user_info(self):
        system_user = get_system_user_by_name(self.run_as)
        if not system_user:
            return {}
        else:
            return system_user._to_secret_json()

    def set_all_variables(self):
        for host_data in self.host_list:
            # 先设置Groups
            groups = list()
            # 从上到下找到所有的node
            nodes = list(Node.objects.filter(assets=Asset.objects.get(hostname=host_data.get('hostname'))))
            nodes_list = set()
            for node in nodes:
                # 添加自己
                nodes_list.add(node)
                # 添加自己的所有父节点
                parent = node.parent
                while not parent.is_root():
                    nodes_list.add(parent)
                    parent = parent.parent
            # 从父到子排序
            nodes_list = list(nodes_list)
            nodes_list.sort(key=lambda x: len(x.key))

            for node in nodes_list:
                # 添加到groups
                groups.append(node.name)

            host_data['groups'] = groups

            # 在设置Vars
            variables = {}
            # 组的变量
            from ..models import Variable
            for group in groups:
                # 每一层Groups设置变量
                #: 找到id对应的Group Variable 设置Group Vars
                variable = list(
                    Variable.objects.filter(groups=Node.objects.get(value=group)))
                if len(variable) > 0:
                    for key, value in variable[0].vars.items():
                        print(group, key, value)
                        variables.update({key: value})
            # 机器的变量
            variable = list(
                Variable.objects.filter(assets=Asset.objects.get(hostname=host_data.get('hostname'))))
            if len(variable) > 0:
                for key, value in variable[0].vars.items():
                    variables.update({key: value})

            host_data['vars'] = variables
