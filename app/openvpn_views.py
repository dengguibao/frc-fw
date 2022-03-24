import configparser
import ipaddress

import iptc
import os
import shutil
from django.conf import settings
from django.http.response import Http404, HttpResponse
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import OpenVpnUsers
from .serialize import OpenVpnUsersSerializer

from common.verify import (
    filter_user_data, verify_ip_subnet, verify_netmask,
    verify_port, verify_ip, verify_in_array, verify_username, verify_max_length,
    verify_ip_addr, verify_mail
)
from common.functions import prefix2NetMask, ip2MaskPrefix, get_all_ip_list
from common.exec_command import send_command
OPENVPN_SERVER_CONF = """
;local 0.0.0.0  
# 指定监听的本机IP(因为有些计算机具备多个IP地址)，该命令是可选的，默认监听所有IP地址。
port %(listen_port)s      
# 服务端端口号
proto udp
;dev tap
dev tun         
# 路由模式，注意windows下必须使用dev tap
ca ca.crt
#ca证书存放位置
cert openvpn-server.crt 
# 服务器证书存放位置
key openvpn-server.key
# 服务器密钥存放位置
dh dh1024.pem
# openssl dhparam -out dh2048.pem 2048
# dh.pem存放位置
tls-auth ta.key 0
# ta.key存放位置
server %(server)s
crl-verify /etc/openvpn/easy-rsa/keys/crl.pem
# 虚拟局域网网段设置
ifconfig-pool-persist ipp.txt
# push "route 0.0.0.0 0.0.0.0"
# 全网走openvpn
# push "redirect-gateway def1 bypass-dhcp" 
# push "dhcp-option DNS 223.5.5.5"
# 指定客户端使用的主DNS
push "dhcp-option DNS %(dns)s"
# 指定客户端使用的备DNS
client-to-client
# 开启客户端互访
client-config-dir ccd
# 每个独立的客户端配置目录
# duplicate-cn
# 如果需要支持一个证书多个客户端登录使用需要打开该配置，建议不启用，为每个不同的用户创建不同的证书
keepalive 5 30
# 判断是否离线，每隔5秒Ping一次30秒没有收到消息，则认为离线
;cipher AES-128-CBC
# 加密算法，如果开启，客户端配置文件也需要配置，2.4版本在TLS模式下，将自动协商为AES-256-GCM模式
comp-lzo
# 压缩级别，如果服务端开启了，客户端与需要同时开启
max-clients 100
# 最大客户端并发连接数量
user nobody
group nogroup
persist-key
persist-tun
log /var/log/openvpn.log
status /tmp/openvpn-status.log
# 定期把openvpn的一些状态信息写到文件中
verb 3
# 0 is silent, except for fatal errors
# 4 is reasonable for general usage
# 5 and 6 can help to debug connection problems
# 9 is extremely verbose
# 日志级别
mute 20
explicit-exit-notify 1
# 当服务端重启后通知客户端自动重连
topology subnet
"""

