import os
import subprocess
from pyroute2 import NDB, IPDB


def execShell(cmd):
    """
    send command to shell and execute
    :param cmd: shell command
    :return:
    """
    ret = subprocess.run(
        cmd,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
        encoding='utf-8'
    )

    if ret.returncode == 0:
        status = 'success'
    else:
        status = 'failed'
    return {
        'code': ret.returncode,
        'msg': status,
        'return': ret.stdout if ret.stdout else ret.stderr
    }


def timeRange2Seconds(time_range_str: str) -> int:
    """
    将time_range转换成seconds
    :param time_range_str: time_range
    :return: seconds
    """
    suffix = time_range_str[-1]
    num = time_range_str[:-1]
    if suffix not in ['m', 'h', 's']:
        return False
    try:
        n = int(num)
        if suffix == 'm':
            return n * 60
        if suffix == 'h':
            return n * 60 * 60
        if suffix == 's':
            return n
    except ValueError:
        return False


def hexStr2Ip(hex_str: str):
    """
    hex string convert to ip address
    :param hex_str: hex string
    :return: ip address string
    """
    if not isinstance(hex_str, str) or len(hex_str) != 8:
        return

    field1 = int('0x%s' % hex_str[0:2], 16)
    field2 = int('0x%s' % hex_str[2:4], 16)
    field3 = int('0x%s' % hex_str[4:6], 16)
    field4 = int('0x%s' % hex_str[6:8], 16)

    field_list = (
        str(field4),
        str(field3),
        str(field2),
        str(field1)
    )

    return '.'.join(field_list)


def ip2MaskPrefix(ip_addr: str) -> int:
    """
    ip address convert to netmask prefix
    :param ip_addr: ip address
    :return:
    """
    ip_field = ip_addr.split('.')
    buff = []
    for field in ip_field:
        ip_num = int(field)
        if ip_num > 255 or ip_num < 0:
            return -1
        buff.append(bin(ip_num))

    bin_netmask_str = ''.join(buff).replace('0', '').replace('b', '')
    return len(bin_netmask_str)


def prefix2NetMask(prefix: int) -> str:
    """
    netmask prefix convert to ip
    :param prefix: netmask prefix
    :return:  ip address
    """
    if prefix > 32:
        return ''
    zero = 32 - prefix
    bin_ip = '1' * prefix + '0' * zero
    field1 = int('0b%s' % bin_ip[0:8], 2)
    field2 = int('0b%s' % bin_ip[8:16], 2)
    field3 = int('0b%s' % bin_ip[16:24], 2)
    field4 = int('0b%s' % bin_ip[24:32], 2)
    field_list = (
        str(field1),
        str(field2),
        str(field3),
        str(field4),
    )
    return '.'.join(field_list)


# def get_chain_groups(group_type: str) -> list:
#     data = []
#     g_list = {
#         'snat': {
#             'table_name': 'nat',
#             'chain_name': 'POSTROUTING',
#         },
#         'dnat': {
#             'table_name': 'nat',
#             'chain_name': 'PREROUTING',
#         },
#         'filter': {
#             'table_name': 'filter',
#             'chain_name': 'FORWARD',
#         }
#     }
#
#     assert group_type in g_list, 'illegal group type'
#
#     d = iptc.easy.dump_chain(g_list[group_type]['table_name'], g_list[group_type]['chain_name'], ipv6=False)
#     for i in d:
#         if 'target' in i and 'goto' in i['target']:
#             data.append(i['target']['goto'])
#     return data


def get_client_ip(request):
    """
    获取客户端ip地址
    """
    try:
        remote_ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
    except KeyError:
        remote_ip = request.META.get('REMOTE_ADDR', None)
    return remote_ip


def get_ifindex_pair() -> list:
    # return NDB().interfaces.dump().select('index', 'ifname').format('json')
    ipdb = IPDB()
    iflist = ipdb.by_name
    data = []
    for i in iflist:
        data.append(
            (iflist[i]['index'], i)
        )
    return data


def ifindex2ifname(ifpair: list, index: int) -> str:
    for ifindex, ifname in ifpair:
        if ifindex == index:
            return ifname
        else:
            continue
    return ''


def get_file_content(filename: str) -> list:
    c = []
    if os.path.exists(filename):
        fp = open(filename, 'r')
        c = fp.read().splitlines()
        fp.close()
    return c


def get_all_ip_list() -> list:
    ipdb = IPDB()
    data = []
    for i in ipdb.by_name.keys():
        if i in ('lo', 'tap', 'tun0', 'tun1', 'tun'):
            continue

        x = ipdb.interfaces[i]
        if 'ipaddr' in x and x['ipaddr']:
            ip_addr = x['ipaddr'][0]['local']
            data.append(ip_addr)
        continue

    ipdb.release()
    return data
