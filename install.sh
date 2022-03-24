#! /bin/bash

# environment ubuntu server 18.04
HOME_DIR='/home/firewall/'

usage(){
  cat <<EOM
Format:
./install.sh <command> [parameter]

Command options:
  -h|--help|help         : print this help info
  install                : install firewall dependent software
  add-user               : add super user

Parameter options:

  add-user
    --username=user      : username, default is root
    --password=pwd       : password, default is random string
    --email=a@b.com      : (require) user email

EOM
}

write_to_rc_local(){
  cat > /etc/rc.local << EOF
#!/bin/bash
bash /home/firewall/running_config.sh
EOF
}

install(){
  # copy all systemd file to lib directory
  [ -f running_config.sh ] && rm -f running_config.sh
  cp *.service /lib/systemd/system/
  # remove old database file
  [ -f db.sqlite3 ] && rm -rf db.sqlite3 || echo ''
  # 创建静态资源的快捷方式
  if [ -d static ] ; then
    rm -rf ./static
  fi
  [ -d UI/static ] && ln -s UI/static ./static
  # change some code
  sed -i '351d' ./config/models.py
  # install system dependent software
  apt update
  apt install python3 python3-pip openvpn easy-rsa memcached conntrack ipset sqlite3 -y
  # set startup memcached
  systemctl start memcached && systemctl enable memcached
  # upgrade pip
  python3 -m pip install --upgrade pip
  # install pip lib
  # pip3 install django djangrestframework pymemcached pyroute2 python-iptables ipsetpy django-cors-headers
  pip3 install -r ./requirement.txt
  # build database
  python3 ./manage.py makemigrations
  python3 ./manage.py makemigrations app
  python3 ./manage.py migrate

  # 设定开机启动服务
  systemctl start firewall-web firewall-collector-sar && systemctl enable firewall-web firewall-collector-sar
  echo  'LOAD_DEFAULT_CONFIG()' >>./config/models.py

  # 创建黑白名单
  ipset create blacklist hash:net maxelem 1000000 timeout 0
  ipset create whitelist hash:net maxelem 1000000 timeout 0

  # 写入定时任务与开机加载配置
  echo '0 0 * * * curl http://127.0.0.1:8000/api/serverInfo/sarClear' > /var/spool/cron/crontabs/root
  if [ -f /etc/rc.local ]; then
    echo 'bash /home/firewall/running_config.sh' >> /etc/rc.local
  else
    write_to_rc_local
  fi
  [ -x /etc/rc.local ] || chmod 755 /etc/rc.local


  echo 'please wait 5 seconds, until django load success!'
  for n in `seq 1 5`
  do
    echo $n
    sleep 1
  done

  # 加载初始化规则
  if [[ -z `ss -tnl|grep 8000` ]]; then
    echo -e 'firewall start failed!, please use \e[1;31m systemctl status firewall-web\e[0m command check.'
    exit 1
  fi

  exec_rc=`curl -s http://127.0.0.1:8000/api/config/sys/saveRunningConfig`
  [[ $exec_rc =~ success ]] || (echo 'execute saveRunningConfig failed!';exit 1)

  if [ -f running_config.sh ]; then
    systemctl start rc-local
    systemctl enable rc-local
  fi
}

add_root_user(){
  if [ ! -f db.sqlite3 ]; then
    echo 'firewall not install'
    exit 1
  fi

  export DJANGO_SUPERUSER_PASSWORD=${PASSWORD}

  python3 ./manage.py createsuperuser --username=${USERNAME} --email=${EMAIL} --noinput
  echo 'success, user password is '${DJANGO_SUPERUSER_PASSWORD}
}

main(){

  if [ -d ${HOME_DIR} ]; then
    cd ${HOME_DIR}
  else
    echo 'not found firewall directory, please clone firewall source code to /home/firewall and then execute this script'
    exit 1
  fi

  if [ $# -eq 0 ]; then
    echo 'not found argument params, please add --help arg view help documents'
    exit 1
  fi

  for i in $@
  do
    [[ ${i} =~ ^-{2}username= ]] && USERNAME=${i##*=}
    [[ ${i} =~ ^-{2}password= ]] && PASSWORD=${i##*=}
    [[ ${i} =~ ^-{2}email= ]] && EMAIL=${i##*=}
  done

  while [ $# -gt 0 ]; do
    case "$1" in


      --help|help|-h)
        usage
        exit 0;;

      install)
        install
        exit 0;;

      add-user)
        [ -z ${USERNAME} ] && USERNAME='root'
        [ -z ${PASSWORD} ] && PASSWORD=`head /dev/urandom |cksum |md5sum |cut -c 1-9`
        [ -z ${EMAIL} ] && (echo 'create user failed, please set a email', exit 1)
        add_root_user
        exit 0;;

      *)
        echo 'incorrect command line parameter.'
        exit 1;;
      esac
    done
}

main $@