INIT_CERT_SHELL = """
#!/bin/bash
set -e
OPENVPN_CONFIG_DIR=/etc/openvpn
EASY_RSA_DIR=$OPENVPN_CONFIG_DIR/easy-rsa
PKI_DIR=$EASY_RSA_DIR/keys

dpkg -L openvpn
[[ $? -ne 0  ]] && apt install -y openvpn=2.4.4-2ubuntu1.6

dpkg -L easy-rsa
[[ $? -ne 0 ]] && apt install -y easy-rsa=2.2.2-2

rm -rf $OPENVPN_CONFIG_DIR/{ca.crt,openvpn-server.*,ipp.txt,ta.key,/dh*}
rm -rf $EASY_RSA_DIR
mkdir -p $PKI_DIR
mkdir -p $OPENVPN_CONFIG_DIR/ccd
cp -f /usr/share/easy-rsa/* $EASY_RSA_DIR
cd $EASY_RSA_DIR
mv openssl-1.0.0.cnf openssl.cnf
cat > vars <<EOF
export EASY_RSA="$EASY_RSA_DIR"
export OPENSSL="openssl"
export PKCS11TOOL="pkcs11-tool"
export GREP="grep"
export KEY_CONFIG=`$EASY_RSA_DIR/whichopensslcnf $EASY_RSA_DIR`
export KEY_DIR="$PKI_DIR"
echo NOTE: If you run ./clean-all, I will be doing a rm -rf on $KEY_DIR
export PKCS11_MODULE_PATH="dummy"
export PKCS11_PIN="dummy"
export KEY_SIZE=2048
export CA_EXPIRE=3650
export KEY_EXPIRE=3650

export KEY_COUNTRY="%(country)s"
export KEY_PROVINCE="%(province)s"
export KEY_CITY="%(city)s"
export KEY_ORG="%(org)s"
export KEY_EMAIL="%(email)s"
export KEY_OU="%(org_unit)s"
export KEY_NAME="EasyRSA"
EOF

source ./vars
./clean-all 
# printf '\\n\\n\\n\\n\\n\\n\\n\\n' | ./build-ca
./build-ca --batch
./build-key-server --batch openvpn-server
touch ./keys/dh1024.pem
openssl dhparam -out ./keys/dh1024.pem 1024
# generate crl.pem file
export KEY_CN=""
export KEY_OU=""
export KEY_NAME=""
export KEY_ALTNAMES=""
openssl ca -gencrl -out $PKI_DIR/crl.pem -config $EASY_RSA_DIR/openssl.cnf
chmod 755 $PKI_DIR
chmod o+r $PKI_DIR/crl.pem
# copy essential cert to /etc/openvpn
cd $PKI_DIR
cp dh1024.pem openvpn-server.* ca.crt $OPENVPN_CONFIG_DIR
# gen TLS-AUTH key
openvpn --genkey --secret $OPENVPN_CONFIG_DIR/ta.key
"""


@api_view(('GET',))
def get_openvpn_status(request):
    openvpn_pid_file = settings.OPENVPN_PID_FILE
    status = 'stop'
    if os.path.exists(openvpn_pid_file):
        status = 'running'

    openvpn_config_result = {'status': status}

    app_setting_file = settings.APP_SETTING_FILE
    if os.path.exists(app_setting_file):
        cp = configparser.ConfigParser(allow_no_value=True)
        cp.read(app_setting_file)

        if cp.has_section('openvpn'):
            openvpn_config_result['listen_port'] = int(cp.get('openvpn', 'listen_port'))
            openvpn_config_result['listen_ip'] = cp.get('openvpn', 'listen_ip')
            server = cp.get('openvpn', 'server').split()
            openvpn_config_result['server'] = server[0] + '/' + str(ip2MaskPrefix(server[1]))
            openvpn_config_result['dns'] = cp.get('openvpn', 'dns')

    return Response({
        'msg': 'success',
        'data': openvpn_config_result
    })


@api_view(('POST',))
def generate_cert(request):

    _fields = (
        ('*country', str, (verify_max_length, 4)),
        ('*province', str, (verify_max_length, 4)),
        ('*city', str, (verify_max_length, 10)),
        ('*org', str, (verify_max_length, 20)),
        ('*email', str, verify_mail),
        ('*org_unit', str, (verify_max_length, 20)),
    )
    data = filter_user_data(request.data, _fields)
    with open('./app/generate_openvpn_cert.sh', 'w+') as fp:
        fp.write(INIT_CERT_SHELL % data)

    if send_command('bash', './app/generate_openvpn_cert.sh', timeout=20):
        # 生成证书将删除所有的用户，而清空所有对应的转发条目
        OpenVpnUsers.objects.all().delete()
        iptc.easy.flush_chain('filter', '__SYS_OPENVPN_RULE__')
        shutil.rmtree('/etc/openvpn/ccd')
        os.mkdir('/etc/openvpn/ccd')
        return Response({'msg': 'success'})

    raise ParseError('command execute failed!')


