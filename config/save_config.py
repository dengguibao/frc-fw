import configparser

from rest_framework.response import Response
from rest_framework.decorators import api_view
from config.models import ChainGroup, Rule, PolicyRoute
from pyroute2 import IPDB
from .models import SysSetting
from app.models import OpenVpnUsers
from django.conf import settings
from .sys_views import get_all_record_form_ipset
from common.functions import get_ifindex_pair, ifindex2ifname, get_file_content, ip2MaskPrefix
import os


def get_all_iptables_rules():
    data = []
    for c in ChainGroup.objects.all():
        x, y = c.iptables_cmd
        data.append(x)
        data.append(y)
        for r in Rule.objects.filter(chain=c, enable=1).order_by('rule_seq'):
            data.append(repr(r))
        data.append('#')

    return data


def get_all_route_table():
    ipdb = IPDB()
    ifname_list = get_ifindex_pair()
    data = []
    for i in ipdb.routes:
        # print(i)
        dev = ifindex2ifname(ifname_list, i.oif)

        if i.family != 2 or 'tun' in dev:
            continue
        dst = '0.0.0.0' if i.dst == 'default' else i.dst
        cmd = f'ip route add {dst} dev {dev}'

        if i.gateway:
            cmd += f' gateway {i.gateway}'
        # if i.metric:
        #     cmd += f' metric {i.metric}'
        data.append(cmd)
    ipdb.release()
    return data


def get_all_interface_addr():
    ipdb = IPDB()
    data = []

    policy_route = ['!']

    for i in ipdb.by_name.keys():
        net_if = ipdb.interfaces[i]
        ifname = net_if.get('ifname')
        if 'tun' in ifname:
            continue
        operstate = 'UP' if net_if.get("operstate") == 'UNKNOWN' else net_if.get("operstate")
        data.append(
            f'ip link set {ifname} {operstate.lower()}'
        )
        if not net_if.ipaddr.ipv4:
            continue
        __ip_addr = net_if.ipaddr.ipv4[0].get('address')
        __prefix = net_if.ipaddr.ipv4[0].get('prefixlen')

        prefix = __prefix
        ipaddr = __ip_addr

        data.append(
            f'ip addr add {ipaddr}/{prefix} dev {ifname}'
        )
        policy_route.append(
            f'ip route add default via {ipaddr} dev {ifname} table {net_if.get("index")}'
        )
    ipdb.release()
    return data + policy_route


def get_sys_setting():
    data = []
    iptables_log_rule_tmp = (
        'iptables -t {table} -I {chain} ! -s 127.0.0.1/32 -j LOG --log-prefix "{log_prefix} " --log-level {log_level}'
    )
    config_map = (
        ('sys_forward', 'echo 1 > /proc/sys/net/ipv4/ip_forward'),
        ('iptables_snat_log', iptables_log_rule_tmp.format(
            table='nat',
            chain='POSTROUTING',
            log_prefix=settings.IPTABLES_PREFIX + 'SNAT',
            log_level=settings.IPTABLES_LOG_LEVEL
        )),
        ('iptables_dnat_log', iptables_log_rule_tmp.format(
            table='nat',
            chain='PREROUTING',
            log_prefix=settings.IPTABLES_PREFIX + 'DNAT',
            log_level=settings.IPTABLES_LOG_LEVEL
        )),
        ('iptables_foward_log', iptables_log_rule_tmp.format(
            table='filter',
            chain='FORWARD',
            log_prefix=settings.IPTABLES_PREFIX + 'FORWARD',
            log_level=settings.IPTABLES_LOG_LEVEL
        )),
    )

    for i in SysSetting.objects.all():
        for k, v in config_map:
            if k == i.item and i.value:
                data.append(v)
                break

    return data


def get_all_policy_route_rule():
    data = []
    all_obj = PolicyRoute.objects.all()
    for i in all_obj:
        data.append(i.iprule_cmd)

    if data:
        data.append('!')

    for i in all_obj:
        data.append(i.iptables_cmd)

    return data


def build_ipset_command():
    data = []
    for i in ('blacklist', 'whitelist'):
        for n in get_all_record_form_ipset(i):
            timeout_str = ''
            if n['timeout']:
                timeout_str = f' timeout {n["timeout"]}'
            data.append(f'ipset add {i} {n["ip"]}{timeout_str}')
    return data


