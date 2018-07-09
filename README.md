## Jumpserver-Ansible

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
  - Playbook支持资产的变量绑定
  - Playbook支持WebHook执行
  - Playbook支持查看错误消息
  - 支持局域网的资产管理

### 开始使用

提供了一键安装shell脚本[Docker安装]，脚本参见: utils/jumpserver-install.sh (需要root权限)
```
./jumpserver-install.sh
```

### 示例
1. 维护资产与系统用户
![image](https://user-images.githubusercontent.com/19886406/42433942-d8c36fc6-8383-11e8-92a7-9c45e2899c78.png)
![image](https://user-images.githubusercontent.com/19886406/42434001-099db80e-8384-11e8-92ac-8d8e18a1756d.png)

2. 下载或上传Ansible Role
![image](https://user-images.githubusercontent.com/19886406/42434107-6bb3d83e-8384-11e8-8d0a-34b5ac590563.png)

3. 新建任务
![image](https://user-images.githubusercontent.com/19886406/42434164-97b22e86-8384-11e8-9fdb-71add806c7cd.png)

4. 配置资产与系统用户
![image](https://user-images.githubusercontent.com/19886406/42434218-e71398d4-8384-11e8-97fa-e534071ed698.png)

5. 配置资产的变量集
![image](https://user-images.githubusercontent.com/19886406/42434322-58b429f4-8385-11e8-96e6-8b8d772fa0e4.png)

6. 选择资产执行
![image](https://user-images.githubusercontent.com/19886406/42434353-78c70766-8385-11e8-82b0-a5c817e325de.png)

7. 查看执行结果
![image](https://user-images.githubusercontent.com/19886406/42434381-9164c2e0-8385-11e8-9be3-5304659f3b36.png)
![image](https://user-images.githubusercontent.com/19886406/42434392-9fdfc4b4-8385-11e8-9710-c103392c8050.png)




### License
Licensed under The GNU General Public License version 2 (GPLv2)  (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

https://www.gnu.org/licenses/gpl-2.0.html

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