@api_view(('POST',))
def start_or_stop_openvpn_server(request):
    validate_ip_list = get_all_ip_list()
    _fields = (
        ('*status', str, (verify_in_array, ('stop', 'start'))),
        ('*listen_port', int, verify_port),
        ('*listen_ip', str, (verify_in_array, tuple(validate_ip_list))),
        ('*server', str, verify_ip_subnet),
        ('*dns', str, verify_ip),
    )
    data = filter_user_data(request.data, _fields)
    ip_prefix = data['server'].split('/')
    server_addr = ip_prefix[0]
    server_mask = prefix2NetMask(int(ip_prefix[1]))

    openvpn_server_config_str = OPENVPN_SERVER_CONF % {
        'server': server_addr + ' ' + server_mask,
        'dns': data['dns'],
        'listen_port': data['listen_port']
    }

    config_backup_str = None
    if data['status'] == 'start':
        try:
            fp = open('/etc/openvpn/server.conf', 'w+')
            config_backup_str = fp.read()
            fp.write(openvpn_server_config_str)
            fp.close()
        except PermissionError:
            raise ParseError('/etc/openvpn/server.conf permission denied!')

    in_rule = {
        'protocol': 'udp',
        'udp': {
            'dport': str(data['listen_port'])
        },
        'target': "ACCEPT"
    }

    out_rule = {
        'protocol': 'udp',
        'udp': {
            'sport': str(data['listen_port'])
        },
        'target': "ACCEPT"
    }

    if data['status'] == 'start':
        rs = send_command('bash', './app/check_openvpn_env.sh')
        if not rs:
            raise ParseError('openvpn environment check failed!')

    # 执行启动或者停止服务命令
    if send_command('systemctl', data['status'], 'openvpn@server'):
        # 启动服务成功，将最新的配置更新到本平台的app配置文件中
        if data['status'] == 'start':
            # iptables添加openvpn的监听端口以及放行客户端网段
            iptc.easy.insert_rule('filter', 'INPUT', in_rule)
            iptc.easy.insert_rule('filter', 'OUTPUT', out_rule)
            # 更新配置文件
            cp = configparser.ConfigParser()
            cp.read(settings.APP_SETTING_FILE)
            if not cp.has_section('openvpn'):
                cp.add_section('openvpn')
            cp.set('openvpn', 'listen_port', str(data['listen_port']))
            cp.set('openvpn', 'listen_ip', data['listen_ip'])
            cp.set('openvpn', 'server', server_addr + ' ' + server_mask)
            cp.set('openvpn', 'dns', data['dns'])
            cp.write(open(settings.APP_SETTING_FILE, 'w'))

        if data['status'] == 'stop':
            iptc.easy.delete_rule('filter', 'INPUT', in_rule)
            iptc.easy.delete_rule('filter', 'OUTPUT', out_rule)
            # iptc.easy.flush_chain('filter', '__SYS_OPENVPN_RULE__')

        return Response({
            'msg': data['status'] + ' openvpn server success.'
        })

    # 如果启动服务令命执行失败，回滚配置
    if data['status'] == 'start' and config_backup_str:
        with open('/etc/openvpn/server.conf', 'w') as fp:
            fp.write(config_backup_str)
        iptc.easy.delete_rule('filter', 'INPUT', in_rule)
        iptc.easy.delete_rule('filter', 'OUTPUT', out_rule)

    raise ParseError(data['status'] + ' openvpn server failed!')