def get_all_config():
    data = []
    m = (
        # get_forward_status,
        build_ipset_command,
        get_all_interface_addr,
        get_all_route_table,
        get_all_policy_route_rule,
        # get_all_chaingroup,
        get_all_iptables_rules,
        get_sys_setting,
        get_openvpn_config,
    )

    for backup_method in m:

        result = backup_method()

        if not result:
            continue

        if isinstance(result, str):
            data += [result, '!']

        data += (result + ['!'])

    opened_ports = '80,443,8000'

    try:
        rs = SysSetting.objects.get(item='sys_ping_func')
    except SysSetting.DoesNotExist:
        rs = None

    default_config = [
        '# -- ipset whitelist and blacklist config --',
        'ipset create blacklist hash:net maxelem 1000000 timeout 0',
        'ipset create whitelist hash:net maxelem 1000000 timeout 0',

        '# -- filter relate CHAIN policy --',
        'iptables -t filter -P FORWARD DROP',
        'iptables -t filter -P OUTPUT DROP',
        'iptables -t filter -P INPUT DROP',

        # '# -- system default opened port --',
        # 'iptables -N __SYS_OPENED_PORT__',
        # 'iptables -A __SYS_OPENED_PORT__ -p tcp -m multiport --dports %s -j ACCEPT' % opened_ports,
        # 'iptables -A __SYS_OPENED_PORT__ -p tcp -m multiport --sports %s -j ACCEPT' % opened_ports,

        '# -- system default rule --',
        'iptables -N __SYS_DEFAULT_RULE__',
        'iptables -N __SYS_OPENVPN_RULE__',

        'iptables -A __SYS_DEFAULT_RULE__ -i lo -p all -j ACCEPT',
        'iptables -A __SYS_DEFAULT_RULE__ -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT',
        'iptables -A __SYS_DEFAULT_RULE__ -m set --match-set whitelist src -j ACCEPT',
        'iptables -A __SYS_DEFAULT_RULE__ -m set --match-set blacklist src -j DROP',

        # '# DROP spoofing packets',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 10.0.0.0/8 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 169.254.0.0/16 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 172.16.0.0/12 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 127.0.0.0/8 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 192.168.0.0/24 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 224.0.0.0/4 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -d 224.0.0.0/4 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 240.0.0.0/5 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -d 240.0.0.0/5 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -s 0.0.0.0/8 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -d 0.0.0.0/8 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -d 239.255.255.0/24 -j DROP',
        # 'iptables -A __SYS_DEFAULT_RULE__ -d 255.255.255.255 -j DROP',

        '# for SMURF attack protection',
        'iptables -A __SYS_DEFAULT_RULE__ -p icmp -m icmp --icmp-type address-mask-request -j DROP',
        'iptables -A __SYS_DEFAULT_RULE__ -p icmp -m icmp --icmp-type timestamp-request -j DROP',
        'iptables -A __SYS_DEFAULT_RULE__ -p icmp -m icmp --icmp-type echo-reply  -m limit --limit 1/second -j ACCEPT',

        '# Droping all invalid packets',
        'iptables -A __SYS_DEFAULT_RULE__ -m state --state INVALID -j DROP',

        '# flooding of RST packets, smurf attack Rejection',
        'iptables -A __SYS_DEFAULT_RULE__ -p tcp -m tcp --tcp-flags RST RST -m limit --limit 2/second --limit-burst 2 -j ACCEPT',

        '# Protecting portscans, Attacking IP will be locked for 24 hours (3600 x 24 = 86400 Seconds)',
        'iptables -A __SYS_DEFAULT_RULE__ -m recent --name portscan --rcheck --seconds 86400 -j DROP',

        '# Remove attacking IP after 24 hours',
        'iptables -A __SYS_DEFAULT_RULE__ -m recent --name portscan --remove',

        # '# These rules add scanners to the portscan list.',
        # 'iptables -A __SYS_DEFAULT_RULE__ -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP',

        '# Allow ping means ICMP port is open (If you do not want ping replace ACCEPT with REJECT)',
        'iptables -A __SYS_DEFAULT_RULE__ -p icmp -m icmp --icmp-type 8 -j %s' % ('ACCEPT' if rs and rs.value else 'REJECT'),

        '# -- apply blacklist and whitelist --',
        # 'iptables -A INPUT -p all -i lo -j ACCEPT',
        'iptables -A INPUT -p tcp -m multiport --dports %s -j ACCEPT' % opened_ports,
        'iptables -A INPUT -j __SYS_DEFAULT_RULE__',
        'iptables -A INPUT -j __SYS_OPENVPN_RULE__',

        'iptables -A OUTPUT -p all -o lo -j ACCEPT',
        'iptables -A OUTPUT -p tcp -m multiport --sports %s -j ACCEPT' % opened_ports,
        'iptables -A OUTPUT -p icmp -j ACCEPT',

        'iptables -t filter -A FORWARD -j __SYS_DEFAULT_RULE__',
        'iptables -t filter -A FORWARD -j __SYS_OPENVPN_RULE__',

        '# -- disable source address validation --',
        'echo 2 > /proc/sys/net/ipv4/conf/all/rp_filter',
        '!',
        # iptables connection track
        # 'echo 1 > /proc/sys/net/netfilter/nf_conntrack_acct ',
    ]

    try:
        rs = SysSetting.objects.get(item='set_ssh_rule_func')
        if rs.value == 1:
            default_config.append('iptables -I INPUT -p tcp --dport 22 -j ACCEPT')
            default_config.append('iptables -I OUTPUT -p tcp --sport 22 -j ACCEPT')
        else:
            default_config.append('iptables -I INPUT -p tcp --dport 22 -j REJECT')
            default_config.append('iptables -I OUTPUT -p tcp --sport 22 -j REJECT')
    except SysSetting.DoesNotExist:
        pass

    default_config.append('!')

    return default_config + data


