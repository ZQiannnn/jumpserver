#!/usr/bin/env bash
set -e
#准备data文件夹
cd /opt/jumpserver
docker pull zqiannnn/jumpserver-ansible:0.5.0

# docker-compose 文件
rm -rf /opt/jumpserver/postgresql-redis.yml
cat >> /opt/jumpserver/postgresql-redis.yml << EOF
version: '2'
services:
  redis:
    container_name: jumpserver_redis
    image: sameersbn/redis:latest
    restart: always
    volumes:
      - /opt/jumpserver/redis:/var/lib/redis
    environment:
      - REDIS_PASSWORD=jumpserver
  postgresql:
    image: postgres:10.3-alpine
    restart: always
    container_name: jumpserver_postgresql
    environment:
      - POSTGRES_PASSWORD=jumpserver
      - POSTGRES_USER=jumpserver
      - POSTGRES_DB=jumpserver
    volumes:
       - /opt/jumpserver/postgresql:/var/lib/postgresql/data
    command: "postgres -c 'shared_buffers=256MB' -c 'max_connections=200'"
    ports:
      - 5432:5432
EOF

rm -rf /opt/jumpserver/jumpserver.yml
cat >> /opt/jumpserver/jumpserver.yml << EOF
version: '2'
services:
  jumpserver:
    image: zqiannnn/jumpserver-ansible:0.5.0
    container_name: jumpserver
    restart: always
    environment:
      - DB_ENGINE=postgresql
      - DB_HOST=postgresql
      - DB_PORT=5432
      - DB_USER=jumpserver
      - DB_PASSWORD=jumpserver
      - DB_NAME=jumpserver
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=jumpserver
    volumes:
      - /opt/jumpserver/coco:/opt/coco/keys
      - /opt/jumpserver/jumpserver:/opt/jumpserver/data
      - /opt/jumpserver/logs:/opt/jumpserver/logs
    ports:
      - 2222:2222
      - 80:80
    external_links:
      - postgresql
      - redis
EOF

#启动MySQL Redis

docker-compose -f postgresql-redis.yml rm -s -f



docker-compose -f postgresql-redis.yml up -d

#休眠1min 等待MYSQL启动
echo "等待依赖启动20s"
sleep 20s

#启动JumpServer

docker-compose -f jumpserver.yml rm -s -f

echo "开始安装JumpServer"
if docker-compose -f jumpserver.yml up -d >/dev/null 2>&1; then
    sleep 5s
    echo "从dhcp获取局域网ip"
    echo "#######################################################################"
    echo "                              安装完成                                 "
    echo "                       请在浏览器中打开Jumpserver                         "
    echo "                   若应用异常可用此脚本重启，数据不会丢失                   "
    echo "#######################################################################"

else
    echo "请检查端口占用或尝试重启docker安装: systemctl restart docker"
fi