@api_view(('GET', 'POST', 'DELETE', 'PUT'))
def openvpn_op_endpoint(request):
    # 查询所有openvpn用户
    if request.method == 'GET':
        qs = OpenVpnUsers.objects.all()
        page = PageNumberPagination()
        page.page_size = settings.PAGE_SIZE
        page.page_query_param = 'page'
        page.max_page_size = 20
        page.number = int(request.GET.get('page', 1))
        # page.max_page_size = 20
        ret = page.paginate_queryset(qs, request)
        ser = OpenVpnUsersSerializer(ret, many=True)
        return Response({
            'msg': 'success',
            'data': ser.data,
            'page_info': {
                'total': len(qs),
                'pageSize': page.page_size,
                'current': page.page.number
            }
        })

    # 新增openvpn用户
    if request.method == 'POST':
        _fields = (
            ('*username', str, verify_username),
            ('*name', str, (verify_max_length, 6)),
            ('*user_ip', str, verify_ip_addr),
            ('*user_route', str, (verify_max_length, 500))
        )
        data = filter_user_data(request.data, _fields)
        cp = configparser.ConfigParser()
        cp.read(settings.APP_SETTING_FILE)
        server_subnet = cp.get('openvpn', 'server').split()
        if ipaddress.ip_address(data['user_ip']) not in ipaddress.ip_network(
                f'{server_subnet[0]}/{ip2MaskPrefix(server_subnet[1])}').hosts():
            raise ParseError('illegal client ip')

        for i in data['user_route'].splitlines():
            x = i.split()
            if len(x) != 2:
                raise ParseError('user route format error!')
            if not ipaddress.ip_address(x[0]):
                raise ParseError('illegal route network')
            if not verify_netmask(x[1]) or not ip2MaskPrefix(x[1]):
                raise ParseError('illegal route mask')
            try:
                ipaddress.ip_network(f'{x[0]}/{ip2MaskPrefix(x[1])}')
            except:
                raise ParseError('illegal sub network')
        try:
            OpenVpnUsers.objects.create(**data)
        except Exception as e:
            raise ParseError('create user failed, ' + e.args[0])

        return Response({
            'msg': 'create user success'
        })

    # 修改openVPN用户ip route
    if request.method == 'PUT':
        _fields = (
            ('*uid', int, None),
            ('*user_ip', str, verify_ip_addr),
            ('*user_route', str, (verify_max_length, 500))
        )
        data = filter_user_data(request.data, _fields)
        cp = configparser.ConfigParser()
        cp.read(settings.APP_SETTING_FILE)
        server_subnet = cp.get('openvpn', 'server').split()
        if ipaddress.ip_address(data['user_ip']) not in ipaddress.ip_network(
                f'{server_subnet[0]}/{ip2MaskPrefix(server_subnet[1])}').hosts():
            raise ParseError('illegal client ip')

        for i in data['user_route'].splitlines():
            x = i.split()
            if len(x) != 2:
                raise ParseError('user route format error!')
            if not ipaddress.ip_address(x[0]):
                raise ParseError('illegal route network')
            if not verify_netmask(x[1]) or not ip2MaskPrefix(x[1]):
                raise ParseError('illegal route mask')
            try:
                ipaddress.ip_network(f'{x[0]}/{ip2MaskPrefix(x[1])}')
            except:
                raise ParseError('illegal sub network')

        try:
            res = OpenVpnUsers.objects.get(pk=data['uid'])
        except OpenVpnUsers.DoesNotExist:
            raise NotFound
        # 删除除的iptables规则
        for ou in res.user_route.splitlines():
            route_ip = ou.split()
            iptc.easy.delete_rule('filter', '__SYS_OPENVPN_RULE__', {
                'src': res.user_ip,
                'dst': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                'target': 'ACCEPT',
                'comment': f'{res.username} incoming'
            })
            iptc.easy.delete_rule('filter', '__SYS_OPENVPN_RULE__', {
                'src': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                'dst': res.user_ip,
                'target': 'ACCEPT',
                'comment': f'{res.username} back'
            })
        # 应用新的规则
        ccd_list = [f"ifconfig-push {data['user_ip']} {server_subnet[1]}"]
        for i in data['user_route'].splitlines():
            ccd_list.append(f'push "route {i.strip()}"')
            route_ip = i.split()
            iptc.easy.insert_rule('filter', '__SYS_OPENVPN_RULE__', {
                'src': data['user_ip'],
                'dst': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                'target': 'ACCEPT',
                'comment': f'{res.username} incoming'
            })
            iptc.easy.insert_rule('filter', '__SYS_OPENVPN_RULE__', {
                'src': f'{route_ip[0]}/{ip2MaskPrefix(route_ip[1])}',
                'dst': data['user_ip'],
                'target': 'ACCEPT',
                'comment': f'{res.username} back'
            })
        # 写ccd文件
        with open(f'/etc/openvpn/ccd/{res.username}', 'w+') as fp:
            print(os.linesep.join(ccd_list))
            fp.write(os.linesep.join(ccd_list))

        res.user_ip = data['user_ip']
        res.user_route = data['user_route']
        res.save()

        return Response({
            'msg': 'success'
        })

    # 删除用户
    if request.method == 'DELETE':
        user_id = request.GET.get('uid', None)
        if user_id:
            try:
                OpenVpnUsers.objects.get(pk=user_id).delete()
            except OpenVpnUsers.DoesNotExist:
                raise NotFound()
            return Response({'msg': 'delete openvpn user success'})

        raise ParseError('illegal user id!')


def get_client_ovpn_file(request, uid: int):
    try:
        res = OpenVpnUsers.objects.get(pk=uid)
    except OpenVpnUsers.DoesNotExist:
        return Http404()

    ovpn_str = res.build_ovpn_file()
    return HttpResponse(
        ovpn_str,
        headers={
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename="client.ovpn"',
        }
    )