def write_config_to_file():
    try:
        result = get_all_config()
        fp = open('./running_config.sh', 'w')
        for i in result:
            if i:
                fp.write(i + os.linesep)
        fp.close()
        return True
    except OSError:
        return False


def get_openvpn_config():
    data = []
    for i in OpenVpnUsers.objects.all():
        for n in i.user_route.splitlines():
            ip = n.split()
            data.append(
                f'iptables -A __SYS_OPENVPN_RULE__ -s {i.user_ip} -d {ip[0]}/{ip2MaskPrefix(ip[1])} -m comment --comment "{i.username} incoming"  -j ACCEPT'
            )
            data.append(
                f'iptables -A __SYS_OPENVPN_RULE__ -s {ip[0]}/{ip2MaskPrefix(ip[1])} -d {i.user_ip} -m comment --comment "{i.username} back" -j ACCEPT'
            )
    cp = configparser.ConfigParser()
    cp.read(settings.APP_SETTING_FILE)
    if os.path.exists(settings.OPENVPN_PID_FILE):
        # config_file_list = [
        #     '/etc/openvpn/ca.crt',
        #     '/etc/openvpn/ta.key',
        #     '/etc/openvpn/openvpn-server.crt',
        #     '/etc/openvpn/openvpn-server.key',
        #     '/etc/openvpn/server.conf',
        #     '/etc/openvpn/dh2048.pem',
        # ]
        # for i in config_file_list:
        #     data.append('cat > %s << EOF' % i)
        #     c = get_file_content(i)
        #     data += c
        #     data.append('EOF')
        # openvpn_gateway = cp.get('openvpn', 'server').split()
        # openvpn_gw = f'{openvpn_gateway[0]}/{ip2MaskPrefix(openvpn_gateway[1])}'
        # data.append('iptables -A __SYS_OPENVPN_RULE__ -src %s -j ACCEPT' % openvpn_gw)
        # data.append('iptables -A __SYS_OPENVPN_RULE__ -dst %s -j ACCEPT' % openvpn_gw)
        data.append('iptables -I INPUT -p udp --dport %s -j ACCEPT' % cp.get('openvpn', 'listen_port'))
        data.append('iptables -I OUTPUT -p udp --sport %s -j ACCEPT' % cp.get('openvpn', 'listen_port'))
        data.append('systemctl start openvpn@server')
    return data


@api_view(['GET'])
def get_running_config_endpoint(request):
    result = get_all_config()

    return Response({
        'code': 0,
        'msg': 'success',
        'data': result
    })


@api_view(['GET'])
def write_config_endpoint(request):
    write_config_to_file()
    return Response({
        'code': 0,
        'msg': 'success'
    })
