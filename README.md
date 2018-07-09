## Jumpserver

[![Python3](https://img.shields.io/badge/python-3.6-green.svg?style=plastic)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-1.11-brightgreen.svg?style=plastic)](https://www.djangoproject.com/)
[![Ansible](https://img.shields.io/badge/ansible-2.2.2.0-blue.svg?style=plastic)](https://www.ansible.com/)
[![Paramiko](https://img.shields.io/badge/paramiko-2.1.2-green.svg?style=plastic)](http://www.paramiko.org/)


----

Jumpserver-Ansible 在 Jumpserver 的基础上添加了在管理资产上执行Ansible Role的功能，无侵入与JumpServer集成，目前适配到0.5.0版本，
如需更新请联系作者。

----

### 功能
  - Ansible Galaxy下载
  - Ansible Role本地上传
  - Playbook支持Tags执行
  - Playbook支持选择系统用户执行
  - Playbook支持绑定资产执行
  - Playbook支持WebHook执行
  - 支持局域网的资产管理

### 开始使用

提供了一键安装shell脚本[Docker安装]，脚本参见: utils/jumpserver-install.sh (需要root权限)
```
./jumpserver-install.sh
```

### 示例
1. 维护资产与系统用户

2. 下载或上传Ansible Role

3. 新建任务

4. 配置资产与系统用户

5. 选择资产执行

6. 查看执行结果





### License
Licensed under The GNU General Public License version 2 (GPLv2)  (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

https://www.gnu.org/licenses/gpl-2.0.html

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
