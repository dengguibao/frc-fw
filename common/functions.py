import subprocess


def execShell(cmd):
    """
    send command to shell and execute
    :param cmd: shell command
    :return:
    """
    ret = subprocess.run(
        cmd,
        shell=True,
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
    field1 = int('0b%s' % bin_ip[0:8])
    field2 = int('0b%s' % bin_ip[8:16])
    field3 = int('0b%s' % bin_ip[16:24])
    field4 = int('0b%s' % bin_ip[24:32])
    field_list = (
        str(field1),
        str(field2),
        str(field3),
        str(field4),
    )
    return '.'.join(field_list)


def verify_ip(ip: str) -> bool:
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


def verify_necessary_field(data: dict, field):
    if not isinstance(data, dict):
        return

    if isinstance(field, str):
        if field not in data:
            return False

    if isinstance(field, list):
        for i in field:
            if i not in data:
                return False

    for i in field:
        if not data[i]:
            del data['i']

    return data