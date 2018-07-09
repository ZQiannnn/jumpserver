#!/usr/bin/env bash
set -e
# Root执行 CentOS7
if ! type docker >/dev/null 2>&1; then
   echo "Docker 安装"
   curl -o docker.sh -ssL https://get.docker.com
   chmod +x docker.sh
   sudo sh docker.sh --mirror Aliyun
fi

systemctl start docker
systemctl enable docker

if ! type docker-compose >/dev/null 2>&1; then
    echo "Docker Compose 安装"
    curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py && python get-pip.py
    pip install  -i https://pypi.tuna.tsinghua.edu.cn/simple docker-compose
fi

if ! type git >/dev/null 2>&1; then
    echo "Git 安装"
    yum install -y git
fi

if ! type pipework >/dev/null 2>&1; then
    echo "Pipework 安装"
    git clone https://github.com/jpetazzo/pipework
    mv pipework/pipework /usr/local/bin/
fi



#创建用户
user=jumpserver
group=jumpserver
#create group if not exists
if ! egrep "^$group" /etc/group >/dev/null 2>&1;
then
    echo "创建jumpserver用户组"
    groupadd $group
fi
#create user if not exists
if ! egrep "^$user" /etc/passwd  >/dev/null 2>&1;
then
    echo "创建jumpserver用户"
    useradd -g $group $user
fi
echo "创建用户完成"

#使jumpserver用户能使用docker
echo "增加jumpserver运行docker权限"
usermod -aG docker jumpserver

#创建应用安装文件夹
echo "创建应用文件夹/opt"
mkdir -p /opt

chown jumpserver:docker /opt

mkdir -p /opt/jumpserver
rm -rf /opt/jumpserver/logs



mkdir -p /opt/jumpserver/postgresql
mkdir -p /opt/jumpserver/redis
mkdir -p /opt/jumpserver/jumpserver
mkdir -p /opt/jumpserver/coco

chown -R jumpserver:docker /opt/jumpserver


echo "##################################################"
echo "                  依赖安装完成                     "
echo "#################################################"

# 托管给jumpserver用户执行安装
DIR=`pwd`
cp ${DIR}/jumpserver.sh /home/jumpserver/jumpserver.sh
chown jumpserver:jumpserver /home/jumpserver/jumpserver.sh
chmod +x /home/jumpserver/jumpserver.sh
sudo -u jumpserver /home/jumpserver/jumpserver.sh

{ # try
   docker rm -f `docker ps -a |grep busybox |cut -d ' ' -f 1` && pipework br0 jumpserver dhcp
} || { # catch
    pipework br0 jumpserver dhcp
}



