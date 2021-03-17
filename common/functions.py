import subprocess
from pyroute2 import IPDB


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
    except:
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


def ip2MaskPrefix(ip_addr: str):
    """
    ip address convert to netmask prefix
    :param ip_addr: ip address
    :return:
    """
    ip_field = ip_addr.split('.')
    buff = []
    for field in ip_field:
        ip_num = int(field)
        if ip_num > 255:
            return
        buff.append(bin(ip_num))

    bin_netmask_str = ''.join(buff).replace('0', '').replace('b', '')
    return len(bin_netmask_str)


def prefix2NetMask(prefix: int):
    """
    netmask prefix convert to ip
    :param prefix: netmask prefix
    :return:  ip address
    """
    if prefix > 32:
        return
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


def verify_interface_name(ifname: str) -> bool:
    ipdb = IPDB()
    ifname_list = ipdb.by_name.keys()
    ipdb.release()
    return True if ifname in ifname_list else False


def verify_ip_range(ip_range: str) -> bool:
    if '-' not in ip_range:
        return False

    ip = ip_range.split('-')
    if len(ip) != 2:
        return False

    ip1 = ip[0]
    ip2 = ip[1]
    if not verify_ip(ip1) or not verify_ip(ip2):
        return False

    if int(ip1.split('.')[-1]) > int(ip2.split('.')[-1]):
        return False

    return True


# def verify_table(table: str) -> bool:
#     if not verify_interface_name(table) and table != 'main':
#         return False
#     return True


def verify_interface_state(state: str) -> bool:
    return True if state.lower() in ('up', 'down') else False


def verify_ip(ip: str) -> bool:
    if verify_ip_addr(ip) or verify_prefix_mode_net(ip):
        return True
    return False


def verify_ip_addr(ip: str) -> bool:
    """
    verify ip whether is a invalid ip
    :param ip:
    :return:
    """
    if len(ip) > 15 or '.' not in ip or len(ip.split('.')) > 4:
        return False
    first = True
    for i in ip.split('.'):
        try:
            n = int(i)
        except:
            return False
        if n > 255:
            return False
        if first and n == 0:
            return False
        first = False
    return True


def verify_netmask(ip: str) -> bool:
    """
    verify ip whether is invalid netmask
    :param ip: ip address
    :return:
    """
    result = verify_ip(ip)
    if result:
        valid_dns_num = (128, 192, 224, 240, 248, 252, 254, 255)
        field_num = [int(i) for i in ip.split('.')]
        x = 1
        for i in field_num:
            if i > 0 and i not in valid_dns_num:
                return False
            if x < 4 and field_num[x] > i:
                return False
            x += 1
        return True
    else:
        return False


def verify_prefix_mode_net(net: str) -> bool:
    if '/' not in net or len(net.split('/')) > 2:
        return False
    ip_prefix = net.split('/')
    if not verify_ip(ip_prefix[0]):
        return False

    try:
        n = int(ip_prefix[1])
    except:
        return False

    if n > 32:
        return False

    return True


def simple_verify_field(data: dict, field: tuple):
    if not isinstance(data, dict):
        return

    buff = {}

    pass_flag = False

    if isinstance(field, tuple):
        for i in field:
            if i[0] == '*' and i[1:] not in data:
                return False

            if i[0] == '*' and i[1:] in data:
                pass_flag = True

            if i in data:
                pass_flag = True

    if pass_flag:
        for i in field:
            k = i.strip()
            if k[0] == '*':
                k = k[1:]

            if k in data and data[k]:
                buff[k] = data[k]

        return buff
    return False


def verify_prefix(prefix: int):
    return True if prefix >= 0 or prefix <= 32 else False


def verify_protocol(protocol: str) -> bool:
    if protocol in ('tcp', 'udp', 'icmp', 'gre', 'ah', 'esp', 'ospf', 'sctp'):
        return True
    return False


def verify_port(p):
    try:
        if not isinstance(p, int):
            d = int(p)
    except Exception as e:
        # print(e)
        return False

    if 0 < d or d > 65535:
        return str(p)
    return False


def verify_field(data: dict, field: tuple):
    if not isinstance(data, dict):
        return

    buff = {}

    pass_flag = False

    if isinstance(field, tuple):
        for field_name, field_type, verify_func in field:

            if field_name[0] == '*':
                field_name = field_name[1:]

                if field_name not in data or not data[field_name].strip():
                    return 'field %s is necessary and can not be empty' % field_name

            if field_name not in data:
                continue

            if not isinstance(data[field_name], field_type):
                return 'field %s type wrong!' % field_name

            if verify_func and not verify_func(data[field_name]):
                return 'field %s verify failed!' % field_name

            if field_name in data:
                pass_flag = True

    if pass_flag:
        for i, _, _ in field:
            k = i.strip()
            if k[0] == '*':
                k = k[1:]

            if k in data and data[k]:
                buff[k] = data[k].strip()

        return buff
    return False
