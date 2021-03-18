from pyroute2 import IPDB
import re


def verify_interface_name(ifname: str) -> bool:
    """
    verify the ifname whether is invalid interface name
    """
    ipdb = IPDB()
    ifname_list = ipdb.by_name.keys()
    ipdb.release()
    return True if ifname in ifname_list else False


def verify_ip_range(ip_range: str) -> bool:
    """
    verify ip range format
    e.g.
    a.b.c.d-a.b.c.e
    """
    if '-' not in ip_range:
        return False

    ip = ip_range.split('-')
    if len(ip) != 2:
        return False

    ip1 = ip[0]
    ip2 = ip[1]
    if not verify_ip(ip1) or not verify_ip(ip2):
        return False

    x = ip1.split('.')
    y = ip2.split('.')

    if int(x[-1]) > int(y[-1]) or (x[0] != y[0]) or (x[1] != y[1]) or (x[2] != y[2]):
        return False

    return True


def verify_interface_state(state: str) -> bool:
    """
    verify interface state whether is up or down
    """
    return True if state.lower() in ('up', 'down') else False


def verify_ip(ip: str) -> bool:
    """
    verify ip address whether is a.b.c.d or a.b.c.d/x
    """
    if verify_ip_addr(ip) or verify_ip_subnet(ip):
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


def verify_ip_subnet(net: str) -> bool:
    """
    verify a.b.c.d/x format subnet
    """
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


def verify_prefix(prefix: int):
    """
    verify prefix whether is invalid prefix
    """
    return True if prefix >= 0 or prefix <= 32 else False


def verify_protocol(protocol: str) -> bool:
    """
    verify iptables rule protocol
    """
    if protocol in ('tcp', 'udp', 'icmp', 'gre', 'ah', 'esp', 'ospf', 'sctp'):
        return True
    return False


def verify_port(p):
    """
    verify port whether is invalid
    """
    try:
        if not isinstance(p, int):
            d = int(p)
    except Exception as e:
        return False

    if 0 < d or d > 65535:
        return str(p)
    return False


def verify_username(username: str) -> bool:
    """
    verify username whether contain special charset
    """
    special_char = ('/', ' ', '[', ']', '"', '\\', '\'', '$', '%', '^', '*', '(', ')', '!', '~', '`')
    for i in special_char:
        if i in username:
            return False
    return True


def verify_in_array(arg1: str, array: tuple) -> bool:
    """
    verify arg1 whether in array
    """
    return True if arg1 in array else False


def verify_is_equal(x, y):
    """
    verify two object whether equal
    """
    return True if x == y else False


def verify_field(data: dict, field: tuple):
    """
    verify received dict data
    field format is ('field_name', field_type, verify_func)
    when verify_func is function then call the function verify field content
    when verify_func is tuple then tuple first element is verify_func, the second element is arg
    when field_name start with '*' mean the filed is necessary
    """
    if not isinstance(data, dict):
        return

    buff = {}

    # prevent all field is not necessary
    pass_flag = False

    if isinstance(field, tuple):
        for field_name, field_type, verify_param in field:

            if field_name[0] == '*':
                field_name = field_name[1:]

                if field_name not in data or not data[field_name]:
                    return 'field %s is necessary and can not be empty' % field_name

            if field_name not in data:
                continue

            if not isinstance(data[field_name], field_type):
                return 'field %s type wrong!' % field_name

            if verify_param and isinstance(verify_param, tuple) and len(verify_param) > 1:
                verify_func = verify_param[0]
                verify_arg = verify_param[1]
                verify_result = verify_func(data[field_name], verify_arg)

            if verify_param and hasattr(verify_param, '__call__'):
                verify_result = verify_param(data[field_name])

            if verify_param and not verify_result:
                return 'field %s verify failed!' % field_name

            if field_name in data:
                pass_flag = True

    if pass_flag:
        for i, _, _ in field:
            k = i.strip()
            if k[0] == '*':
                k = k[1:]

            if k in data and data[k]:
                if isinstance(data[k], str) and len(data[k]) > 100:
                    data[k] = data[k].strip()[0:100]
                buff[k] = data[k].strip() if isinstance(data[k], str) else data[k]
        return buff
    return False


def verify_mail(mail: str) -> bool:
    """
    verify mail whether invalid
    """
    return True if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", mail) else False


def verify_true_false(i) -> bool:
    """
    verify object(i) is true or false
    """
    return True if i.lower() in ('1', 1, 'true', 'false', 0, '0') else False
